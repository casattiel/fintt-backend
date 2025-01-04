from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Crear un router para fintto_chat
router = APIRouter()

# Modelo de datos para Fintto Chat
class ChatMessage(BaseModel):
    question: str

@router.post("/chat")
async def fintto_chat(data: ChatMessage):
    try:
        user_question = data.question.lower()

        # Lógica básica para respuestas automáticas
        if "bolsa" in user_question:
            response = "Para invertir en la bolsa, necesitas abrir una cuenta con un broker y elegir tus activos."
        elif "criptomonedas" in user_question:
            response = "Las criptomonedas son activos digitales que puedes adquirir en plataformas como Binance o Coinbase."
        elif "préstamo" in user_question or "loan" in user_question:
            response = "Para solicitar un préstamo, asegúrate de cumplir con los requisitos necesarios en tu cuenta de usuario."
        else:
            response = f"Fintto Chat dice: La respuesta a tu pregunta '{data.question}' será más detallada en el futuro."

        return {"question": data.question, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Fintto Chat: {str(e)}")
