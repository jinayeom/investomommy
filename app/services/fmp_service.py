import httpx
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import get_settings
from app.models.schemas import (
    StockSearchResult,
    PricePoint,
    PriceMultiples,
    NewsHeadline,
)

settings = get_settings()

FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"


class FMPService:
    """Service for interacting with Financial Modeling Prep API."""

    def __init__(self):
        self.api_key = settings.fmp_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_stocks(self, query: str, limit: int = 10) -> list[StockSearchResult]:
        """
        Search for stocks by ticker symbol or company name.
        
        Args:
            query: Search term (ticker or company name)
            limit: Maximum number of results to return
            
        Returns:
            List of matching stocks
        """
        url = f"{FMP_BASE_URL}/search"
        params = {
            "query": query,
            "limit": limit,
            "apikey": self.api_key,
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return [
            StockSearchResult(
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                exchange=item.get("exchangeFullName"),
                exchange_short_name=item.get("exchangeShortName"),
                stock_type=item.get("type"),
            )
            for item in data
        ]

    async def get_stock_quote(self, symbol: str) -> Optional[dict]:
        """
        Get current stock quote.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Stock quote data or None
        """
        url = f"{FMP_BASE_URL}/quote/{symbol}"
        params = {"apikey": self.api_key}

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return data[0] if data else None

    async def get_price_history(
        self, symbol: str, days: int = 30
    ) -> list[PricePoint]:
        """
        Get historical price data for the past N days.
        
        Args:
            symbol: Stock ticker symbol
            days: Number of days of history (default 30)
            
        Returns:
            List of price points
        """
        url = f"{FMP_BASE_URL}/historical-price-full/{symbol}"
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "apikey": self.api_key,
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        historical = data.get("historical", [])
        
        return [
            PricePoint(
                date=item["date"],
                open=item["open"],
                high=item["high"],
                low=item["low"],
                close=item["close"],
                volume=item["volume"],
            )
            for item in historical
        ]

    async def get_key_metrics(self, symbol: str) -> PriceMultiples:
        """
        Get key financial metrics (price multiples).
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Price multiples data
        """
        # Get ratios from key-metrics-ttm endpoint
        url = f"{FMP_BASE_URL}/key-metrics-ttm/{symbol}"
        params = {"apikey": self.api_key}

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return PriceMultiples()

        metrics = data[0]
        
        return PriceMultiples(
            pe_ratio=metrics.get("peRatioTTM"),
            pb_ratio=metrics.get("pbRatioTTM"),
            ps_ratio=metrics.get("priceToSalesRatioTTM"),
            ev_ebitda=metrics.get("enterpriseValueOverEBITDATTM"),
        )

    async def get_company_profile(self, symbol: str) -> Optional[dict]:
        """
        Get company profile information.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Company profile data or None
        """
        url = f"{FMP_BASE_URL}/profile/{symbol}"
        params = {"apikey": self.api_key}

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return data[0] if data else None

    async def get_stock_news(self, symbol: str, limit: int = 10) -> list[NewsHeadline]:
        """
        Get recent news for a stock.
        
        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of news items
            
        Returns:
            List of news headlines
        """
        url = f"{FMP_BASE_URL}/stock_news"
        params = {
            "tickers": symbol,
            "limit": limit,
            "apikey": self.api_key,
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return [
            NewsHeadline(
                title=item.get("title", ""),
                url=item.get("url", ""),
                published_date=item.get("publishedDate", ""),
                source=item.get("site"),
            )
            for item in data
        ]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
fmp_service = FMPService()
