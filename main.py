import os
import stripe
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import requests
import time
import hmac
import base64

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_51QfQbOCFuzFSWK4L7KMEakMZVSFM7dCq2FHekAzw9Dj5gjgjEu3lXMXlCX2VJvFWqEYCm8mVYr9e2GHLu1anUBhM00HeEKCAwW")
BASIC_PLAN_PRICE_ID = "price_1QfCzWCFuzFSWK4Lr4Lo26jX"
PREMIUM_PLAN_PRICE_ID = "price_1QfD4WCFuzFSWK4LzFLo36jX"

# Kraken API Configuration
KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY", "y0R5IG8Hamnc6ifMdaugcebvLDoFHRVh/4re8EKkohCGR1/qyNQQLCu+")
KRAKEN_API_SECRET = os.getenv("KRAKEN_API_SECRET", "mX9TDrjxpWFckAnOqoZ1Mi3XjnJjGUyxJVrR7DAEbJv/tG6DhMSt2LUUTNLOwOIi7NrXMYrzOZOY8DramPHRWA==")
KRAKEN_API_URL = "https://api.kraken.com/0"

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST", "fint-db.ctkokc288j85.us-east-2.rds.amazonaws.com"),
    "user": os.getenv("DB_USER", "fint_user"),
    "password": os.getenv("DB_PASSWORD", "JesusismyLord33!"),
    "database": os.getenv("DB_NAME", "fint_db"),
}

db_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config)

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
    return {"message": "FINTT Backend is running with full broker functionality!"}

# Models
class LoginData(BaseModel):
    email: str
    password: str

class RegisterData(BaseModel):
    name: str
    email: str
    password: str
    country: str

class SubscriptionData(BaseModel):
    email: str
    plan: str  # "basic" or "premium"

class TradeData(BaseModel):
    user_id: int
    crypto: str
    amount: float

class WalletData(BaseModel):
    user_id: int
    type: str  # "hot" or "cold"
    amount: float

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def kraken_api_request(endpoint: str, data=None, is_private=False):
    headers = {}
    url = f"{KRAKEN_API_URL}/{endpoint}"

    if is_private:
        nonce = str(int(time.time() * 1000))
        post_data = f"nonce={nonce}"
        if data:
            post_data += "&" + "&".join(f"{key}={value}" for key, value in data.items())
        message = f"{nonce}{post_data}".encode("utf-8")
        signature = hmac.new(
            base64.b64decode(KRAKEN_API_SECRET),
            f"/0/{endpoint}".encode("utf-8") + hashlib.sha256(message).digest(),
            hashlib.sha512
        )
        headers["API-Key"] = KRAKEN_API_KEY
        headers["API-Sign"] = base64.b64encode(signature.digest())
    else:
        post_data = None
        if data:
            post_data = data

    response = requests.post(url, headers=headers, data=post_data)
    return response.json()

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

# Market endpoint
@app.get("/market")
async def get_market_data():
    try:
        response = kraken_api_request("public/AssetPairs")
        if "error" in response and response["error"]:
            raise HTTPException(status_code=500, detail="Error fetching market data")

        pairs = [pair for pair in response["result"]]
        ticker_response = kraken_api_request(f"public/Ticker?pair={','.join(pairs)}")
        if "error" in ticker_response and ticker_response["error"]:
            raise HTTPException(status_code=500, detail="Error fetching ticker data")

        market_data = {}
        for pair, info in ticker_response["result"].items():
            market_data[pair] = {
                "ask": info["a"][0],
                "bid": info["b"][0],
                "last_trade": info["c"][0],
            }
        return market_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")

# Trading endpoints
@app.post("/trade/buy")
async def buy_crypto(data: TradeData):
    # Buying logic here
    pass

@app.post("/trade/sell")
async def sell_crypto(data: TradeData):
    # Selling logic here
    pass

# Wallet endpoints
@app.get("/wallet")
async def get_wallet(user_id: int, type: str):
    # Wallet retrieval logic here
    pass
