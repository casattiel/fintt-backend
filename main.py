import os
import stripe
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import hashlib
import requests
import time
import hmac
import base64
from firebase_admin import credentials, auth, initialize_app
import logging

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

# Initialize Firebase
firebase_creds = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
}
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
}
db_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config)

# Friendly crypto names mapping
CRYPTO_NAMES = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "ADA": "Cardano",
    "DOT": "Polkadot",
    "DOGE": "Dogecoin",
    "XRP": "Ripple",
    "LTC": "Litecoin",
    "USDT": "Tether",
    "SOL": "Solana",
    "BNB": "Binance Coin",
}

# Models
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

# Utility functions
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

async def verify_user(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")

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
            base_currency = pair[:3]
            friendly_name = CRYPTO_NAMES.get(base_currency, base_currency)
            market_data.append({
                "crypto": friendly_name,
                "last_price": info["c"][0],
                "bid": info["b"][0],
                "ask": info["a"][0]
            })
        return market_data
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail="Error fetching market data")

@app.get("/wallet")
async def get_wallet_data(request: Request):
    user = await verify_user(request.headers.get("Authorization"))
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT type, balance FROM wallets WHERE user_id = %s", (user["uid"],))
        wallets = cursor.fetchall()
        conn.close()
        return {"wallets": wallets}
    except Exception as e:
        logger.error(f"Error fetching wallet data: {e}")
        raise HTTPException(status_code=500, detail="Error fetching wallet data")

@app.get("/notifications")
async def get_notifications(request: Request):
    user = await verify_user(request.headers.get("Authorization"))
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT message, date FROM notifications WHERE user_id = %s ORDER BY date DESC", (user["uid"],))
        notifications = cursor.fetchall()
        conn.close()
        return {"notifications": notifications}
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail="Error fetching notifications")

@app.get("/portfolio")
async def get_portfolio(request: Request):
    user = await verify_user(request.headers.get("Authorization"))
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT crypto, amount FROM portfolio WHERE user_id = %s", (user["uid"],))
        portfolio = cursor.fetchall()
        conn.close()
        return {"portfolio": portfolio}
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail="Error fetching portfolio")
