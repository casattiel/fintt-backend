import mysql.connector
from mysql.connector import pooling
import os

# Global database pool
db_pool = None

def init_db():
    """Initialize the database connection pool."""
    global db_pool
    if db_pool is None:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="fintt_pool",
            pool_size=5,  # Adjust based on your app's requirements
            pool_reset_session=True,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
    return db_pool

def get_db_pool():
    """Retrieve the initialized database connection pool."""
    global db_pool
    if not db_pool:
        raise Exception("Database connection pool has not been initialized.")
    return db_pool
