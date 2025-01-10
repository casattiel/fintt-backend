from fastapi import APIRouter, HTTPException
from utils.db import db_pool

router = APIRouter()

@router.get("/{user_id}")
async def get_wallets(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM wallets WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        wallets = cursor.fetchall()
        return {"wallets": wallets}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error fetching wallets: {err}")
    finally:
        cursor.close()
        conn.close()
