import os
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import Error

db_pool = None

def init_db():
    global db_pool
    try:
        db_pool = MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        print("Database connection pool initialized successfully")
    except Error as err:
        print(f"Error initializing database connection pool: {err}")
