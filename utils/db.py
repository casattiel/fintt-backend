import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Global database connection pool
db_pool = None

def init_db():
    """
    Initialize the database connection pool.
    """
    global db_pool
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),  # Default port is 3306
        )
        print("✅ Database connection pool initialized.")
    except mysql.connector.Error as err:
        print(f"❌ Error initializing DB connection pool: {err}")
        raise

def get_db_connection():
    """
    Get a connection from the database connection pool.
    """
    global db_pool
    if not db_pool:
        raise Exception("❌ Database connection pool is not initialized.")
    try:
        connection = db_pool.get_connection()
        if connection.is_connected():
            return connection
        else:
            raise Exception("❌ Failed to get a valid database connection.")
    except mysql.connector.Error as err:
        print(f"❌ Error getting DB connection: {err}")
        raise

def close_connection(connection):
    """
    Close the provided database connection.
    """
    if connection:
        try:
            connection.close()
            print("✅ Database connection closed.")
        except mysql.connector.Error as err:
            print(f"❌ Error closing DB connection: {err}")
