import json
import psycopg
from datetime import datetime, timedelta, timezone
from multiprocessing import Pool, cpu_count

# Database connection parameters
DB_HOST = "horizon.cz2imkksk7b4.us-west-1.rds.amazonaws.com"
DB_PORT = 5434
DB_NAME = "horizon"
DB_USER = "stellar"
DB_PASS = "new_stellar_pass"

# Connect to the PostgreSQL database
def get_db_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=300,
        sslmode="require"
    )

# Fetch swaps for all wallets in batches
def fetch_swaps_for_all_wallets(wallet_addresses, limit_per_wallet=200, batch_size=100):
    conn = get_db_connection()
    cursor = conn.cursor()
    swaps_by_wallet = {}

    start_time = datetime.now(timezone.utc) - timedelta(hours=36)
    total_wallets = len(wallet_addresses)

    # Process wallets in batches
    for batch_start in range(0, total_wallets, batch_size):
        batch_end = min(batch_start + batch_size, total_wallets)
        batch_wallets = wallet_addresses[batch_start:batch_end]
        print(f"Fetching swaps for wallets {batch_start + 1} to {batch_end}/{total_wallets}...")

        # Create placeholders for the IN clause
        placeholders = ",".join(["%s"] * len(batch_wallets))
        query = f"""
        SELECT
            ho.source_account,
            ho.type,
            ho.details->>'source_asset_type' as source_asset_type,
            ho.details->>'source_asset_code' as source_asset_code,
            ho.details->>'source_asset_issuer' as source_asset_issuer,
            ho.details->>'source_amount' as source_amount,
            ho.details->>'asset_type' as asset_type,
            ho.details->>'asset_code' as asset_code,
            ho.details->>'asset_issuer' as asset_issuer,
            ho.details->>'amount' as amount,
            ht.created_at
        FROM history_operations ho
        JOIN history_transactions ht ON ho.transaction_id = ht.id
        WHERE
            ho.type IN (2, 13, 24)
            AND ht.successful = true
            AND ho.source_account IN ({placeholders})
            AND ht.created_at >= %s
        ORDER BY ho.source_account, ht.created_at DESC;
        """
        # Execute with the batch of wallets and start_time
        cursor.execute(query, (*batch_wallets, start_time))
        results = cursor.fetchall()

        # Group results by wallet
        current_wallet = None
        wallet_swaps = []
        swap_count = 0
        for row in results:
            wallet = row[0]
            if wallet != current_wallet:
                if current_wallet:
                    swaps_by_wallet[current_wallet] = wallet_swaps[:limit_per_wallet]
                current_wallet = wallet
                wallet_swaps = []
                swap_count = 0
            if swap_count < limit_per_wallet:
                wallet_swaps.append({
                    "type": row[1],
                    "source_asset_type": row[2],
                    "source_asset_code": row[3] if row[2] != "native" else "XLM",
                    "source_asset_issuer": row[4],
                    "source_amount": float(row[5]) if row[5] else 0.0,
                    "asset_type": row[6],
                    "asset_code": row[7] if row[6] != "native" else "XLM",
                    "asset_issuer": row[8],
                    "amount": float(row[9]) if row[9] else 0.0,
                    "closed_at": row[10]
                })
                swap_count += 1
        # Add the last wallet's swaps
        if current_wallet:
            swaps_by_wallet[current_wallet] = wallet_swaps[:limit_per_wallet]

    cursor.close()
    conn.close()
    return swaps_by_wallet

