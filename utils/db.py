import os
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection pool
db_pool = None

def init_db():
    global db_pool
    try:
        db_pool = MySQLConnectionPool(
            pool_name="fintt_pool",
            pool_size=5,
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        print("Database connection pool initialized successfully.")
    except Exception as e:
        print(f"Error initializing database connection pool: {e}")
        raise
