import os
from mysql.connector import pooling
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global database connection pool
db_pool = None

def init_db():
    """
    Initializes the database connection pool.
    This function creates a connection pool with the provided database credentials.
    """
    global db_pool
    try:
        # Create a MySQL connection pool
        db_pool = pooling.MySQLConnectionPool(
            pool_name="fintt_pool",
            pool_size=10,  # Adjust the pool size based on your needs
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        print("Database connection pool initialized successfully")
    except Exception as e:
        print(f"Error initializing database connection pool: {e}")