# Function to estimate P&L for a single wallet (for parallel processing)
def estimate_pnl_for_wallet(wallet_data):
    wallet_address = wallet_data["source_account"]
    num_swaps = wallet_data["num_swaps"]
    total_volume_xlm = wallet_data["total_volume_xlm"]
    swaps = wallet_data["swaps"]

    if not swaps:
        return {
            "source_account": wallet_address,
            "num_swaps": num_swaps,
            "total_volume_xlm": total_volume_xlm,
            "pnl": {
                "total_pnl_xlm": 0.0,
                "num_round_trips": 0,
                "avg_pnl_per_round_trip": 0.0,
                "net_xlm_change": 0.0,
                "num_swaps_analyzed": 0,
                "asset_pairs": []
            }
        }

    # Sort swaps by timestamp (ascending)
    swaps.sort(key=lambda x: x["closed_at"])

    # Track XLM balance changes and asset pairs
    xlm_balance = 0.0
    fee_per_swap = 0.00001  # 100 stroops per operation
    num_swaps_analyzed = len(swaps)
    asset_pairs = set()

    # Track round-trips for P&L calculation
    round_trips = []
    pending_trades = {}  # {asset_key: [(amount, xlm_amount)]}

    for swap in swaps:
        # Record the asset pair
        if swap["source_asset_type"] == "native":
            pair = f"XLM/{swap['asset_code']}"
            xlm_balance -= swap["source_amount"]
            asset_key = f"{swap['asset_code']}_{swap['asset_issuer']}" if swap["asset_type"] != "native" else "XLM"
            if asset_key not in pending_trades:
                pending_trades[asset_key] = []
            pending_trades[asset_key].append((swap["amount"], swap["source_amount"]))
        else:
            pair = f"{swap['source_asset_code']}/XLM"
            xlm_balance += swap["amount"]
            asset_key = f"{swap['source_asset_code']}_{swap['source_asset_issuer']}" if swap["source_asset_type"] != "native" else "XLM"
            if asset_key in pending_trades and pending_trades[asset_key]:
                for i, (prev_amount, prev_xlm) in enumerate(pending_trades[asset_key]):
                    if abs(prev_amount - swap["source_amount"]) < 0.01:
                        slippage = 0.005  # 0.5% slippage per trade
                        pnl_xlm = (swap["amount"] - prev_xlm) * (1 - slippage) - (2 * fee_per_swap)
                        round_trips.append(pnl_xlm)
                        pending_trades[asset_key].pop(i)
                        break
        asset_pairs.add(pair)
        xlm_balance -= fee_per_swap

    total_pnl_xlm = sum(round_trips) if round_trips else 0.0
    num_round_trips = len(round_trips)
    avg_pnl = total_pnl_xlm / num_round_trips if num_round_trips > 0 else 0.0

    return {
        "source_account": wallet_address,
        "num_swaps": num_swaps,
        "total_volume_xlm": total_volume_xlm,
        "pnl": {
            "total_pnl_xlm": total_pnl_xlm,
            "num_round_trips": num_round_trips,
            "avg_pnl_per_round_trip": avg_pnl,
            "net_xlm_change": xlm_balance,
            "num_swaps_analyzed": num_swaps_analyzed,
            "asset_pairs": list(asset_pairs)
        }
    }

# Main script logic
if __name__ == "__main__":
    # Load the wallet rankings
    with open("wallet_rankings.json", "r") as f:
        wallet_rankings = json.load(f)

    # Validate addresses in wallet_rankings
    wallet_rankings = [
        wallet for wallet in wallet_rankings
        if len(wallet["source_account"]) == 56 and wallet["source_account"].startswith('G')
    ]

    # Select all wallets
    wallets = wallet_rankings  # Already limited to 1,000 by the query
    print(f"Selected {len(wallets)} wallets for P&L analysis.")

    # Fetch swaps for all wallets
    print("Fetching swaps for all wallets (including Soroban transactions)...")
    wallet_addresses = [wallet["source_account"] for wallet in wallets]
    swaps_by_wallet = fetch_swaps_for_all_wallets(wallet_addresses, limit_per_wallet=200, batch_size=100)

    # Prepare data for parallel processing
    wallet_data_list = []
    for wallet in wallets:
        wallet_address = wallet["source_account"]
        wallet_data_list.append({
            "source_account": wallet_address,
            "num_swaps": wallet["num_swaps"],
            "total_volume_xlm": wallet["total_volume_xlm"],
            "swaps": swaps_by_wallet.get(wallet_address, [])
        })

    # Analyze P&L in parallel
    print(f"Analyzing P&L for {len(wallet_data_list)} wallets using {cpu_count()} CPU cores...")
    with Pool(processes=cpu_count()) as pool:
        pnl_results = pool.map(estimate_pnl_for_wallet, wallet_data_list)

    # Save results to JSON
    with open("wallet_pnl.json", "w") as f:
        json.dump(pnl_results, f, indent=2, default=str)

    print(f"Saved P&L results for {len(pnl_results)} wallets to wallet_pnl.json")
