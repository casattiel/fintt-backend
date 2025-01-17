import os
import json
import stripe
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from firebase_admin import credentials, auth, initialize_app
import logging
import time
import hmac
import hashlib
import base64
import requests

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase private key configuration from environment
firebase_creds = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(firebase_creds)
initialize_app(cred)

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Kraken API Configuration
KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY")
KRAKEN_API_SECRET = os.getenv("KRAKEN_API_SECRET")
KRAKEN_API_URL = "https://api.kraken.com/0"

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT"),
}
db_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config)

# Models
class LoginData(BaseModel):
    email: str
    password: str

class RegisterData(BaseModel):
    email: str
    password: str
    name: str
    country: str

class TradeData(BaseModel):
    crypto: str
    amount: float

class SubscriptionData(BaseModel):
    plan: str

@app.on_event("startup")
async def startup_event():
    try:
        conn = db_pool.get_connection()
        if conn.is_connected():
            logger.info("Database connection successful")
            conn.close()
    except Error as err:
        logger.error(f"Error connecting to MySQL: {err}")
        raise Exception(f"Error connecting to MySQL: {err}")

@app.get("/")
async def root():
    return {"message": "FINTT Backend is running with optimized functionality!"}

# User Registration
@app.post("/register")
async def register_user(data: RegisterData):
    try:
        # Create a new Firebase user
        user = auth.create_user(email=data.email, password=data.password)
        
        # Store user information in the database
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (firebase_uid, name, email, country) VALUES (%s, %s, %s, %s)",
            (user.uid, data.name, data.email, data.country),
        )
        conn.commit()
        conn.close()
        
        return {"message": "User registered successfully", "uid": user.uid}
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=400, detail="Error registering user")

# User Login
@app.post("/login")
async def login_user(data: LoginData):
    try:
        # Authenticate using Firebase
        user = auth.get_user_by_email(data.email)
        token = auth.create_custom_token(user.uid)
        
        # Fetch additional user details from the database
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM users WHERE firebase_uid = %s", (user.uid,))
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found in database")
        
        return {
            "message": "Login successful",
            "user": user_data,
            "token": token.decode("utf-8"),
        }
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

# Utility functions for Kraken API
def kraken_api_request(endpoint: str, data=None, is_private=False):
    try:
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
            post_data = data if data else None

        response = requests.post(url, headers=headers, data=post_data)
        return response.json()
    except Exception as e:
        logger.error(f"Kraken API request failed: {e}")
        raise HTTPException(status_code=500, detail="Error communicating with Kraken API")

@app.get("/market")
async def get_market_data():
    try:
        response = kraken_api_request("public/AssetPairs")
        if "error" in response and response["error"]:
            raise HTTPException(status_code=500, detail="Error fetching market data")

        pairs = list(response["result"].keys())
        ticker_response = kraken_api_request(f"public/Ticker?pair={','.join(pairs)}")
        if "error" in ticker_response and ticker_response["error"]:
            raise HTTPException(status_code=500, detail="Error fetching ticker data")

        market_data = []
        for pair, info in ticker_response["result"].items():
            market_data.append({
                "crypto": pair,
                "last_price": info["c"][0],
                "bid": info["b"][0],
                "ask": info["a"][0]
            })
        return market_data
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail="Error fetching market data")

@app.post("/subscription")
async def subscribe(data: SubscriptionData, request: Request):
    user = await verify_user(request.headers.get("Authorization"))
    try:
        plan_price = 30 if data.plan.lower() == "basic" else 70
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO subscriptions (user_id, plan, price, is_active) VALUES (%s, %s, %s, 1)",
                       (user["uid"], data.plan, plan_price))
        conn.commit()
        conn.close()
        return {"message": f"Subscribed to {data.plan} plan successfully"}
    except Exception as e:
        logger.error(f"Error processing subscription: {e}")
        raise HTTPException(status_code=500, detail="Error processing subscription")
