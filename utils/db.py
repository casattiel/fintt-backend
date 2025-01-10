import os
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv

load_dotenv()

db_pool = None

def init_db():
    global db_pool
    try:
        db_pool = MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        print("Database pool initialized successfully.")
    except Exception as e:
        print(f"Error initializing database pool: {e}")
        raise
