import os
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import requests
from subscriptions import router as subscriptions_router
from fintto_chat import router as fintto_chat_router

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

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST", "fint-db.ctkokc288j85.us-east-2.rds.amazonaws.com"),
    "user": os.getenv("DB_USER", "fint_user"),
    "password": os.getenv("DB_PASSWORD", "JesusismyLord33!"),
    "database": os.getenv("DB_NAME", "fint_db"),
}

db_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config)

# Crypto API Configuration
CRYPTO_API_URL = "https://api.coingecko.com/api/v3"
TOP_10_CRYPTOS = ["bitcoin", "ethereum", "binancecoin", "ripple", "cardano", "dogecoin", "solana", "polkadot", "polygon", "litecoin"]

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

class TradeData(BaseModel):
    user_id: int
    crypto: str
    amount: float

class TransactionLog(BaseModel):
    user_id: int
    crypto: str
    action: str  # "buy" or "sell"
    amount: float
    price: float
    timestamp: str

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

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

# Wallet endpoints
@app.get("/wallets/hot")
async def get_hot_wallet(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM wallets WHERE user_id = %s AND type = 'hot'"
        cursor.execute(query, (user_id,))
        wallet = cursor.fetchone()
        cursor.close()
        conn.close()
        return wallet if wallet else {"message": "Hot wallet not found"}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error fetching hot wallet: {err}")

@app.get("/wallets/cold")
async def get_cold_wallet(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM wallets WHERE user_id = %s AND type = 'cold'"
        cursor.execute(query, (user_id,))
        wallet = cursor.fetchone()
        cursor.close()
        conn.close()
        return wallet if wallet else {"message": "Cold wallet not found"}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error fetching cold wallet: {err}")

# Trading endpoints
@app.post("/trade/buy")
async def buy_crypto(data: TradeData):
    try:
        # Fetch real-time price
        response = requests.get(f"{CRYPTO_API_URL}/simple/price?ids={data.crypto}&vs_currencies=usd")
        price_data = response.json()
        price = price_data.get(data.crypto, {}).get("usd")

        if not price:
            raise HTTPException(status_code=404, detail="Crypto not found")

        total_cost = price * data.amount

        # Deduct from hot wallet
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "UPDATE wallets SET balance = balance - %s WHERE user_id = %s AND type = 'hot'"
        cursor.execute(query, (total_cost, data.user_id))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Crypto purchased successfully", "crypto": data.crypto, "amount": data.amount, "price": price}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error buying crypto: {err}")

@app.post("/trade/sell")
async def sell_crypto(data: TradeData):
    try:
        # Fetch real-time price
        response = requests.get(f"{CRYPTO_API_URL}/simple/price?ids={data.crypto}&vs_currencies=usd")
        price_data = response.json()
        price = price_data.get(data.crypto, {}).get("usd")

        if not price:
            raise HTTPException(status_code=404, detail="Crypto not found")

        total_earnings = price * data.amount

        # Add to hot wallet
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "UPDATE wallets SET balance = balance + %s WHERE user_id = %s AND type = 'hot'"
        cursor.execute(query, (total_earnings, data.user_id))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Crypto sold successfully", "crypto": data.crypto, "amount": data.amount, "price": price}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error selling crypto: {err}")

# Portfolio endpoints
@app.get("/portfolio")
async def get_portfolio(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT crypto, amount FROM portfolio WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        portfolio = cursor.fetchall()
        cursor.close()
        conn.close()

        # Fetch real-time prices
        response = requests.get(f"{CRYPTO_API_URL}/simple/price?ids={','.join(TOP_10_CRYPTOS)}&vs_currencies=usd")
        prices = response.json()

        # Calculate portfolio value
        portfolio_value = []
        total_value = 0
        for asset in portfolio:
            price = prices.get(asset["crypto"], {}).get("usd", 0)
            value = price * asset["amount"]
            total_value += value
            portfolio_value.append({"crypto": asset["crypto"], "amount": asset["amount"], "value": value})

        return {"portfolio": portfolio_value, "total_value": total_value}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {err}")

@app.get("/portfolio/performance")
async def get_portfolio_performance(user_id: int):
    # Placeholder for historical performance data
    return {"message": "Performance data endpoint under construction"}

# Transaction history
@app.get("/transactions")
async def get_transactions(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM transactions WHERE user_id = %s ORDER BY timestamp DESC"
        cursor.execute(query, (user_id,))
        transactions = cursor.fetchall()
        cursor.close()
        conn.close()
        return transactions
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {err}")

@app.post("/transactions")
async def log_transaction(data: TransactionLog):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO transactions (user_id, crypto, action, amount, price, timestamp) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (data.user_id, data.crypto, data.action, data.amount, data.price, data.timestamp))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Transaction logged successfully"}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error logging transaction: {err}")

# Include routers
app.include_router(subscriptions_router)
app.include_router(fintto_chat_router, prefix="/api")
