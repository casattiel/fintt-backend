from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.kraken import execute_trade

router = APIRouter()

class TradeData(BaseModel):
    crypto_pair: str
    amount: float
    action: str  # "buy" or "sell"

@router.post("/")
async def trade(data: TradeData):
    try:
        result = execute_trade(data.crypto_pair, data.amount, data.action)
        return {"message": "Trade executed successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing trade: {e}")
