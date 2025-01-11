from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError, EmailAlreadyExistsError
from utils.db import get_db_connection

router = APIRouter()

# Request models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str


@router.post("/login")
async def login_user(request: LoginRequest):
    """
    Log in a user by verifying their existence in Firebase. Note that password validation must be handled in the frontend.
    """
    try:
        # Fetch user by email
        user = auth.get_user_by_email(request.email)

        # Simulate successful login
        # Firebase Admin SDK does not handle password verification; use Firebase Auth SDK on the client-side.
        return {
            "message": "Login successful",
            "user": {
                "email": user.email,
                "uid": user.uid,
                "email_verified": user.email_verified,
            },
        }
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")


@router.post("/register")
async def register_user(request: RegisterRequest):
    """
    Register a new user in Firebase.
    """
    # Check password confirmation
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    try:
        # Create user in Firebase
        user = auth.create_user(
            email=request.email,
            password=request.password
        )
        return {
            "message": "User registered successfully",
            "user": {
                "email": user.email,
                "uid": user.uid,
            },
        }
    except EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during registration: {str(e)}")
