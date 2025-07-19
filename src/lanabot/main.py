"""Main FastAPI application for LanaBot."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from .config import get_settings
from .database import DatabaseManager
from .models import Transaction, WhatsAppMessage, WhatsAppWebhook
from .openai_client import OpenAIClient
from .whatsapp_client import WhatsAppClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Starting LanaBot application...")
    
    # Initialize services
    app.state.db = DatabaseManager()
    app.state.openai_client = OpenAIClient()
    app.state.whatsapp_client = WhatsAppClient()
    
    logger.info("LanaBot application started successfully!")
    yield
    logger.info("Shutting down LanaBot application...")


app = FastAPI(
    title="LanaBot",
    description="Bot de WhatsApp para registro de ventas de tienditas mexicanas",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/webhook")
async def verify_webhook():
    """Webhook verification endpoint for Twilio (not used but kept for compatibility)."""
    return {"status": "webhook endpoint ready"}


@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming Twilio WhatsApp webhook messages."""
    try:
        # Get form data first (Twilio sends form-encoded data)
        form_data = await request.form()
        
        # Skip signature verification for now to debug
        # TODO: Implement proper signature verification later
        logger.info(f"Received webhook from Twilio: {dict(form_data)}")
        
        # Extract message information from Twilio webhook
        message_sid = form_data.get("MessageSid")
        from_number = form_data.get("From", "").replace("whatsapp:", "")
        to_number = form_data.get("To", "").replace("whatsapp:", "")
        message_body = form_data.get("Body", "")
        media_url = form_data.get("MediaUrl0")  # For audio/media files
        media_content_type = form_data.get("MediaContentType0", "")
        
        if not all([message_sid, from_number]):
            logger.warning("Missing required message fields from Twilio")
            return {"status": "ok"}
        
        # Determine message type
        message_type = "text"
        audio_url = None
        
        if media_url and "audio" in media_content_type:
            message_type = "audio"
            audio_url = media_url
        
        # Create WhatsApp message object
        whatsapp_message = WhatsAppMessage(
            message_id=message_sid,
            from_number=from_number,
            message_type=message_type,
            content=message_body if message_type == "text" else None,
            audio_url=audio_url,
            timestamp=datetime.utcnow(),
        )
        
        # Process the message
        await process_message(whatsapp_message)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Legacy function - no longer used with Twilio
# async def process_whatsapp_change(value: dict) -> None:
#     """Process WhatsApp webhook change - Legacy Meta API function."""
#     pass


async def process_message(message: WhatsAppMessage) -> None:
    """Process a WhatsApp message and handle transaction logic."""
    try:
        text_to_process = message.content
        
        # If it's an audio message, transcribe it first
        if message.message_type == "audio" and message.audio_url:
            # Download the audio file from Twilio
            audio_file_path = await app.state.whatsapp_client.download_media(message.audio_url)
            
            if not audio_file_path:
                await app.state.whatsapp_client.send_message(
                    message.from_number,
                    "¡Órale! No pude descargar el audio. ¿Puedes intentar de nuevo? 🎤",
                )
                return
            
            try:
                text_to_process = await app.state.openai_client.transcribe_audio(
                    audio_file_path
                )
                
                # Clean up temporary file
                import os
                try:
                    os.unlink(audio_file_path)
                except Exception:
                    pass  # Ignore cleanup errors
                
            except Exception as e:
                logger.error(f"Error transcribing audio: {e}")
                # Clean up temporary file on error too
                import os
                try:
                    os.unlink(audio_file_path)
                except Exception:
                    pass
                
                await app.state.whatsapp_client.send_message(
                    message.from_number,
                    "¡Órale! No pude entender el audio. ¿Puedes intentar de nuevo o escribir tu mensaje? 🎤",
                )
                return
            
            if not text_to_process:
                await app.state.whatsapp_client.send_message(
                    message.from_number,
                    "¡Órale! No pude entender el audio. ¿Puedes intentar de nuevo o escribir tu mensaje? 🎤",
                )
                return
        
        # If no text content, skip processing
        if not text_to_process:
            logger.warning(f"No text content for message {message.message_id}")
            return
        
        # Check if it's a balance inquiry
        if is_balance_inquiry(text_to_process):
            await handle_balance_inquiry(message.from_number)
            return
        
        # Process transaction with OpenAI
        processed_transaction = await app.state.openai_client.process_transaction_text(
            text_to_process
        )
        
        if not processed_transaction:
            await app.state.whatsapp_client.send_message(
                message.from_number,
                "No pude entender si es una venta o gasto. ¿Puedes ser más específico? Por ejemplo: 'Vendí 3 refrescos a 10 pesos' 🤔",
            )
            return
        
        # Only process transactions with high confidence
        if processed_transaction.confidence < 0.7:
            await app.state.whatsapp_client.send_message(
                message.from_number,
                f"¿Seguro que entendí bien? Parece que {processed_transaction.transaction_type.value} {processed_transaction.description} por ${processed_transaction.amount}. Si es correcto, manda 'sí' 🤨",
            )
            return
        
        # Create transaction
        transaction = Transaction(
            phone_number=message.from_number,
            transaction_type=processed_transaction.transaction_type,
            amount=processed_transaction.amount,
            description=processed_transaction.description,
        )
        
        # Save to database
        saved_transaction = await app.state.db.create_transaction(transaction)
        logger.info(f"Transaction created: {saved_transaction}")
        
        # Get updated balance
        balance = await app.state.db.get_balance(message.from_number)
        
        # Generate response message
        balance_info = {
            "current_balance": balance.current_balance,
            "total_sales": balance.total_sales,
            "total_expenses": balance.total_expenses,
        }
        
        response_message = await app.state.openai_client.generate_response_message(
            balance_info, transaction_added=True
        )
        
        # Send response
        await app.state.whatsapp_client.send_message(
            message.from_number, response_message
        )
        
        # Check for low balance alert
        if await app.state.db.check_low_balance_alert(message.from_number):
            alert_message = f"🚨 ¡Aguas! Tu saldo está muy bajo: ${balance.current_balance:.2f}. Considera hacer más ventas o reducir gastos."
            await app.state.whatsapp_client.send_message(
                message.from_number, alert_message
            )
    
    except Exception as e:
        logger.error(f"Error processing message {message.message_id}: {e}")
        await app.state.whatsapp_client.send_message(
            message.from_number,
            "¡Órale! Algo salió mal por acá. Intenta de nuevo en un ratito 🤖",
        )


def is_balance_inquiry(text: str) -> bool:
    """Check if the message is asking for balance information."""
    balance_keywords = [
        "saldo",
        "balance",
        "cuánto tengo",
        "cuanto tengo",
        "dinero",
        "estado",
        "resumen",
        "cuentas",
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in balance_keywords)


async def handle_balance_inquiry(phone_number: str) -> None:
    """Handle balance inquiry request."""
    try:
        balance = await app.state.db.get_balance(phone_number)
        
        balance_info = {
            "current_balance": balance.current_balance,
            "total_sales": balance.total_sales,
            "total_expenses": balance.total_expenses,
        }
        
        response_message = await app.state.openai_client.generate_response_message(
            balance_info, transaction_added=False
        )
        
        await app.state.whatsapp_client.send_message(phone_number, response_message)
    
    except Exception as e:
        logger.error(f"Error handling balance inquiry for {phone_number}: {e}")
        await app.state.whatsapp_client.send_message(
            phone_number,
            "¡Órale! No pude consultar tu saldo. Intenta de nuevo 📊",
        )


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.lanabot.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )