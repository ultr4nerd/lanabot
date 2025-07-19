"""Data models for LanaBot."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    VENTA = "venta"
    GASTO = "gasto"
    AJUSTE_CAJA = "ajuste"


class Transaction(BaseModel):
    """Transaction model."""

    id: int | None = None
    phone_number: str = Field(..., description="WhatsApp phone number")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    amount: Decimal = Field(..., description="Transaction amount (can be negative for cash withdrawals)")
    description: str = Field(..., min_length=1, description="Transaction description")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class WhatsAppMessage(BaseModel):
    """WhatsApp message model."""

    message_id: str = Field(..., description="WhatsApp message ID")
    from_number: str = Field(..., description="Sender phone number")
    message_type: str = Field(..., description="Message type (text, audio, image)")
    content: str | None = Field(None, description="Text content")
    audio_url: str | None = Field(None, description="Audio file URL")
    image_url: str | None = Field(None, description="Image file URL")
    timestamp: datetime = Field(..., description="Message timestamp")


class ProcessedTransaction(BaseModel):
    """Processed transaction from AI analysis."""

    transaction_type: TransactionType = Field(..., description="Type of transaction")
    amount: Decimal = Field(..., description="Transaction amount (can be negative for cash withdrawals)")
    description: str = Field(..., min_length=1, description="Transaction description")
    confidence: float = Field(..., ge=0, le=1, description="AI confidence score")


class PendingTransaction(BaseModel):
    """Pending transaction waiting for user confirmation."""

    phone_number: str = Field(..., description="User phone number")
    transaction_type: TransactionType = Field(..., description="Suggested transaction type")
    amount: Decimal = Field(..., description="Transaction amount (can be negative for cash withdrawals)")
    description: str = Field(..., description="Transaction description")
    suggested_at: datetime = Field(..., description="When suggestion was made")
    expires_at: datetime = Field(..., description="When suggestion expires")
    transaction_id: int | None = Field(None, description="ID of created transaction (if any)")


class Balance(BaseModel):
    """Account balance model."""

    phone_number: str = Field(..., description="WhatsApp phone number")
    current_balance: Decimal = Field(..., description="Current balance")
    total_sales: Decimal = Field(default=0, description="Total sales")
    total_expenses: Decimal = Field(default=0, description="Total expenses")
    total_adjustments: Decimal = Field(default=0, description="Total cash adjustments")
    last_updated: datetime = Field(..., description="Last update timestamp")


class WhatsAppWebhookEntry(BaseModel):
    """WhatsApp webhook entry model."""

    id: str
    changes: list[dict]


class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook payload model."""

    object: str
    entry: list[WhatsAppWebhookEntry]
