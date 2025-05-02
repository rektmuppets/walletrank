import psycopg
from stellar_sdk import Asset, Network
import json

# Your database credentials
db_params = {
    'dbname': 'horizon',
    'user': 'stellar',
    'password': 'new_stellar_pass',
    'host': 'horizon.cz2imkksk7b4.us-west-1.rds.amazonaws.com',
    'port': '5434'
}

# Use the public network passphrase (change to Network.TESTNET_NETWORK_PASSPHRASE if using testnet)
NETWORK_PASSPHRASE = Network.PUBLIC_NETWORK_PASSPHRASE

try:
    # Connect to the Horizon database
    print("Connecting to Horizon database...")
    conn = psycopg.connect(**db_params)
    cur = conn.cursor()

    # Query distinct issued assets from history_assets
    print("Querying 'history_assets' table for unique assets...")
    query = """
    SELECT DISTINCT asset_code, asset_issuer
    FROM history_assets
    WHERE asset_type IN ('credit_alphanum4', 'credit_alphanum12');
    """
    cur.execute(query)
    assets = cur.fetchall()

    # List to store the asset-to-SAC mapping
    asset_sac_mapping = []

    for asset_code, asset_issuer in assets:
        try:
            # Create an Asset object
            asset = Asset(code=asset_code, issuer=asset_issuer)

            # Compute the SAC contract ID using Stellar SDK
            sac_contract_id = asset.contract_id(network_passphrase=NETWORK_PASSPHRASE)

            # Append the mapping
            asset_sac_mapping.append({
                'asset_code': asset_code,
                'asset_issuer': asset_issuer,
                'sac_contract_id': sac_contract_id
            })
        except AttributeError as e:
            print(f"Error: SAC contract ID calculation failed. Check Stellar SDK version: {e}")
            break
        except Exception as e:
            print(f"Error processing asset {asset_code}:{asset_issuer}: {e}")

    # Write the mapping to a JSON file
    with open('asset_sac_mapping.json', 'w') as f:
        json.dump(asset_sac_mapping, f, indent=4)

    print(f"Successfully mapped {len(asset_sac_mapping)} assets to their SAC contract IDs. Output saved to 'asset_sac_mapping.json'.")

except psycopg.OperationalError as e:
    print(f"Database connection error: {e}")
    print("Please verify the database credentials and ensure the database is accessible.")
except psycopg.Error as e:
    print(f"Database query error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Clean up database resources
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
