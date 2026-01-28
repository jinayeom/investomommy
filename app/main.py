from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.models.database import create_tables
from app.api.routes import page_router, auth_router, dashboard_router, portfolio_router
from app.services.fmp_service import fmp_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("Starting InvestoMommy API...")
    create_tables()
    print("Database tables created.")
    
    yield
    
    # Shutdown
    print("Shutting down InvestoMommy API...")
    await fmp_service.close()
    print("Cleanup complete.")


# Create FastAPI application
app = FastAPI(
    title="InvestoMommy API",
    description="""
    InvestoMommy - Your Personal Investment Companion
    
    ## Features
    
    * **Stock Search**: Search stocks by ticker symbol or company name
    * **Price Analysis**: View 30-day price charts and key price multiples
    * **AI Insights**: Get AI-powered news sentiment and valuation analysis
    * **Virtual Portfolio**: Track your paper trading investments
    
    ## Authentication
    
    Most endpoints require JWT authentication. 
    1. Sign up at `/auth/signup`
    2. Login at `/auth/login` to receive your access token
    3. Include the token in the Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(page_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(portfolio_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "app": settings.app_name}
