import os
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import krakenex
from subscriptions import router as subscriptions_router
from fintto_chat import router as fintto_chat_router

# Load environment variables
load_dotenv()

# Environment variables for Kraken API and database
KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY", "default_api_key")
KRAKEN_SECRET_KEY = os.getenv("KRAKEN_SECRET_KEY", "default_secret_key")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "fint_db")

# Initialize Kraken API
kraken_api = krakenex.API()
kraken_api.key = KRAKEN_API_KEY
kraken_api.secret = KRAKEN_SECRET_KEY

# FastAPI application setup
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pooling
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
)

@app.on_event("startup")
async def startup_event():
    try:
        conn = db_pool.get_connection()
        if conn.is_connected():
            print("Database connection successful")
            conn.close()
    except Error as err:
        raise Exception(f"Error connecting to MySQL: {err}")

@app.get("/")
async def root():
    return {"message": "FINTT Backend is running with Kraken integration!"}

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Models
class LoginData(BaseModel):
    email: str
    password: str

class RegisterData(BaseModel):
    name: str
    email: str
    password: str
    country: str

class TradeData(BaseModel):
    user_id: int
    crypto_pair: str
    amount: float
    action: str  # "buy" or "sell"

class SubscriptionUpgrade(BaseModel):
    user_id: int
    new_plan: str  # "basic" or "premium"

# Authentication endpoints
@app.post("/register")
async def register(data: RegisterData):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(data.password)
        query = "INSERT INTO users (name, email, password, country) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (data.name, data.email, hashed_password, data.country))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "User registered successfully"}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error registering user: {err}")

@app.post("/login")
async def login(data: LoginData):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        hashed_password = hash_password(data.password)
        query = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (data.email, hashed_password))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        cursor.close()
        conn.close()
        return {"message": "Login successful", "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error during login: {err}")

# Kraken trading endpoint
@app.post("/trade")
async def execute_trade(data: TradeData):
    try:
        if data.action not in ["buy", "sell"]:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'buy' or 'sell'.")
        response = kraken_api.query_private('AddOrder', {
            'pair': data.crypto_pair,
            'type': data.action,
            'ordertype': 'market',
            'volume': data.amount
        })

        if response.get("error"):
            raise HTTPException(status_code=500, detail=f"Kraken API error: {response['error']}")

        return {"message": "Trade executed successfully", "details": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing trade: {e}")

@app.post("/subscriptions/upgrade")
async def upgrade_subscription(data: SubscriptionUpgrade):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "UPDATE users SET subscription_plan = %s WHERE id = %s"
        cursor.execute(query, (data.new_plan, data.user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Subscription upgraded successfully", "new_plan": data.new_plan}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error upgrading subscription: {err}")

@app.get("/market/prices")
async def get_market_prices():
    try:
        response = kraken_api.query_public('Ticker', {'pair': 'XXBTZUSD'})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market prices: {e}")

# Include additional routers
app.include_router(subscriptions_router)
app.include_router(fintto_chat_router, prefix="/api")
