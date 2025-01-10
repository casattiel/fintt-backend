from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.db import db_pool
import bcrypt

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database connection pool is not initialized.")
    
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, password FROM users WHERE email = %s"
        cursor.execute(query, (request.email,))
        user = cursor.fetchone()
        
        if not user or not bcrypt.checkpw(request.password.encode(), user["password"].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        
        cursor.close()
        conn.close()
        
        return {"message": "Login successful", "user": {"id": user["id"]}}
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail=f"Error during login: {e}")
