import os
import stripe
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import requests
import time
import hmac
import base64
from firebase_admin import credentials, auth, initialize_app

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
BASIC_PLAN_PRICE_ID = "price_1QfCzWCFuzFSWK4Lr4Lo26jX"
PREMIUM_PLAN_PRICE_ID = "price_1QfD4WCFuzFSWK4LzFLo36jX"

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
class TradeData(BaseModel):
    user_id: int
    crypto: str
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

# Middleware for Firebase authentication
async def verify_user(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Unauthorized")

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
            base_currency = pair[:-3] if pair.endswith("USD") else pair
            friendly_name = CRYPTO_NAMES.get(base_currency, base_currency)
            market_data[friendly_name] = {
                "pair": pair,
                "ask": info["a"][0],
                "bid": info["b"][0],
                "last_trade": info["c"][0],
            }
        return market_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")

# Buy endpoint
@app.post("/trade/buy")
async def buy_crypto(data: TradeData, user=Depends(verify_user)):
    try:
        # Get market price
        response = kraken_api_request(f"public/Ticker?pair={data.crypto}USD")
        if "error" in response and response["error"]:
            raise HTTPException(status_code=404, detail="Crypto not found")

        price = float(response["result"][f"X{data.crypto}ZUSD"]["c"][0])
        total_cost = price * data.amount

        # Deduct balance from wallet
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE wallets SET balance = balance - %s WHERE user_id = %s AND type = 'hot'", (total_cost, user["uid"]))
        conn.commit()

        # Add crypto to portfolio
        cursor.execute(
            "INSERT INTO portfolio (user_id, crypto, amount) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE amount = amount + %s",
            (user["uid"], data.crypto, data.amount, data.amount),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Crypto purchased successfully", "crypto": data.crypto, "amount": data.amount, "price": price}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error buying crypto: {str(e)}")

# Sell endpoint
@app.post("/trade/sell")
async def sell_crypto(data: TradeData, user=Depends(verify_user)):
    try:
        # Get market price
        response = kraken_api_request(f"public/Ticker?pair={data.crypto}USD")
        if "error" in response and response["error"]:
            raise HTTPException(status_code=404, detail="Crypto not found")

        price = float(response["result"][f"X{data.crypto}ZUSD"]["c"][0])
        total_earnings = price * data.amount

        # Deduct crypto from portfolio
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE portfolio SET amount = amount - %s WHERE user_id = %s AND crypto = %s", (data.amount, user["uid"], data.crypto))
        conn.commit()

        # Add balance to wallet
        cursor.execute("UPDATE wallets SET balance = balance + %s WHERE user_id = %s AND type = 'hot'", (total_earnings, user["uid"]))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Crypto sold successfully", "crypto": data.crypto, "amount": data.amount, "price": price}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error selling crypto: {str(e)}")
