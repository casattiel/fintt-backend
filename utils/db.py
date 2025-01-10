import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

db_pool = None

def init_db():
    global db_pool
    try:
        db_pool = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            pool_name="mypool",
            pool_size=5,
        )
        print("Database connection pool initialized")
    except mysql.connector.Error as err:
        print(f"Error initializing DB connection pool: {err}")
        raise

def get_db_connection():
    global db_pool
    if not db_pool:
        raise Exception("Database connection pool is not initialized.")
    return db_pool
