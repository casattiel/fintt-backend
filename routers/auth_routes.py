from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from utils.db import get_db_connection
from bcrypt import hashpw, gensalt
import mysql.connector

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    confirm_password: str

@router.post("/register")
async def register_user(request: RegisterRequest):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if user already exists
        cursor.execute("SELECT email FROM users WHERE email = %s", (request.email,))
        existing_user = cursor.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Hash the password
        hashed_password = hashpw(request.password.encode("utf-8"), gensalt()).decode("utf-8")

        # Insert new user
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (request.email, hashed_password))
        conn.commit()
        return {"message": "User registered successfully."}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
