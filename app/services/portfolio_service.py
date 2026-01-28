from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.database import User, PortfolioHolding
from app.models.schemas import (
    PortfolioHoldingCreate,
    PortfolioHoldingResponse,
    PortfolioSummary,
)
from app.services.fmp_service import fmp_service


class PortfolioService:
    """Service for managing user portfolios."""

    async def add_holding(
        self,
        db: Session,
        user: User,
        holding_data: PortfolioHoldingCreate,
    ) -> PortfolioHolding:
        """
        Add a new holding to user's portfolio.
        
        Args:
            db: Database session
            user: Current user
            holding_data: Holding data (symbol, shares, purchase_price)
            
        Returns:
            Created portfolio holding
        """
        # Get company info from FMP
        profile = await fmp_service.get_company_profile(holding_data.symbol)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock symbol '{holding_data.symbol}' not found",
            )

        company_name = profile.get("companyName", holding_data.symbol)

        # Create holding
        holding = PortfolioHolding(
            user_id=user.id,
            symbol=holding_data.symbol.upper(),
            company_name=company_name,
            shares=holding_data.shares,
            purchase_price=holding_data.purchase_price,
        )

        db.add(holding)
        db.commit()
        db.refresh(holding)

        return holding

    async def get_holdings(self, db: Session, user: User) -> list[PortfolioHoldingResponse]:
        """
        Get all holdings for a user with current prices.
        
        Args:
            db: Database session
            user: Current user
            
        Returns:
            List of portfolio holdings with current values
        """
        holdings = db.query(PortfolioHolding).filter(
            PortfolioHolding.user_id == user.id
        ).all()

        result = []
        for holding in holdings:
            # Get current price
            quote = await fmp_service.get_stock_quote(holding.symbol)
            current_price = quote.get("price", holding.purchase_price) if quote else holding.purchase_price

            total_value = current_price * holding.shares
            invested = holding.purchase_price * holding.shares
            gain_loss = total_value - invested
            gain_loss_percent = (gain_loss / invested * 100) if invested > 0 else 0

            result.append(
                PortfolioHoldingResponse(
                    id=holding.id,
                    symbol=holding.symbol,
                    company_name=holding.company_name,
                    shares=holding.shares,
                    purchase_price=holding.purchase_price,
                    current_price=current_price,
                    total_value=total_value,
                    gain_loss=gain_loss,
                    gain_loss_percent=gain_loss_percent,
                    purchased_at=holding.purchased_at,
                )
            )

        return result

    async def get_portfolio_summary(self, db: Session, user: User) -> PortfolioSummary:
        """
        Get portfolio summary with totals.
        
        Args:
            db: Database session
            user: Current user
            
        Returns:
            Portfolio summary with all holdings
        """
        holdings = await self.get_holdings(db, user)

        total_invested = sum(h.purchase_price * h.shares for h in holdings)
        current_value = sum(h.total_value for h in holdings)
        total_gain_loss = current_value - total_invested
        total_gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0

        return PortfolioSummary(
            total_invested=total_invested,
            current_value=current_value,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=total_gain_loss_percent,
            holdings=holdings,
        )

    def remove_holding(self, db: Session, user: User, holding_id: int) -> bool:
        """
        Remove a holding from user's portfolio.
        
        Args:
            db: Database session
            user: Current user
            holding_id: ID of the holding to remove
            
        Returns:
            True if removed successfully
        """
        holding = db.query(PortfolioHolding).filter(
            PortfolioHolding.id == holding_id,
            PortfolioHolding.user_id == user.id,
        ).first()

        if not holding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holding not found",
            )

        db.delete(holding)
        db.commit()

        return True

    def update_holding(
        self,
        db: Session,
        user: User,
        holding_id: int,
        shares: int,
    ) -> PortfolioHolding:
        """
        Update the number of shares in a holding.
        
        Args:
            db: Database session
            user: Current user
            holding_id: ID of the holding to update
            shares: New number of shares
            
        Returns:
            Updated portfolio holding
        """
        holding = db.query(PortfolioHolding).filter(
            PortfolioHolding.id == holding_id,
            PortfolioHolding.user_id == user.id,
        ).first()

        if not holding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holding not found",
            )

        if shares <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shares must be greater than 0",
            )

        holding.shares = shares
        db.commit()
        db.refresh(holding)

        return holding


# Singleton instance
portfolio_service = PortfolioService()
