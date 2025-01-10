from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from utils.db import get_db_pool

router = APIRouter()

# Define a Pydantic model for the request body
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    try:
        db_pool = get_db_pool()  # Get the database pool
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query user by email
        cursor.execute("SELECT * FROM users WHERE email = %s", (request.email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or user["password"] != request.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"message": "Login successful", "user": {"id": user["id"], "email": user["email"]}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {e}")
