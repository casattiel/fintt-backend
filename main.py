from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from firebase_admin import credentials, initialize_app, auth
import mysql.connector
import os

# Load Environment Variables (Ensure these are correctly configured in your Render settings)
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n")  # Ensure correct formatting

# Firebase Initialization
def initialize_firebase():
    try:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": FIREBASE_PRIVATE_KEY,
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
        print(f"❌ Error initializing Firebase: {e}")
        raise e

# Database Initialization
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        print("✅ Database connection established.")
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        raise err

# FastAPI Initialization
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase and Database Initialization
@app.on_event("startup")
def startup_event():
    initialize_firebase()
    print("🔥 App Startup Completed")

# Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str

# Routes
@app.get("/")
async def root():
    return {"message": "FINTT Broker API is running!"}

@app.post("/login")
async def login_user(request: LoginRequest):
    try:
        # Simulate Login (Firebase doesn't allow password verification on backend)
        user = auth.get_user_by_email(request.email)
        return {
            "message": "Login successful",
            "user": {
                "email": user.email,
                "uid": user.uid,
                "email_verified": user.email_verified,
            },
        }
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found in Firebase.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during login: {str(e)}")

@app.post("/register")
async def register_user(request: RegisterRequest):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    try:
        # Create user in Firebase
        user = auth.create_user(
            email=request.email,
            password=request.password,
        )
        return {
            "message": "User registered successfully.",
            "user": {
                "email": user.email,
                "uid": user.uid,
            },
        }
    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already exists.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during registration: {str(e)}")

