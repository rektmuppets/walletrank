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

    # Load meme trade candidates
    try:
        with open("meme_trade_candidates.json", "r") as f:
            meme_candidates_data = json.load(f)
        meme_primary_candidates = meme_candidates_data["primary_candidates"]
        meme_secondary_candidates = meme_candidates_data["secondary_candidates"]
        meme_all_candidates = meme_primary_candidates + meme_secondary_candidates
    except FileNotFoundError:
        meme_all_candidates = []

    return all_candidates, domain_rankings, meme_all_candidates
