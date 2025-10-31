import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a function to get a PostgreSQL connection
def get_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            dbname=os.getenv("POSTGRES_DB", "mortgage_decisioning"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        return connection
    except Exception as e:
        print("Failed to connect to the database:", e)
        raise

if __name__ == "__main__":
    conn = get_connection()
    print("Connection established:", conn)
    conn.close()