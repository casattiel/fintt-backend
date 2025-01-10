import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils.db import init_db
from routers.auth_routes import router as auth_router
from routers.trade_routes import router as trade_router
from routers.wallet_routes import router as wallet_router
from routers.subscription_routes import router as subscription_router
from routers.market_routes import router as market_router

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Startup event to initialize database."""
    print("Starting up...")
    try:
        init_db()
        print("Database connection initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        raise e

@app.get("/")
async def root():
    """Root endpoint to verify the backend is running."""
    return {"message": "FINTT Backend is running!"}

# Include routers with adjusted prefixes
app.include_router(auth_router, prefix="", tags=["Authentication"])  # No `/auth` prefix
app.include_router(trade_router, prefix="/trade", tags=["Trade"])
app.include_router(wallet_router, prefix="/wallets", tags=["Wallets"])
app.include_router(subscription_router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(market_router, prefix="/market", tags=["Market"])
