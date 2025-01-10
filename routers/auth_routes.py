from fastapi import APIRouter, HTTPException
from utils.db import get_db_pool

router = APIRouter()

@router.post("/login")
async def login(email: str, password: str):
    try:
        db_pool = get_db_pool()  # Get the database pool
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or user["password"] != password:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"message": "Login successful", "user": user}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {e}")
