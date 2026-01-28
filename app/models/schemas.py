from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============== Auth Schemas ==============
class UserCreate(BaseModel):
    """Schema for user registration."""
    email: str
    password: str
    username: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


# ============== Stock Schemas ==============
class StockSearchResult(BaseModel):
    """Schema for stock search results."""
    symbol: str
    name: str
    exchange: Optional[str] = None
    exchange_short_name: Optional[str] = None
    stock_type: Optional[str] = None


class PricePoint(BaseModel):
    """Schema for a single price data point."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceMultiples(BaseModel):
    """Schema for price multiple ratios."""
    pe_ratio: Optional[float] = Field(None, description="Price to Earnings Ratio")
    pb_ratio: Optional[float] = Field(None, description="Price to Book Ratio")
    ps_ratio: Optional[float] = Field(None, description="Price to Sales Ratio")
    ev_ebitda: Optional[float] = Field(None, description="Enterprise Value to EBITDA")


class NewsHeadline(BaseModel):
    """Schema for news headline."""
    title: str
    url: str
    published_date: str
    source: Optional[str] = None


class NewsSentiment(BaseModel):
    """Schema for news sentiment analysis."""
    overall_sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str  # "Bullish", "Bearish", "Neutral"
    top_headlines: list[NewsHeadline]
    analysis_summary: str


class AIValuationSummary(BaseModel):
    """Schema for AI-generated valuation summary."""
    summary: str
    recommendation: str  # "Undervalued", "Fairly Valued", "Overvalued"
    key_insights: list[str]


class StockDetail(BaseModel):
    """Schema for complete stock details."""
    symbol: str
    company_name: str
    current_price: float
    price_history: list[PricePoint]
    price_multiples: PriceMultiples
    news_sentiment: Optional[NewsSentiment] = None
    ai_valuation: Optional[AIValuationSummary] = None


# ============== Portfolio Schemas ==============
class PortfolioHoldingCreate(BaseModel):
    """Schema for adding a stock to portfolio."""
    symbol: str
    shares: int = Field(..., gt=0, description="Number of whole shares")
    purchase_price: float = Field(..., gt=0)


class PortfolioHoldingResponse(BaseModel):
    """Schema for portfolio holding response."""
    id: int
    symbol: str
    company_name: str
    shares: int
    purchase_price: float
    current_price: float
    total_value: float
    gain_loss: float
    gain_loss_percent: float
    purchased_at: datetime

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    """Schema for portfolio summary."""
    total_invested: float
    current_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    holdings: list[PortfolioHoldingResponse]
