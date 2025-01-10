from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter()

# Define data models
class MarketNews(BaseModel):
    title: str
    description: str
    url: str

class MarketTrend(BaseModel):
    trend: str
    percentage_change: float

# Example: Fetch market news
@router.get("/news", response_model=List[MarketNews])
async def get_market_news():
    try:
        # Dummy data for market news
        market_news = [
            MarketNews(
                title="Crypto Prices Surge",
                description="Bitcoin and Ethereum prices see a massive surge.",
                url="https://example.com/news1"
            ),
            MarketNews(
                title="Market Crash Expected",
                description="Analysts predict a potential market crash next week.",
                url="https://example.com/news2"
            ),
        ]
        return market_news
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market news: {e}")

# Example: Fetch market trends
@router.get("/trends", response_model=List[MarketTrend])
async def get_market_trends():
    try:
        # Dummy data for market trends
        market_trends = [
            MarketTrend(trend="Bitcoin Uptrend", percentage_change=5.6),
            MarketTrend(trend="Ethereum Downtrend", percentage_change=-3.2),
        ]
        return market_trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market trends: {e}")
