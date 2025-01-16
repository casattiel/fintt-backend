import os
import stripe
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException, Request, Depends
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

# Firebase private key configuration
firebase_creds = {
    "type": "service_account",
    "project_id": "fintt-f8479",
    "private_key_id": "b0484c643022c5cf96b30797cb43f991561d7889",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCLoP/zmvA2XoXo
... (truncated for brevity)
-----END PRIVATE KEY-----""",
    "client_email": "firebase-adminsdk-xzgvh@fintt-f8479.iam.gserviceaccount.com",
    "client_id": "113725028417258551792",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xzgvh@fintt-f8479.iam.gserviceaccount.com"
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
        user = auth.create_user(email=data.email, password=data.password)
        return {"message": "User registered successfully", "uid": user.uid}
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=400, detail="Error registering user")

# User Login
@app.post("/login")
async def login_user(data: LoginData):
    try:
        user = auth.get_user_by_email(data.email)
        token = auth.create_custom_token(user.uid)
        return {"message": "Login successful", "token": token.decode("utf-8")}
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

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
            market_data.append({
                "crypto": base_currency,
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

@app.post("/trade/buy")
async def buy_crypto(data: TradeData, request: Request):
    user = await verify_user(request.headers.get("Authorization"))
    try:
        pair = f"X{data.crypto}ZUSD"
        response = kraken_api_request(f"public/Ticker?pair={pair}")
        if "error" in response and response["error"]:
            raise HTTPException(status_code=404, detail="Crypto not found")

        price = float(response["result"][pair]["c"][0])
        total_cost = price * data.amount

        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT balance FROM wallets WHERE user_id = %s", (user["uid"],))
        wallet = cursor.fetchone()
        if not wallet or wallet["balance"] < total_cost:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        cursor.execute("UPDATE wallets SET balance = balance - %s WHERE user_id = %s", (total_cost, user["uid"]))
        cursor.execute(
            "INSERT INTO portfolio (user_id, crypto, amount) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE amount = amount + %s",
            (user["uid"], data.crypto, data.amount, data.amount)
        )
        conn.commit()
        return {"message": "Crypto purchased successfully"}
    except Exception as e:
        logger.error(f"Error buying crypto: {e}")
        raise HTTPException(status_code=500, detail="Error processing trade")

@app.post("/trade/sell")
async def sell_crypto(data: TradeData, request: Request):
    user = await verify_user(request.headers.get("Authorization"))
    try:
        pair = f"X{data.crypto}ZUSD"
        response = kraken_api_request(f"public/Ticker?pair={pair}")
        if "error" in response and response["error"]:
            raise HTTPException(status_code=404, detail="Crypto not found")

        price = float(response["result"][pair]["c"][0])
        total_earnings = price * data.amount

        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT amount FROM portfolio WHERE user_id = %s AND crypto = %s", (user["uid"], data.crypto))
        portfolio = cursor.fetchone()
        if not portfolio or portfolio["amount"] < data.amount:
            raise HTTPException(status_code=400, detail="Insufficient crypto balance")

        cursor.execute("UPDATE portfolio SET amount = amount - %s WHERE user_id = %s AND crypto = %s", (data.amount, user["uid"], data.crypto))
        cursor.execute("UPDATE wallets SET balance = balance + %s WHERE user_id = %s", (total_earnings, user["uid"]))
        conn.commit()
        return {"message": "Crypto sold successfully"}
    except Exception as e:
        logger.error(f"Error selling crypto: {e}")
        raise HTTPException(status_code=500, detail="Error processing trade")

@app.post("/subscription")
async def subscribe(data: SubscriptionData, request: Request):
    user = await verify_user(request.headers.get("Authorization"))
    try:
        plan_price = 30 if data.plan.lower() == "basic" else 70
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("INSERT INTO subscriptions (user_id, plan, price, is_active) VALUES (%s, %s, %s, 1) ON DUPLICATE KEY UPDATE plan=%s, price=%s, is_active=1",
                       (user["uid"], data.plan, plan_price, data.plan, plan_price))
        conn.commit()
        return {"message": f"Subscribed to {data.plan} plan successfully"}
    except Exception as e:
        logger.error(f"Error processing subscription: {e}")
        raise HTTPException(status_code=500, detail="Error processing subscription")
