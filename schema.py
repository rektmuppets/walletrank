import psycopg

# Your database credentials
db_params = {
    'dbname': 'horizon',
    'user': 'stellar',
    'password': 'new_stellar_pass',
    'host': 'horizon.cz2imkksk7b4.us-west-1.rds.amazonaws.com',
    'port': '5434'
}

try:
    # Connect to the database
    conn = psycopg.connect(**db_params)
    cur = conn.cursor()

    # Query to list all tables in the public schema
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
    """)
    tables = cur.fetchall()

    # Print the list of tables
    print("Tables in your Horizon database:")
    for table in tables:
        print(table[0])

except psycopg.Error as e:
    print(f"Database connection error: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
