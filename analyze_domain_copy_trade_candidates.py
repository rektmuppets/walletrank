import json
from collections import defaultdict

# Load the domain wallet rankings data
def load_wallet_data(file_path="domain_wallet_rankings.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# Determine the most common trading pairs dynamically
def get_common_pairs(wallets, top_n=5):
    pair_counts = defaultdict(int)
    for wallet in wallets:
        # Generate asset pairs from assets_traded
        for asset_code, data in wallet["assets_traded"].items():
            pair_counts[f"XLM/{asset_code}"] += data["num_swaps"]
            pair_counts[f"{asset_code}/XLM"] += data["num_swaps"]
    
    # Sort pairs by frequency and take the top N
    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
    common_pairs = [pair for pair, count in sorted_pairs[:top_n]]
    return common_pairs

# Filter wallets based on criteria
def filter_wallets(wallets, common_pairs):
    filtered_wallets = []
    for wallet in wallets:
        net_xlm_flow = wallet["net_xlm_flow"]
        num_swaps = wallet["num_swaps"]

        # Generate asset pairs from assets_traded
        asset_pairs = set()
        for asset_code, data in wallet["assets_traded"].items():
            asset_pairs.add(f"XLM/{asset_code}")
            asset_pairs.add(f"{asset_code}/XLM")

        # Check profitability and number of swaps
        if net_xlm_flow <= 50 or num_swaps <= 0:
            continue

        # Check for exotic pairs (not in the common pairs)
        has_exotic_pairs = any(pair not in common_pairs for pair in asset_pairs)
        if not has_exotic_pairs:
            continue

        wallet["asset_pairs"] = list(asset_pairs)
        filtered_wallets.append(wallet)
    return filtered_wallets

# Rank wallets based on a scoring system
def rank_wallets(wallets):
    ranked_wallets = []
    for wallet in wallets:
        net_xlm_flow = wallet["net_xlm_flow"]
        num_swaps = wallet["num_swaps"]
        asset_pairs = wallet["asset_pairs"]

        # Calculate metrics
        per_swap_profit = net_xlm_flow / num_swaps if num_swaps > 0 else 0
        daily_swaps = num_swaps / 2.0  # 48 hours = 2 days
        pair_diversity = len(asset_pairs)

        # Scoring system (weights can be adjusted)
        # - Profitability (40%): Higher net_xlm_flow is better
        # - Activity (30%): Higher daily_swaps is better
        # - Efficiency (20%): Higher per_swap_profit is better
        # - Stability (10%): Lower pair_diversity is better (less volatility)
        max_net_xlm = max(w["net_xlm_flow"] for w in wallets)
        max_daily_swaps = max(w["num_swaps"] / 2.0 for w in wallets)
        max_per_swap_profit = max(w["net_xlm_flow"] / w["num_swaps"] for w in wallets if w["num_swaps"] > 0)
        max_pair_diversity = max(len(w["asset_pairs"]) for w in wallets)

        profitability_score = (net_xlm_flow / max_net_xlm) if max_net_xlm > 0 else 0
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

        ranked_wallets.append({
            "source_account": wallet["source_account"],
            "net_xlm_change": net_xlm_flow,  # Align with copy trade candidates
            "num_swaps": num_swaps,
            "total_volume_xlm": wallet["xlm_inflows"] + wallet["xlm_outflows"],
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
def analyze_domain_copy_trade_candidates():
    # Load data
    wallets = load_wallet_data()

    # Determine common pairs dynamically
    common_pairs = get_common_pairs(wallets)
    print(f"Determined common pairs: {common_pairs}")

    # Filter wallets
    filtered_wallets = filter_wallets(wallets, common_pairs)
    print(f"Filtered {len(filtered_wallets)} domain-specific wallets meeting criteria.")

    # Rank wallets
    ranked_wallets = rank_wallets(filtered_wallets)
    print(f"Ranked {len(ranked_wallets)} domain-specific wallets.")

    # Generate recommendations
    primary_candidates, secondary_candidates = generate_recommendations(ranked_wallets)
    
    # Print results
    print("\nPrimary Domain-Specific Candidates:")
    for candidate in primary_candidates:
        print(json.dumps(candidate, indent=2))
    
    print("\nSecondary Domain-Specific Candidates:")
    for candidate in secondary_candidates:
        print(json.dumps(candidate, indent=2))

    # Archive the current domain_copy_trade_candidates.json with a timestamp
    import os
    from datetime import datetime
    if os.path.exists("domain_copy_trade_candidates.json"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.rename("domain_copy_trade_candidates.json", f"backups/domain_copy_trade_candidates_{timestamp}.json")

    # Save results
    with open("domain_copy_trade_candidates.json", "w") as f:
        json.dump({
            "primary_candidates": primary_candidates,
            "secondary_candidates": secondary_candidates
        }, f, indent=2)

    print("\nSaved domain-specific results to domain_copy_trade_candidates.json")

if __name__ == "__main__":
    analyze_domain_copy_trade_candidates()
