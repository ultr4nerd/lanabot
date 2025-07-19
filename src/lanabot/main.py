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
from .pending_manager import pending_manager

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
        image_url = None
        
        if media_url:
            if "audio" in media_content_type:
                message_type = "audio"
                audio_url = media_url
            elif "image" in media_content_type:
                message_type = "image"
                image_url = media_url
        
        # Create WhatsApp message object
        whatsapp_message = WhatsAppMessage(
            message_id=message_sid,
            from_number=from_number,
            message_type=message_type,
            content=message_body if message_type == "text" else None,
            audio_url=audio_url,
            image_url=image_url,
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


async def handle_processed_transaction(phone_number: str, processed_transaction) -> None:
    """Handle a processed transaction based on confidence level."""
    try:
        confidence = processed_transaction.confidence
        
        if confidence >= 0.8:
            # High confidence - auto-process with confirmation option
            await process_transaction_with_confirmation(phone_number, processed_transaction)
        else:
            # Low confidence - ask for clarification
            pending_manager.add_pending(phone_number, processed_transaction)
            
            transaction_type_es = "VENTA" if processed_transaction.transaction_type.value == "venta" else "GASTO"
            
            await app.state.whatsapp_client.send_message(
                phone_number,
                f"📊 Leí ${processed_transaction.amount} en el ticket ({processed_transaction.description})\n\n"
                f"¿Es una {transaction_type_es} o lo contrario?\n"
                f"Responde: VENTA o GASTO"
            )
            
    except Exception as e:
        logger.error(f"Error handling processed transaction: {e}")


async def process_transaction_with_confirmation(phone_number: str, processed_transaction) -> None:
    """Process transaction and offer correction option."""
    try:
        # Create and save transaction
        transaction = Transaction(
            phone_number=phone_number,
            transaction_type=processed_transaction.transaction_type,
            amount=processed_transaction.amount,
            description=processed_transaction.description,
        )
        
        saved_transaction = await app.state.db.create_transaction(transaction)
        logger.info(f"Transaction created with confirmation: {saved_transaction}")
        
        # Get updated balance
        balance = await app.state.db.get_balance(phone_number)
        
        # Generate response with correction option
        transaction_type_es = "VENTA" if processed_transaction.transaction_type.value == "venta" else "GASTO"
        opposite_type = "GASTO" if processed_transaction.transaction_type.value == "venta" else "VENTA"
        
        response_message = f"""✅ Registré {transaction_type_es} de ${processed_transaction.amount} ({processed_transaction.description})

💰 Saldo actual: ${balance.current_balance:.2f} MXN
📈 Total ventas: ${balance.total_sales:.2f}
📉 Total gastos: ${balance.total_expenses:.2f}

❌ ¿Está mal? Responde {opposite_type} para corregir"""

        # Send response
        await app.state.whatsapp_client.send_message(phone_number, response_message)
        
        # Store transaction ID for potential correction
        pending_manager.add_pending(phone_number, processed_transaction)
        
        # Check for low balance alert
        if await app.state.db.check_low_balance_alert(phone_number):
            alert_message = f"🚨 ¡Aguas! Tu saldo está muy bajo: ${balance.current_balance:.2f}. Considera hacer más ventas o reducir gastos."
            await app.state.whatsapp_client.send_message(phone_number, alert_message)
            
    except Exception as e:
        logger.error(f"Error processing transaction with confirmation: {e}")


def is_correction_command(text: str) -> Optional[str]:
    """Check if text is a correction command and return the type."""
    text_clean = text.strip().lower()
    
    if text_clean in ["venta", "vendí", "vendi", "es venta"]:
        return "venta"
    elif text_clean in ["gasto", "compra", "compre", "compré", "es gasto"]:
        return "gasto"
    
    return None


async def handle_transaction_correction(phone_number: str, correction_type: str) -> None:
    """Handle transaction type correction."""
    try:
        pending = pending_manager.get_pending(phone_number)
        if not pending:
            await app.state.whatsapp_client.send_message(
                phone_number,
                "No hay transacciones pendientes de corrección 🤔"
            )
            return
        
        # Remove from pending
        pending_manager.remove_pending(phone_number)
        
        from .models import TransactionType
        new_type = TransactionType(correction_type)
        
        # Create corrected transaction
        transaction = Transaction(
            phone_number=phone_number,
            transaction_type=new_type,
            amount=pending.amount,
            description=pending.description,
        )
        
        saved_transaction = await app.state.db.create_transaction(transaction)
        logger.info(f"Corrected transaction created: {saved_transaction}")
        
        # Get updated balance
        balance = await app.state.db.get_balance(phone_number)
        
        # Generate response
        transaction_type_es = "VENTA" if correction_type == "venta" else "GASTO"
        
        response_message = f"""✅ Corregido a {transaction_type_es} de ${pending.amount} ({pending.description})

💰 Saldo actual: ${balance.current_balance:.2f} MXN
📈 Total ventas: ${balance.total_sales:.2f}
📉 Total gastos: ${balance.total_expenses:.2f}"""

        await app.state.whatsapp_client.send_message(phone_number, response_message)
        
        # Check for low balance alert
        if await app.state.db.check_low_balance_alert(phone_number):
            alert_message = f"🚨 ¡Aguas! Tu saldo está muy bajo: ${balance.current_balance:.2f}. Considera hacer más ventas o reducir gastos."
            await app.state.whatsapp_client.send_message(phone_number, alert_message)
            
    except Exception as e:
        logger.error(f"Error handling transaction correction: {e}")


async def process_message(message: WhatsAppMessage) -> None:
    """Process a WhatsApp message and handle transaction logic."""
    try:
        # First check if this is a correction command
        if message.message_type == "text" and message.content:
            correction_type = is_correction_command(message.content)
            if correction_type and pending_manager.has_pending(message.from_number):
                await handle_transaction_correction(message.from_number, correction_type)
                return
        
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
                
        # If it's an image message, process the ticket
        elif message.message_type == "image" and message.image_url:
            # Download the image file from Twilio
            image_file_path = await app.state.whatsapp_client.download_media(message.image_url)
            
            if not image_file_path:
                await app.state.whatsapp_client.send_message(
                    message.from_number,
                    "¡Órale! No pude descargar la imagen. ¿Puedes intentar de nuevo? 📸",
                )
                return
            
            try:
                processed_transaction = await app.state.openai_client.process_ticket_image(
                    image_file_path
                )
                
                # Clean up temporary file
                import os
                try:
                    os.unlink(image_file_path)
                except Exception:
                    pass  # Ignore cleanup errors
                
                if not processed_transaction:
                    await app.state.whatsapp_client.send_message(
                        message.from_number,
                        "No pude encontrar información de compra en esta imagen. ¿Puedes tomar otra foto del ticket? 🧾",
                    )
                    return
                
                # Handle based on confidence level
                await handle_processed_transaction(message.from_number, processed_transaction)
                return
                
            except Exception as e:
                logger.error(f"Error processing ticket image: {e}")
                # Clean up temporary file on error too
                import os
                try:
                    os.unlink(image_file_path)
                except Exception:
                    pass
                
                await app.state.whatsapp_client.send_message(
                    message.from_number,
                    "¡Órale! No pude leer el ticket. ¿Puedes tomar otra foto más clara? 📸",
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
        
        # Handle transaction with new smart confirmation flow
        await handle_processed_transaction(message.from_number, processed_transaction)
    
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