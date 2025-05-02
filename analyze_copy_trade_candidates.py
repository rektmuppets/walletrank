import json
from collections import defaultdict

# Define common pairs
COMMON_PAIRS = [
    "XLM/USDC", "USDC/XLM", "XLM/AQUA", "AQUA/XLM",
    "XLM/XRP", "XRP/XLM", "XLM/SLT", "SLT/XLM"
]

# Load the wallet P&L data
def load_wallet_data(file_path="wallet_pnl.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# Filter wallets based on criteria
def filter_wallets(wallets):
    filtered_wallets = []
    for wallet in wallets:
        net_xlm_change = wallet["pnl"]["net_xlm_change"]
        num_swaps_analyzed = wallet["pnl"]["num_swaps_analyzed"]
        asset_pairs = wallet["pnl"]["asset_pairs"]

        # Check profitability and swaps analyzed
        if net_xlm_change <= 50 or num_swaps_analyzed <= 0:
            continue

        # Check for exotic pairs
        has_exotic_pairs = any(pair not in COMMON_PAIRS for pair in asset_pairs)
        if not has_exotic_pairs:
            continue

        filtered_wallets.append(wallet)
    return filtered_wallets

# Rank wallets based on a scoring system
def rank_wallets(wallets):
    ranked_wallets = []
    for wallet in wallets:
        net_xlm_change = wallet["pnl"]["net_xlm_change"]
        num_swaps = wallet["num_swaps"]
        total_volume_xlm = wallet["total_volume_xlm"]
        num_swaps_analyzed = wallet["pnl"]["num_swaps_analyzed"]
        asset_pairs = wallet["pnl"]["asset_pairs"]
        total_pnl_xlm = wallet["pnl"]["total_pnl_xlm"]
        num_round_trips = wallet["pnl"]["num_round_trips"]

        # Calculate metrics
        per_swap_profit = net_xlm_change / num_swaps_analyzed if num_swaps_analyzed > 0 else 0
        daily_swaps = num_swaps / 1.5  # 36 hours = 1.5 days
        pair_diversity = len(asset_pairs)

        # Scoring system (weights can be adjusted)
        # - Profitability (40%): Higher net_xlm_change is better
        # - Activity (30%): Higher daily_swaps is better
        # - Efficiency (20%): Higher per_swap_profit is better
        # - Stability (10%): Lower pair_diversity is better (less volatility)
        max_net_xlm = max(w["pnl"]["net_xlm_change"] for w in wallets)
        max_daily_swaps = max(w["num_swaps"] / 1.5 for w in wallets)
        max_per_swap_profit = max(w["pnl"]["net_xlm_change"] / w["pnl"]["num_swaps_analyzed"] for w in wallets)
        max_pair_diversity = max(len(w["pnl"]["asset_pairs"]) for w in wallets)

        profitability_score = (net_xlm_change / max_net_xlm) if max_net_xlm > 0 else 0
        activity_score = (daily_swaps / max_daily_swaps) if max_daily_swaps > 0 else 0
        efficiency_score = (per_swap_profit / max_per_swap_profit) if max_per_swap_profit > 0 else 0
        stability_score = 1 - (pair_diversity / max_pair_diversity) if max_pair_diversity > 0 else 1

        # Weighted score
        score = (
            0.4 * profitability_score +
            0.3 * activity_score +
            0.2 * efficiency_score +
            0.1 * stability_score
        )

        # Risk assessment
        risk_level = "Low" if daily_swaps > 100 else "Moderate" if daily_swaps > 10 else "High"
        if pair_diversity > 20:
            risk_level = "Moderate" if risk_level == "Low" else "High"

        # Recommendation
        trade_type = "Directional"
        if num_round_trips > 0 and total_pnl_xlm > 0:
            trade_type = "Directional and Round-Trips"

        ranked_wallets.append({
            "source_account": wallet["source_account"],
            "net_xlm_change": net_xlm_change,
            "num_swaps": num_swaps,
            "total_volume_xlm": total_volume_xlm,
            "per_swap_profit": per_swap_profit,
            "daily_swaps": daily_swaps,
            "pair_diversity": pair_diversity,
            "asset_pairs": asset_pairs,
            "score": score,
            "risk_level": risk_level,
            "trade_type": trade_type
        })

    # Sort by score descending
    ranked_wallets.sort(key=lambda x: x["score"], reverse=True)
    return ranked_wallets

# Generate recommendations
def generate_recommendations(ranked_wallets, top_n=3):
    primary_candidates = []
    secondary_candidates = []

    for i, wallet in enumerate(ranked_wallets):
        recommendation = {
            "source_account": wallet["source_account"],
            "net_xlm_change": wallet["net_xlm_change"],
            "num_swaps": wallet["num_swaps"],
            "total_volume_xlm": wallet["total_volume_xlm"],
            "per_swap_profit": wallet["per_swap_profit"],
            "daily_swaps": wallet["daily_swaps"],
            "pair_diversity": wallet["pair_diversity"],
            "asset_pairs": wallet["asset_pairs"],
            "score": wallet["score"],
            "risk_level": wallet["risk_level"],
            "trade_type": wallet["trade_type"],
            "recommendation": f"Replicate {wallet['trade_type']} trades on {', '.join(wallet['asset_pairs'][:5])}. Start with small volumes to test consistency."
        }

        if i < top_n and wallet["risk_level"] != "High":
            primary_candidates.append(recommendation)
        else:
            secondary_candidates.append(recommendation)

    return primary_candidates, secondary_candidates

# Main function to analyze and rank candidates
def analyze_copy_trade_candidates():
    # Load data
    wallets = load_wallet_data()

    # Filter wallets
    filtered_wallets = filter_wallets(wallets)
    print(f"Filtered {len(filtered_wallets)} wallets meeting criteria.")

    # Rank wallets
    ranked_wallets = rank_wallets(filtered_wallets)
    print(f"Ranked {len(ranked_wallets)} wallets.")

    # Generate recommendations
    primary_candidates, secondary_candidates = generate_recommendations(ranked_wallets)
    
    # Print results
    print("\nPrimary Candidates:")
    for candidate in primary_candidates:
        print(json.dumps(candidate, indent=2))
    
    print("\nSecondary Candidates:")
    for candidate in secondary_candidates:
        print(json.dumps(candidate, indent=2))

    # Save results
    with open("copy_trade_candidates.json", "w") as f:
        json.dump({
            "primary_candidates": primary_candidates,
            "secondary_candidates": secondary_candidates
        }, f, indent=2)

    print("\nSaved results to copy_trade_candidates.json")

if __name__ == "__main__":
    analyze_copy_trade_candidates()
