from fastapi import APIRouter, HTTPException, Depends
from utils.db import db_pool
from pydantic import BaseModel
import bcrypt

router = APIRouter()

class LoginData(BaseModel):
    email: str
    password: str

@router.post("/login", tags=["Authentication"])
async def login(data: LoginData):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (data.email,))
        user = cursor.fetchone()

        if not user or not bcrypt.checkpw(data.password.encode("utf-8"), user["password"].encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"user": {"id": user["id"], "email": user["email"], "name": user["name"]}}

    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error during login: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
