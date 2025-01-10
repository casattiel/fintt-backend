from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, initialize_app
from routers.auth_routes import router as auth_router
from utils.db import init_db
import os

# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),  # Correct newline formatting
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
        })
        initialize_app(cred)
        print("✅ Firebase initialized successfully.")
    except Exception as e:
        print("❌ Error initializing Firebase:", str(e))
        raise

# Initialize Firebase on startup
initialize_firebase()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database connection pool
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("✅ Database initialized.")
    except Exception as e:
        print("❌ Error initializing database:", str(e))
        raise

@app.get("/")
async def root():
    return {"message": "FINTT Backend is running with Firebase initialized!"}

# Include authentication routes
app.include_router(auth_router, prefix="", tags=["Authentication"])
