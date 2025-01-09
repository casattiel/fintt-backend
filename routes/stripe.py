import os
import stripe
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()  # Cargar las variables de entorno si usas un archivo .env

# Claves de Stripe
STRIPE_SECRET_KEY = "sk_test_51QfQbOCFuzFSWK4L7KMEakMZVSFM7dCq2FHekAzw9Dj5gjgjEu3lXMXlCX2VJvFWqEYCm8mVYr9e2GHLu1anUBhM00HeEKCAwW"
stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter()

# Endpoint para crear la sesión de pago
@router.post("/create-checkout-session")
async def create_checkout_session(plan_id: str):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url="http://localhost:5173/success",  # Cambia a tu URL en producción
            cancel_url="http://localhost:5173/cancel",  # Cambia a tu URL en producción
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
