from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai

openai.api_key = "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"

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/api/chatbot")
async def chatbot(request: ChatRequest):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Asesor financiero: {request.message}",
            max_tokens=150,
            temperature=0.7
        )
        return {"response": response.choices[0].text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")
