import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers.auth_routes import router as auth_router
from routers.trade_routes import router as trade_router
from routers.wallet_routes import router as wallet_router
from routers.subscription_routes import router as subscription_router
from routers.market_routes import router as market_router
from utils.db import init_db

# Load environment variables
load_dotenv()

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

# Database initialization on app startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "FINTT Backend is running with all integrations!"}

# Include modularized routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(trade_router, prefix="/trade", tags=["Trade"])
app.include_router(wallet_router, prefix="/wallets", tags=["Wallets"])
app.include_router(subscription_router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(market_router, prefix="/market", tags=["Market Data"])
