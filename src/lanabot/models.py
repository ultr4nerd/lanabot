"""Data models for LanaBot."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    VENTA = "venta"
    GASTO = "gasto"


class Transaction(BaseModel):
    """Transaction model."""

    id: Optional[int] = None
    phone_number: str = Field(..., description="WhatsApp phone number")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    description: str = Field(..., min_length=1, description="Transaction description")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class WhatsAppMessage(BaseModel):
    """WhatsApp message model."""

    message_id: str = Field(..., description="WhatsApp message ID")
    from_number: str = Field(..., description="Sender phone number")
    message_type: str = Field(..., description="Message type (text, audio, etc.)")
    content: Optional[str] = Field(None, description="Text content")
    audio_url: Optional[str] = Field(None, description="Audio file URL")
    timestamp: datetime = Field(..., description="Message timestamp")


class ProcessedTransaction(BaseModel):
    """Processed transaction from AI analysis."""

    transaction_type: TransactionType = Field(..., description="Type of transaction")
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    description: str = Field(..., min_length=1, description="Transaction description")
    confidence: float = Field(..., ge=0, le=1, description="AI confidence score")


class Balance(BaseModel):
    """Account balance model."""

    phone_number: str = Field(..., description="WhatsApp phone number")
    current_balance: Decimal = Field(..., description="Current balance")
    total_sales: Decimal = Field(default=0, description="Total sales")
    total_expenses: Decimal = Field(default=0, description="Total expenses")
    last_updated: datetime = Field(..., description="Last update timestamp")


class WhatsAppWebhookEntry(BaseModel):
    """WhatsApp webhook entry model."""

    id: str
    changes: list[dict]


class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook payload model."""

    object: str
    entry: list[WhatsAppWebhookEntry]