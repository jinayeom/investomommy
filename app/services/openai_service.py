from openai import AsyncOpenAI
from typing import Optional
import json

from app.core.config import get_settings
from app.models.schemas import (
    NewsHeadline,
    NewsSentiment,
    PriceMultiples,
    AIValuationSummary,
)

settings = get_settings()


class OpenAIService:
    """Service for OpenAI LLM-powered analysis."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o"

    async def analyze_news_sentiment(
        self, symbol: str, company_name: str, headlines: list[NewsHeadline]
    ) -> NewsSentiment:
        """
        Analyze news sentiment using OpenAI.
        
        Args:
            symbol: Stock ticker symbol
            company_name: Company name
            headlines: List of news headlines to analyze
            
        Returns:
            News sentiment analysis
        """
        if not headlines:
            return NewsSentiment(
                overall_sentiment_score=0.0,
                sentiment_label="Neutral",
                top_headlines=[],
                analysis_summary="No recent news available for analysis.",
            )

        # Prepare headlines for analysis
        headlines_text = "\n".join(
            [f"- {h.title} (Source: {h.source}, Date: {h.published_date})" 
             for h in headlines[:10]]
        )

        prompt = f"""Analyze the following news headlines for {company_name} ({symbol}) and provide:
1. An overall sentiment score from -1.0 (very bearish) to 1.0 (very bullish)
2. A sentiment label: "Bullish", "Bearish", or "Neutral"
3. A brief summary of the overall news sentiment (2-3 sentences)

Headlines:
{headlines_text}

Respond in JSON format:
{{
    "sentiment_score": <float>,
    "sentiment_label": "<string>",
    "analysis_summary": "<string>"
}}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst specializing in news sentiment analysis. Provide objective, data-driven analysis.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        result = json.loads(response.choices[0].message.content)

        return NewsSentiment(
            overall_sentiment_score=float(result.get("sentiment_score", 0.0)),
            sentiment_label=result.get("sentiment_label", "Neutral"),
            top_headlines=headlines[:5],  # Return top 5 headlines
            analysis_summary=result.get("analysis_summary", ""),
        )

    async def generate_valuation_summary(
        self,
        symbol: str,
        company_name: str,
        current_price: float,
        multiples: PriceMultiples,
    ) -> AIValuationSummary:
        """
        Generate an AI-powered valuation summary based on price multiples.
        
        Args:
            symbol: Stock ticker symbol
            company_name: Company name
            current_price: Current stock price
            multiples: Price multiple ratios
            
        Returns:
            AI valuation summary
        """
        prompt = f"""As a financial analyst, provide a valuation summary for {company_name} ({symbol}).

Current Price: ${current_price:.2f}

Price Multiples:
- P/E Ratio: {multiples.pe_ratio if multiples.pe_ratio else 'N/A'}
- P/B Ratio: {multiples.pb_ratio if multiples.pb_ratio else 'N/A'}
- P/S Ratio: {multiples.ps_ratio if multiples.ps_ratio else 'N/A'}
- EV/EBITDA: {multiples.ev_ebitda if multiples.ev_ebitda else 'N/A'}

Based on these multiples, provide:
1. A comprehensive valuation summary (3-4 sentences)
2. A recommendation: "Undervalued", "Fairly Valued", or "Overvalued"
3. 3-5 key insights about the valuation

Consider typical market averages:
- Average S&P 500 P/E: ~20-25
- Average P/B: ~3-4
- Average P/S: ~2-3
- Average EV/EBITDA: ~12-15

Respond in JSON format:
{{
    "summary": "<string>",
    "recommendation": "<string>",
    "key_insights": ["<string>", "<string>", ...]
}}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional equity research analyst. Provide balanced, educational analysis. Always include appropriate disclaimers that this is not financial advice.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )

        result = json.loads(response.choices[0].message.content)

        return AIValuationSummary(
            summary=result.get("summary", ""),
            recommendation=result.get("recommendation", "Fairly Valued"),
            key_insights=result.get("key_insights", []),
        )


# Singleton instance
openai_service = OpenAIService()
