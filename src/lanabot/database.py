"""Database operations for LanaBot."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from supabase import Client, create_client

from .config import get_settings
from .models import Balance, Transaction, TransactionType

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for Supabase operations."""

    def __init__(self) -> None:
        """Initialize database manager."""
        settings = get_settings()
        self.client: Client = create_client(
            settings.supabase_url, settings.supabase_key
        )

    async def create_transaction(self, transaction: Transaction) -> Transaction:
        """Create a new transaction in the database."""
        try:
            logger.info(f"Creating transaction: {transaction}")
            logger.info(f"Transaction type: {transaction.transaction_type}, type: {type(transaction.transaction_type)}")
            
            # Handle both enum and string transaction types
            if hasattr(transaction.transaction_type, 'value'):
                transaction_type_value = transaction.transaction_type.value
            else:
                transaction_type_value = str(transaction.transaction_type)
            
            data = {
                "phone_number": transaction.phone_number,
                "transaction_type": transaction_type_value,
                "amount": float(transaction.amount),
                "description": transaction.description,
                "created_at": datetime.utcnow().isoformat(),
            }

            result = self.client.table("transactions").insert(data).execute()

            if result.data:
                created_transaction = result.data[0]
                return Transaction(
                    id=created_transaction["id"],
                    phone_number=created_transaction["phone_number"],
                    transaction_type=TransactionType(
                        created_transaction["transaction_type"]
                    ),
                    amount=Decimal(str(created_transaction["amount"])),
                    description=created_transaction["description"],
                    created_at=datetime.fromisoformat(
                        created_transaction["created_at"]
                    ),
                    updated_at=datetime.fromisoformat(
                        created_transaction["updated_at"]
                    )
                    if created_transaction.get("updated_at")
                    else None,
                )

            msg = "No data returned from transaction creation"
            raise ValueError(msg)

        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise

    async def get_balance(self, phone_number: str) -> Balance:
        """Get current balance for a phone number."""
        try:
            logger.info(f"Getting balance for phone_number: '{phone_number}'")
            
            # Get all transactions for this phone number
            result = (
                self.client.table("transactions")
                .select("*")
                .eq("phone_number", phone_number)
                .execute()
            )

            transactions = result.data
            logger.info(f"Found {len(transactions)} transactions for {phone_number}")
            
            if transactions:
                logger.info(f"Sample transaction: {transactions[0]}")
            else:
                # Check if there are ANY transactions in the table
                all_result = self.client.table("transactions").select("phone_number").execute()
                logger.info(f"All phone numbers in DB: {[t['phone_number'] for t in all_result.data]}")

            total_sales = Decimal("0")
            total_expenses = Decimal("0")
            last_updated = None

            for transaction in transactions:
                amount = Decimal(str(transaction["amount"]))
                if transaction["transaction_type"] == TransactionType.VENTA.value:
                    total_sales += amount
                else:
                    total_expenses += amount

                # Update last_updated with the most recent transaction
                transaction_date = datetime.fromisoformat(transaction["created_at"])
                if last_updated is None or transaction_date > last_updated:
                    last_updated = transaction_date

            # If no transactions, use current time
            if last_updated is None:
                from datetime import timezone
                last_updated = datetime.now(timezone.utc)

            current_balance = total_sales - total_expenses

            return Balance(
                phone_number=phone_number,
                current_balance=current_balance,
                total_sales=total_sales,
                total_expenses=total_expenses,
                last_updated=last_updated,
            )

        except Exception as e:
            logger.error(f"Error getting balance for {phone_number}: {e}")
            # Return empty balance if no transactions found
            return Balance(
                phone_number=phone_number,
                current_balance=Decimal("0"),
                total_sales=Decimal("0"),
                total_expenses=Decimal("0"),
                last_updated=datetime.utcnow(),
            )

    async def get_recent_transactions(
        self, phone_number: str, limit: int = 10
    ) -> list[Transaction]:
        """Get recent transactions for a phone number."""
        try:
            result = (
                self.client.table("transactions")
                .select("*")
                .eq("phone_number", phone_number)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            transactions = []
            for data in result.data:
                transaction = Transaction(
                    id=data["id"],
                    phone_number=data["phone_number"],
                    transaction_type=TransactionType(data["transaction_type"]),
                    amount=Decimal(str(data["amount"])),
                    description=data["description"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"])
                    if data.get("updated_at")
                    else None,
                )
                transactions.append(transaction)

            return transactions

        except Exception as e:
            logger.error(f"Error getting recent transactions for {phone_number}: {e}")
            return []

    async def check_low_balance_alert(self, phone_number: str) -> bool:
        """Check if balance is below alert threshold."""
        try:
            balance = await self.get_balance(phone_number)
            settings = get_settings()
            return balance.current_balance < Decimal(str(settings.minimum_balance_alert))
        except Exception as e:
            logger.error(f"Error checking low balance alert for {phone_number}: {e}")
            return False