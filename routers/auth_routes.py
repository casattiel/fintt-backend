from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from firebase_admin import auth
from utils.db import get_db_connection

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    confirm_password: str

@router.post("/login")
async def login_user(request: LoginRequest):
    try:
        # Verificar credenciales en Firebase
        user = auth.get_user_by_email(request.email)
        if user.email_verified:  # Ejemplo: Verificar si el usuario está verificado
            return {"message": "Login successful", "user": user.email}
        else:
            raise HTTPException(status_code=401, detail="Email not verified")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error during login: {e}")

@router.post("/register")
async def register_user(request: RegisterRequest):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    try:
        # Crear usuario en Firebase
        user = auth.create_user(email=request.email, password=request.password)
        return {"message": "User registered successfully", "user": user.email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during registration: {e}")
