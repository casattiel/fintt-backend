from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from firebase_admin import auth, exceptions

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
    Simulates login by checking if a user exists in Firebase.
    Note: Password validation is handled client-side using Firebase Authentication SDK.
    """
    try:
        # Check if user exists in Firebase
        user = auth.get_user_by_email(request.email)

        # Return user info (password validation happens on the frontend)
        return {
            "message": "Login successful",
            "user": {
                "email": user.email,
                "uid": user.uid,
                "email_verified": user.email_verified,
            },
        }
    except exceptions.NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")


@router.post("/register")
async def register_user(request: RegisterRequest):
    """
    Registers a user in Firebase and returns their info.
    """
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        # Create user in Firebase
        user = auth.create_user(
            email=request.email,
            password=request.password,
        )
        return {
            "message": "User registered successfully",
            "user": {
                "email": user.email,
                "uid": user.uid,
            },
        }
    except exceptions.AlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during registration: {str(e)}")
