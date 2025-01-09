import os
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import krakenex
import stripe
from subscriptions import router as subscriptions_router
from fintto_chat import router as fintto_chat_router

# Load environment variables
load_dotenv()

# Configuration of API Keys and Database
KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY", "SzQ41RAGaxOFOxiqs88aQis8eCmGPJ5VpoR1Vz2ypP8kksjYUVXcWCQ7")
KRAKEN_SECRET_KEY = os.getenv("KRAKEN_SECRET_KEY", "Zo6J3HnywhPUkrUtnhKKu3UdnABtOHeEIEvWrGyHkloHNz++8K2UYeg/rHbNSY0HqUe7fEPuSYJ7XSXstTzk/A==")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_51QfQbOCFuzFSWK4L7KMEakMZVSFM7dCq2FHekAzw9Dj5gjgjEu3lXMXlCX2VJvFWqEYCm8mVYr9e2GHLu1anUBhM00HeEKCAwW")
DB_HOST = os.getenv("DB_HOST", "fint-db.ctkokc288j85.us-east-2.rds.amazonaws.com")
DB_USER = os.getenv("DB_USER", "fint_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "JesusismyLord33!")
DB_NAME = os.getenv("DB_NAME", "fint_db")

# Initialize Kraken and Stripe APIs
kraken_api = krakenex.API()
kraken_api.key = KRAKEN_API_KEY
kraken_api.secret = KRAKEN_SECRET_KEY
stripe.api_key = STRIPE_SECRET_KEY

# Initialize FastAPI
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pooling
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
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
    return {"message": "FINTT Backend is running with Kraken and Stripe integrations!"}

# Utility function to hash passwords
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Data models
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

# User registration endpoint
@app.post("/register")
async def register(data: RegisterData):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(data.password)
        query = "INSERT INTO users (name, email, password, country) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (data.name, data.email, hashed_password, data.country))
        conn.commit()
        return {"message": "User registered successfully"}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error registering user: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# User login endpoint
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

        return {"message": "Login successful", "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error during login: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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

# Subscription upgrade endpoint
@app.post("/subscriptions/upgrade")
async def upgrade_subscription(data: SubscriptionUpgrade):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "UPDATE users SET subscription_plan = %s WHERE id = %s"
        cursor.execute(query, (data.new_plan, data.user_id))
        conn.commit()
        return {"message": "Subscription upgraded successfully", "new_plan": data.new_plan}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error upgrading subscription: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Stripe payment session endpoint
@app.post("/api/stripe/create-checkout-session")
async def create_checkout_session(plan_id: str):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url="http://localhost:5173/success",
            cancel_url="http://localhost:5173/cancel",
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Stripe checkout session: {e}")

# Include additional routers
app.include_router(subscriptions_router)
app.include_router(fintto_chat_router, prefix="/api")
