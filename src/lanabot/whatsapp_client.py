"""WhatsApp Business Cloud API client for Meta."""

import hashlib
import hmac
import logging
import tempfile
from typing import Optional

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """WhatsApp Business Cloud API client for Meta."""

    def __init__(self) -> None:
        """Initialize Meta WhatsApp client."""
        self.settings = get_settings()
        self.base_url = "https://graph.facebook.com/v18.0"
        self.headers = {
            "Authorization": f"Bearer {self.settings.meta_access_token}",
            "Content-Type": "application/json"
        }

    async def send_message(self, to: str, message: str) -> bool:
        """Send a text message via WhatsApp using Meta Cloud API."""
        try:
            # Remove whatsapp: prefix if present and ensure proper format
            phone_number = to.replace("whatsapp:", "").replace("+", "")
            
            url = f"{self.base_url}/{self.settings.meta_phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                
            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")
                logger.info(f"Message sent successfully to {to}: {message_id}")
                return True
            else:
                # If it's a "not in allowed list" error, try template fallback
                error_text = response.text
                if "131030" in error_text or "not in allowed list" in error_text.lower():
                    logger.info(f"Number {to} not in allowed list, trying template fallback...")
                    return await self.send_template_message(to, message)
                
                logger.error(f"Error sending message to {to}: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending message to {to}: {e}")
            return False

    async def send_template_message(self, to: str, original_message: str) -> bool:
        """Send a template message as fallback when free-form messages fail."""
        try:
            # Remove whatsapp: prefix if present and ensure proper format
            phone_number = to.replace("whatsapp:", "").replace("+", "")
            
            url = f"{self.base_url}/{self.settings.meta_phone_number_id}/messages"
            
            # Use hello_world template as fallback
            # Note: In production, you'd want to create custom templates
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": {
                    "name": "hello_world",
                    "language": {
                        "code": "en_US"
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                
            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")
                logger.info(f"Template message sent successfully to {to}: {message_id}")
                logger.info(f"Original message was: {original_message}")
                return True
            else:
                logger.error(f"Error sending template to {to}: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending template to {to}: {e}")
            return False

    async def send_transaction_template(self, to: str, transaction_type: str, amount: float, 
                                      description: str, current_balance: float, 
                                      total_sales: float, total_expenses: float) -> bool:
        """Send transaction confirmation using custom template."""
        try:
            # Remove whatsapp: prefix if present and ensure proper format
            phone_number = to.replace("whatsapp:", "").replace("+", "")
            
            url = f"{self.base_url}/{self.settings.meta_phone_number_id}/messages"
            
            # Map transaction type to Spanish
            transaction_type_es = "VENTA" if transaction_type == "venta" else "GASTO"
            
            # Use custom transaction_confirmation template
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": {
                    "name": "transaction_confirmation",
                    "language": {
                        "code": "es_MX"
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": transaction_type_es},
                                {"type": "text", "text": str(amount)},
                                {"type": "text", "text": description},
                                {"type": "text", "text": f"{current_balance:.2f}"},
                                {"type": "text", "text": f"{total_sales:.2f}"},
                                {"type": "text", "text": f"{total_expenses:.2f}"}
                            ]
                        }
                    ]
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                
            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")
                logger.info(f"Transaction template sent successfully to {to}: {message_id}")
                return True
            else:
                logger.error(f"Error sending transaction template to {to}: {response.status_code} - {response.text}")
                # Fallback to hello_world if custom template fails
                return await self.send_template_message(to, f"{transaction_type_es}: ${amount}")

        except Exception as e:
            logger.error(f"Error sending transaction template to {to}: {e}")
            return False

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Verify Meta webhook signature."""
        try:
            expected_signature = hmac.new(
                self.settings.meta_app_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Meta sends signature as 'sha256=<signature>'
            signature_without_prefix = signature.replace("sha256=", "")
            
            return hmac.compare_digest(expected_signature, signature_without_prefix)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    async def download_media(self, media_id: str) -> Optional[str]:
        """Download media file from Meta and return local path."""
        try:
            logger.info(f"Downloading media from Meta: {media_id}")
            
            # Get media info first
            media_info_url = f"{self.base_url}/{media_id}"
            
            async with httpx.AsyncClient() as client:
                # Get media info first
                info_response = await client.get(media_info_url, headers=self.headers)
                
                if info_response.status_code != 200:
                    logger.error(f"Failed to get media info: {info_response.status_code}")
                    return None
                
                media_info = info_response.json()
                actual_media_url = media_info.get("url")
                
                if not actual_media_url:
                    logger.error("No media URL found in response")
                    return None
                
                # Download the actual media file
                media_response = await client.get(actual_media_url, headers=self.headers)
                
            if media_response.status_code == 200:
                # Determine file extension from mime type
                mime_type = media_info.get("mime_type", "")
                
                if "audio" in mime_type:
                    if "ogg" in mime_type:
                        extension = ".ogg"
                    elif "mpeg" in mime_type or "mp3" in mime_type:
                        extension = ".mp3"
                    elif "wav" in mime_type:
                        extension = ".wav"
                    else:
                        extension = ".ogg"  # Default for WhatsApp audio
                elif "image" in mime_type:
                    if "jpeg" in mime_type:
                        extension = ".jpg"
                    elif "png" in mime_type:
                        extension = ".png"
                    else:
                        extension = ".jpg"  # Default
                else:
                    extension = ".tmp"
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
                    tmp_file.write(media_response.content)
                    file_path = tmp_file.name
                
                logger.info(f"Downloaded media successfully: {len(media_response.content)} bytes")
                return file_path
            else:
                logger.error(f"Failed to download media: {media_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None