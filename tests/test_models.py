"""Tests for Pydantic models."""

from decimal import Decimal
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.lanabot.models import (
    Balance,
    ProcessedTransaction,
    Transaction,
    TransactionType,
    WhatsAppMessage,
)


def test_transaction_model():
    """Test Transaction model validation."""
    transaction = Transaction(
        phone_number="1234567890",
        transaction_type=TransactionType.VENTA,
        amount=Decimal("150.50"),
        description="3 coca colas",
    )
    
    assert transaction.phone_number == "1234567890"
    assert transaction.transaction_type == TransactionType.VENTA
    assert transaction.amount == Decimal("150.50")
    assert transaction.description == "3 coca colas"


def test_transaction_model_validation_errors():
    """Test Transaction model validation errors."""
    # Test negative amount
    with pytest.raises(ValidationError):
        Transaction(
            phone_number="1234567890",
            transaction_type=TransactionType.VENTA,
            amount=Decimal("-10"),
            description="invalid transaction",
        )
    
    # Test empty description
    with pytest.raises(ValidationError):
        Transaction(
            phone_number="1234567890",
            transaction_type=TransactionType.VENTA,
            amount=Decimal("10"),
            description="",
        )


def test_processed_transaction_model():
    """Test ProcessedTransaction model."""
    processed = ProcessedTransaction(
        transaction_type=TransactionType.GASTO,
        amount=Decimal("75.25"),
        description="mercancía",
        confidence=0.95,
    )
    
    assert processed.transaction_type == TransactionType.GASTO
    assert processed.amount == Decimal("75.25")
    assert processed.description == "mercancía"
    assert processed.confidence == 0.95


def test_balance_model():
    """Test Balance model."""
    balance = Balance(
        phone_number="1234567890",
        current_balance=Decimal("1000.00"),
        total_sales=Decimal("1500.00"),
        total_expenses=Decimal("500.00"),
        last_updated=datetime.now(),
    )
    
    assert balance.phone_number == "1234567890"
    assert balance.current_balance == Decimal("1000.00")
    assert balance.total_sales == Decimal("1500.00")
    assert balance.total_expenses == Decimal("500.00")


def test_whatsapp_message_model():
    """Test WhatsAppMessage model."""
    message = WhatsAppMessage(
        message_id="msg123",
        from_number="1234567890",
        message_type="text",
        content="Vendí 5 refrescos",
        timestamp=datetime.now(),
    )
    
    assert message.message_id == "msg123"
    assert message.from_number == "1234567890"
    assert message.message_type == "text"
    assert message.content == "Vendí 5 refrescos"
    assert message.audio_url is None