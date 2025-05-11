import json
import psycopg
from datetime import datetime, timedelta, timezone
import requests
import toml
import os

# Database connection parameters
DB_HOST = "horizon.cz2imkksk7b4.us-west-1.rds.amazonaws.com"
DB_PORT = 5434
DB_NAME = "horizon"
DB_USER = "stellar"
DB_PASS = "new_stellar_pass"

# Connect to the PostgreSQL database
conn = psycopg.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    connect_timeout=300,
    sslmode="require"
)
cursor = conn.cursor()

# Fetch assets issued by a domain by directly parsing stellar.toml
def get_assets_by_domain(domain):
    try:
        response = requests.get(f"https://{domain}/.well-known/stellar.toml", timeout=10)
        response.raise_for_status()
        toml_content = toml.loads(response.text)
        
        assets = []
        if "CURRENCIES" in toml_content:
            for currency in toml_content["CURRENCIES"]:
                if "code" in currency and "issuer" in currency and "status" in currency and currency["status"] == "live":
                    assets.append((currency["code"], currency["issuer"]))
        
        print(f"Assets found for {domain}: {len(assets)} assets")
        return assets
    except (requests.RequestException, toml.TomlDecodeError) as e:
        print(f"Error fetching or parsing stellar.toml for {domain}: {e}")
        return []

