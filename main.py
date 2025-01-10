import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils.db import init_db, get_db_pool
from routers.auth_routes import router as auth_router
from routers.trade_routes import router as trade_router
from routers.wallet_routes import router as wallet_router
from routers.subscription_routes import router as subscription_router
from routers.market_routes import router as market_router

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Global database pool
db_pool = None

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Startup event to initialize database."""
    global db_pool
    try:
        db_pool = init_db()
        print("Database connection pool initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        raise e

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event to close database connections."""
    global db_pool
    if db_pool:
        db_pool.close()
        print("Database connection pool closed.")

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
