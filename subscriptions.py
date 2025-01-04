from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import mysql.connector.pooling

router = APIRouter()

class Subscription(BaseModel):
    user_id: int
    plan: str

@router.post("/subscribe")
async def create_subscription(data: Subscription):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO subscriptions (user_id, plan, created_at)
        VALUES (%s, %s, NOW())
        """
        cursor.execute(query, (data.user_id, data.plan))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Suscripción creada exitosamente"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error al crear suscripción: {err}")

@router.get("/subscriptions/{user_id}")
async def get_subscriptions(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM subscriptions WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        subscriptions = cursor.fetchall()
        cursor.close()
        conn.close()
        return subscriptions
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error al obtener suscripciones: {err}")
