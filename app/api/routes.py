from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.config import get_settings
from app.models.database import get_db, User
from app.models.schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    StockSearchResult,
    StockDetail,
    PortfolioHoldingCreate,
    PortfolioHoldingResponse,
    PortfolioSummary,
)
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from app.services.fmp_service import fmp_service
from app.services.openai_service import openai_service
from app.services.portfolio_service import portfolio_service

settings = get_settings()

# ============== Page Routes ==============
page_router = APIRouter(tags=["Pages"])


@page_router.get("/")
async def landing_page():
    """
    Landing page endpoint.
    Returns information about the InvestoMommy app.
    """
    return {
        "app": "InvestoMommy",
        "message": "Welcome to InvestoMommy - Your Personal Investment Companion!",
        "version": "1.0.0",
        "features": [
            "Stock search by ticker or company name",
            "Real-time price charts",
            "AI-powered news sentiment analysis",
            "Price multiple valuations",
            "Virtual portfolio tracking",
        ],
        "endpoints": {
            "landing": "/",
            "auth": "/auth",
            "dashboard": "/dashboard",
            "docs": "/docs",
        },
    }


# ============== Auth Routes ==============
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.get("")
async def auth_page():
    """
    Auth page endpoint.
    Returns authentication options.
    """
    return {
        "page": "Authentication",
        "message": "Login or Sign Up to access InvestoMommy",
        "options": {
            "login": "/auth/login",
            "signup": "/auth/signup",
        },
    }


@auth_router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **email**: User's email address
    - **username**: Unique username
    - **password**: User's password
    """
    user = create_user(db, user_data)
    return user


@auth_router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login and receive JWT access token.
    
    - **username**: User's email address (OAuth2 spec uses 'username' field)
    - **password**: User's password
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    
    return Token(access_token=access_token)


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    """
    return current_user


# ============== Dashboard/Stock Routes ==============
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("")
async def dashboard_home(current_user: User = Depends(get_current_user)):
    """
    Dashboard home page.
    Requires authentication.
    """
    return {
        "page": "Dashboard",
        "user": current_user.username,
        "message": f"Welcome back, {current_user.username}!",
        "actions": {
            "search_stocks": "/dashboard/stocks/search?query=<ticker_or_name>",
            "get_stock_details": "/dashboard/stocks/{symbol}",
            "view_portfolio": "/dashboard/portfolio",
        },
    }


