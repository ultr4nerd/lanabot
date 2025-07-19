"""Twilio WhatsApp API client using official SDK."""

import logging
from typing import Optional

from twilio.request_validator import RequestValidator
from twilio.rest import Client

from .config import get_settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Twilio WhatsApp API client using official SDK."""

    def __init__(self) -> None:
        """Initialize Twilio WhatsApp client."""
        self.settings = get_settings()
        self.client = Client(
            self.settings.twilio_account_sid,
            self.settings.twilio_auth_token
        )
        self.validator = RequestValidator(self.settings.twilio_auth_token)

    async def send_message(self, to: str, message: str) -> bool:
        """Send a text message via WhatsApp using Twilio SDK."""
        try:
            # Ensure phone number has whatsapp: prefix for Twilio
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"

            # Use Twilio SDK to send message
            message_instance = self.client.messages.create(
                from_=f"whatsapp:{self.settings.twilio_whatsapp_number}",
                to=to,
                body=message
            )

            logger.info(f"Message sent successfully to {to}: {message_instance.sid}")
            return True

        except Exception as e:
            logger.error(f"Error sending message to {to}: {e}")
            return False

    async def download_media(self, media_url: str) -> Optional[str]:
        """Download media file from Twilio URL."""
        try:
            # Twilio provides direct media URLs in webhooks
            # Just return the URL as Twilio handles authentication
            return media_url

        except Exception as e:
            logger.error(f"Error processing media URL {media_url}: {e}")
            return None

    async def mark_message_read(self, message_id: str) -> bool:
        """Mark a message as read (Not supported in Twilio WhatsApp)."""
        # Twilio WhatsApp doesn't support read receipts like Meta's API
        logger.info(f"Read receipt not supported for message {message_id}")
        return True

    def verify_webhook(self, request_url: str, post_body: str, signature: str) -> bool:
        """Verify Twilio webhook signature using SDK."""
        try:
            return self.validator.validate(request_url, post_body, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook: {e}")
            return False
