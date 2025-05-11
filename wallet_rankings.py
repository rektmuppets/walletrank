import json
import psycopg
from datetime import datetime, timedelta, timezone
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

# Fetch swaps for the last 36 hours
def fetch_swaps():
    start_time = datetime.now(timezone.utc) - timedelta(hours=36)
    query = """
    SELECT 
        ho.source_account,
        COUNT(*) as num_swaps,
        SUM(CASE 
            WHEN ho.type = 2 AND ho.details->>'asset_type' = 'native' THEN (ho.details->>'amount')::float
            WHEN ho.type = 2 AND ho.details->>'source_asset_type' = 'native' THEN (ho.details->>'source_amount')::float
            WHEN ho.type = 13 AND ho.details->>'source_asset_type' = 'native' THEN (ho.details->>'source_amount')::float
            WHEN ho.type = 13 AND ho.details->>'asset_type' = 'native' THEN (ho.details->>'amount')::float
            WHEN ho.type = 24 THEN 100.0  -- Placeholder for Soroban transactions
            ELSE 0
        END) as total_volume_xlm
    FROM history_operations ho
    JOIN history_transactions ht ON ho.transaction_id = ht.id
    WHERE 
        ho.type IN (2, 13, 24)  -- Payment, PathPaymentStrictSend, InvokeHostFunction
        AND ht.successful = true
        AND ht.created_at >= %s  -- Use created_at
        AND ho.source_account LIKE 'G%%' ESCAPE ''
    GROUP BY ho.source_account
    HAVING COUNT(*) >= 5
    ORDER BY num_swaps DESC
    LIMIT 1000;
    """
    # Set a statement timeout to prevent hanging
    cursor.execute("SET statement_timeout = '300s';")  # 5-minute timeout
    cursor.execute(query, (start_time,))
    results = cursor.fetchall()

    wallet_rankings = []
    for row in results:
        wallet_rankings.append({
            "source_account": row[0],
            "num_swaps": row[1],
            "total_volume_xlm": row[2] or 0.0  # Handle NULL volumes
        })

    return wallet_rankings

# Main script logic
if __name__ == "__main__":
    print("Fetching swaps from Horizon PostgreSQL database...")
    try:
        wallet_rankings = fetch_swaps()

        # Archive the current wallet_rankings.json with a timestamp
        if os.path.exists("wallet_rankings.json"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.rename("wallet_rankings.json", f"backups/wallet_rankings_{timestamp}.json")

        with open("wallet_rankings.json", "w") as f:
            json.dump(wallet_rankings, f, indent=2)

        print(f"Saved {len(wallet_rankings)} wallet rankings to wallet_rankings.json")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Clean up
        cursor.close()
        conn.close()