# Fetch swaps for assets issued by specified domains
def fetch_swaps_for_domains(domains):
    start_time = datetime.now(timezone.utc) - timedelta(hours=36)  # Reduced to 36 hours
    swaps_by_wallet = {}

    # Get assets for each domain
    target_assets = []
    for domain in domains:
        assets = get_assets_by_domain(domain)
        target_assets.extend(assets)

    if not target_assets:
        print("No assets found for the specified domains.")
        return swaps_by_wallet

    print(f"Processing swaps for {len(target_assets)} assets...")

    # Prepare conditions for all assets in a single query
    conditions = []
    asset_params = []
    for asset_code, asset_issuer in target_assets:
        condition = """
            ((ho.details->>'asset_type' = 'credit_alphanum4' AND ho.details->>'asset_code' = %s AND ho.details->>'asset_issuer' = %s)
            OR (ho.details->>'source_asset_type' = 'credit_alphanum4' AND ho.details->>'source_asset_code' = %s AND ho.details->>'source_asset_issuer' = %s))
        """
        conditions.append(condition)
        asset_params.extend([asset_code, asset_issuer, asset_code, asset_issuer])

    # Combine all conditions with OR
    asset_conditions = " OR ".join(conditions)

    # Single query to fetch swaps for all assets
    query = f"""
    WITH path_payment_ops AS (
        SELECT DISTINCT ON (ho.transaction_id)
            ho.transaction_id,
            ho.source_account,
            ho.details->>'amount' as amount,
            ho.details->>'source_amount' as source_amount,
            ho.details->>'asset_type' as dest_asset_type,
            ho.details->>'source_asset_type' as src_asset_type,
            COALESCE(ho.details->>'fee', '0')::float as fee,
            CASE
                WHEN ho.details->>'asset_type' = 'credit_alphanum4' THEN ho.details->>'asset_code'
                WHEN ho.details->>'source_asset_type' = 'credit_alphanum4' THEN ho.details->>'source_asset_code'
                ELSE 'UNKNOWN'
            END as asset_code
        FROM history_operations ho
        JOIN history_transactions ht ON ho.transaction_id = ht.id
        WHERE 
            ho.type = 13  -- PathPaymentStrictSend
            AND ht.successful = true
            AND ht.created_at >= %s
            AND ho.source_account LIKE 'G%%' ESCAPE ''
            AND ({asset_conditions})
        ORDER BY ho.transaction_id, ho.id DESC
    ),
    payment_ops AS (
        SELECT 
            ho.transaction_id,
            ho.source_account,
            ho.details->>'amount' as amount,
            ho.details->>'source_amount' as source_amount,
            ho.details->>'asset_type' as dest_asset_type,
            ho.details->>'source_asset_type' as src_asset_type,
            0 as fee,
            CASE
                WHEN ho.details->>'asset_type' = 'credit_alphanum4' THEN ho.details->>'asset_code'
                WHEN ho.details->>'source_asset_type' = 'credit_alphanum4' THEN ho.details->>'source_asset_code'
                ELSE 'UNKNOWN'
            END as asset_code
        FROM history_operations ho
        JOIN history_transactions ht ON ho.transaction_id = ht.id
        WHERE 
            ho.type = 2  -- Payment
            AND ht.successful = true
            AND ht.created_at >= %s
            AND ho.source_account LIKE 'G%%' ESCAPE ''
            AND ({asset_conditions})
    ),
    all_ops AS (
        SELECT * FROM path_payment_ops
        UNION ALL
        SELECT * FROM payment_ops
    )
    SELECT 
        source_account,
        COUNT(*) as num_swaps,
        SUM(CASE 
            WHEN dest_asset_type = 'native' THEN (amount)::float - fee
            ELSE 0
        END) as xlm_inflows,
        SUM(CASE 
            WHEN src_asset_type = 'native' THEN (source_amount)::float + fee
            ELSE 0
        END) as xlm_outflows,
        asset_code
    FROM all_ops
    GROUP BY source_account, asset_code
    HAVING COUNT(*) >= 1
    ORDER BY num_swaps DESC;
    """
    # Construct the full params list
    params = [start_time] + asset_params + [start_time] + asset_params
    cursor.execute("SET statement_timeout = '300s';")  # 5-minute timeout
    cursor.execute(query, params)
    results = cursor.fetchall()

    for row in results:
        wallet = row[0]
        asset_code = row[4] if row[4] else "UNKNOWN"
        if wallet not in swaps_by_wallet:
            swaps_by_wallet[wallet] = {
                "num_swaps": 0,
                "xlm_inflows": 0.0,
                "xlm_outflows": 0.0,
                "assets_traded": {}
            }
        swaps_by_wallet[wallet]["num_swaps"] += row[1]
        swaps_by_wallet[wallet]["xlm_inflows"] += row[2] or 0.0
        swaps_by_wallet[wallet]["xlm_outflows"] += row[3] or 0.0
        if asset_code not in swaps_by_wallet[wallet]["assets_traded"]:
            swaps_by_wallet[wallet]["assets_traded"][asset_code] = {
                "num_swaps": 0,
                "xlm_inflows": 0.0,
                "xlm_outflows": 0.0
            }
        swaps_by_wallet[wallet]["assets_traded"][asset_code]["num_swaps"] += row[1]
        swaps_by_wallet[wallet]["assets_traded"][asset_code]["xlm_inflows"] += row[2] or 0.0
        swaps_by_wallet[wallet]["assets_traded"][asset_code]["xlm_outflows"] += row[3] or 0.0

    return swaps_by_wallet

# Main script logic
if __name__ == "__main__":
    print("Fetching swaps for assets issued by specified domains...")
    try:
        domains = ["lu.meme"]
        swaps_by_wallet = fetch_swaps_for_domains(domains)

        wallet_rankings = []
        for wallet, data in swaps_by_wallet.items():
            wallet_rankings.append({
                "source_account": wallet,
                "num_swaps": data["num_swaps"],
                "xlm_inflows": data["xlm_inflows"],
                "xlm_outflows": data["xlm_outflows"],
                "net_xlm_flow": data["xlm_inflows"] - data["xlm_outflows"],
                "assets_traded": data["assets_traded"]
            })

        wallet_rankings.sort(key=lambda x: x["num_swaps"], reverse=True)

        # Archive the current domain_wallet_rankings.json with a timestamp
        if os.path.exists("domain_wallet_rankings.json"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.rename("domain_wallet_rankings.json", f"backups/domain_wallet_rankings_{timestamp}.json")

        with open("domain_wallet_rankings.json", "w") as f:
            json.dump(wallet_rankings, f, indent=2)

        print(f"Saved {len(wallet_rankings)} wallet rankings to domain_wallet_rankings.json")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Clean up
        cursor.close()
        conn.close()