@dashboard_router.get("/stocks/search", response_model=list[StockSearchResult])
async def search_stocks(
    query: str = Query(..., min_length=1, description="Stock ticker or company name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    current_user: User = Depends(get_current_user),
):
    """
    Search for stocks by ticker symbol or company name.
    
    Uses FMP API to find matching stocks.
    
    - **query**: Search term (e.g., "AAPL" or "Apple")
    - **limit**: Maximum number of results (default: 10)
    """
    results = await fmp_service.search_stocks(query, limit)
    return results


@dashboard_router.get("/stocks/{symbol}", response_model=StockDetail)
async def get_stock_details(
    symbol: str,
    include_ai_analysis: bool = Query(True, description="Include AI sentiment and valuation analysis"),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive stock details including:
    
    - Price chart for the past 30 days
    - Price multiples (P/E, P/B, P/S, EV/EBITDA)
    - News sentiment analysis (AI-powered)
    - AI valuation summary
    
    - **symbol**: Stock ticker symbol (e.g., "AAPL")
    - **include_ai_analysis**: Whether to include AI analysis (default: True)
    """
    symbol = symbol.upper()
    
    # Get company profile
    profile = await fmp_service.get_company_profile(symbol)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{symbol}' not found",
        )
    
    # Get current quote
    quote = await fmp_service.get_stock_quote(symbol)
    current_price = quote.get("price", 0) if quote else 0
    
    # Get price history (30 days)
    price_history = await fmp_service.get_price_history(symbol, days=30)
    
    # Get price multiples
    multiples = await fmp_service.get_key_metrics(symbol)
    
    # Initialize optional AI analysis
    news_sentiment = None
    ai_valuation = None
    
    if include_ai_analysis:
        # Get news and analyze sentiment
        news = await fmp_service.get_stock_news(symbol, limit=10)
        news_sentiment = await openai_service.analyze_news_sentiment(
            symbol=symbol,
            company_name=profile.get("companyName", symbol),
            headlines=news,
        )
        
        # Generate AI valuation summary
        ai_valuation = await openai_service.generate_valuation_summary(
            symbol=symbol,
            company_name=profile.get("companyName", symbol),
            current_price=current_price,
            multiples=multiples,
        )
    
    return StockDetail(
        symbol=symbol,
        company_name=profile.get("companyName", symbol),
        current_price=current_price,
        price_history=price_history,
        price_multiples=multiples,
        news_sentiment=news_sentiment,
        ai_valuation=ai_valuation,
    )


# ============== Portfolio Routes ==============
portfolio_router = APIRouter(prefix="/dashboard/portfolio", tags=["Portfolio"])


@portfolio_router.get("", response_model=PortfolioSummary)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's portfolio summary with all holdings.
    
    Returns:
    - Total invested amount
    - Current portfolio value
    - Total gain/loss
    - All individual holdings with current prices
    """
    return await portfolio_service.get_portfolio_summary(db, current_user)


@portfolio_router.post("/holdings", response_model=PortfolioHoldingResponse, status_code=status.HTTP_201_CREATED)
async def add_holding(
    holding_data: PortfolioHoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a new stock holding to portfolio.
    
    - **symbol**: Stock ticker symbol
    - **shares**: Number of whole shares to "buy"
    - **purchase_price**: Price per share at purchase
    """
    holding = await portfolio_service.add_holding(db, current_user, holding_data)
    
    # Get current price for response
    quote = await fmp_service.get_stock_quote(holding.symbol)
    current_price = quote.get("price", holding.purchase_price) if quote else holding.purchase_price
    
    total_value = current_price * holding.shares
    invested = holding.purchase_price * holding.shares
    gain_loss = total_value - invested
    
    return PortfolioHoldingResponse(
        id=holding.id,
        symbol=holding.symbol,
        company_name=holding.company_name,
        shares=holding.shares,
        purchase_price=holding.purchase_price,
        current_price=current_price,
        total_value=total_value,
        gain_loss=gain_loss,
        gain_loss_percent=(gain_loss / invested * 100) if invested > 0 else 0,
        purchased_at=holding.purchased_at,
    )


@portfolio_router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_holding(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a holding from portfolio (sell all shares).
    
    - **holding_id**: ID of the holding to remove
    """
    portfolio_service.remove_holding(db, current_user, holding_id)
    return None


@portfolio_router.patch("/holdings/{holding_id}")
async def update_holding(
    holding_id: int,
    shares: int = Query(..., gt=0, description="New number of shares"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the number of shares in a holding.
    
    - **holding_id**: ID of the holding to update
    - **shares**: New number of whole shares
    """
    holding = portfolio_service.update_holding(db, current_user, holding_id, shares)
    
    # Get current price for response
    quote = await fmp_service.get_stock_quote(holding.symbol)
    current_price = quote.get("price", holding.purchase_price) if quote else holding.purchase_price
    
    total_value = current_price * holding.shares
    invested = holding.purchase_price * holding.shares
    gain_loss = total_value - invested
    
    return PortfolioHoldingResponse(
        id=holding.id,
        symbol=holding.symbol,
        company_name=holding.company_name,
        shares=holding.shares,
        purchase_price=holding.purchase_price,
        current_price=current_price,
        total_value=total_value,
        gain_loss=gain_loss,
        gain_loss_percent=(gain_loss / invested * 100) if invested > 0 else 0,
        purchased_at=holding.purchased_at,
    )
