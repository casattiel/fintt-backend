from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ChatMessage(BaseModel):
    message: str

@router.post("/chat")
async def fintto_chat(message: ChatMessage):
    user_message = message.message.lower()

    # Respuesta simulada - Aquí puedes integrar IA más adelante
    if "bolsa de valores" in user_message:
        return {"response": "Para invertir en la bolsa de valores, necesitas abrir una cuenta con un broker autorizado."}
    elif "criptomonedas" in user_message:
        return {"response": "Las criptomonedas son activos digitales que puedes comprar mediante plataformas como Binance o Coinbase."}
    else:
        return {"response": "Esto es una respuesta generada por el asistente Fintto."}
