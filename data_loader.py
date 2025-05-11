import json

def load_data():
    # Load copy trade candidates
    with open("copy_trade_candidates.json", "r") as f:
        candidates_data = json.load(f)
    primary_candidates = candidates_data["primary_candidates"]
    secondary_candidates = candidates_data["secondary_candidates"]
    all_candidates = primary_candidates + secondary_candidates

    # Load domain wallet rankings
    try:
        with open("domain_wallet_rankings.json", "r") as f:
            domain_rankings = json.load(f)
    except FileNotFoundError:
        domain_rankings = []

    # Load network-wide wallet rankings
    try:
        with open("wallet_rankings.json", "r") as f:
            network_rankings = json.load(f)
    except FileNotFoundError:
        network_rankings = []

    # Load domain-specific copy trade candidates
    try:
        with open("domain_copy_trade_candidates.json", "r") as f:
            domain_copy_trade_data = json.load(f)
        domain_copy_trade_primary = domain_copy_trade_data["primary_candidates"]
        domain_copy_trade_secondary = domain_copy_trade_data["secondary_candidates"]
        domain_copy_trade_all = domain_copy_trade_primary + domain_copy_trade_secondary
    except FileNotFoundError:
        domain_copy_trade_all = []

    return all_candidates, domain_rankings, network_rankings, domain_copy_trade_all
