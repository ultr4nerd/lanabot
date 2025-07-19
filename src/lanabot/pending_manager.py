"""Manager for pending transactions awaiting user confirmation."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from .models import PendingTransaction, ProcessedTransaction, TransactionType

logger = logging.getLogger(__name__)


class PendingTransactionManager:
    """Manages pending transactions in memory."""
    
    def __init__(self):
        """Initialize the pending transaction manager."""
        self._pending: Dict[str, PendingTransaction] = {}
    
    def add_pending(self, phone_number: str, processed_transaction: ProcessedTransaction, transaction_id: int = None) -> None:
        """Add a pending transaction for confirmation."""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)  # 2 minute timeout
        
        pending = PendingTransaction(
            phone_number=phone_number,
            transaction_type=processed_transaction.transaction_type,
            amount=processed_transaction.amount,
            description=processed_transaction.description,
            suggested_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            transaction_id=transaction_id
        )
        
        self._pending[phone_number] = pending
        logger.info(f"Added pending transaction for {phone_number}: {pending}")
    
    def get_pending(self, phone_number: str) -> Optional[PendingTransaction]:
        """Get pending transaction for a phone number."""
        pending = self._pending.get(phone_number)
        
        if pending and datetime.now(timezone.utc) > pending.expires_at:
            # Transaction expired, remove it
            del self._pending[phone_number]
            logger.info(f"Expired pending transaction for {phone_number}")
            return None
            
        return pending
    
    def remove_pending(self, phone_number: str) -> Optional[PendingTransaction]:
        """Remove and return pending transaction."""
        return self._pending.pop(phone_number, None)
    
    def has_pending(self, phone_number: str) -> bool:
        """Check if user has a pending transaction."""
        return self.get_pending(phone_number) is not None
    
    def cleanup_expired(self) -> None:
        """Remove all expired pending transactions."""
        now = datetime.now(timezone.utc)
        expired_phones = [
            phone for phone, pending in self._pending.items()
            if now > pending.expires_at
        ]
        
        for phone in expired_phones:
            del self._pending[phone]
            logger.info(f"Cleaned up expired pending transaction for {phone}")


# Global instance
pending_manager = PendingTransactionManager()