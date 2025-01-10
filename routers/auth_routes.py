from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.db import db_pool
from utils.hashing import hash_password

router = APIRouter()

class RegisterData(BaseModel):
    name: str
    email: str
    password: str
    country: str

class LoginData(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(data: RegisterData):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(data.password)
        query = "INSERT INTO users (name, email, password, country) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (data.name, data.email, hashed_password, data.country))
        conn.commit()
        return {"message": "User registered successfully"}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error registering user: {err}")
    finally:
        cursor.close()
        conn.close()

@router.post("/login")
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
        return {"message": "Login successful", "user": user}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error during login: {err}")
    finally:
        cursor.close()
        conn.close()
