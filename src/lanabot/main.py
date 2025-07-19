"""Main FastAPI application for LanaBot."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from .config import get_settings
from .database import DatabaseManager
from .models import Transaction, WhatsAppMessage
from .openai_client import OpenAIClient
from .pending_manager import pending_manager
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
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge")
):
    """Webhook verification endpoint for Meta WhatsApp."""
    settings = get_settings()

    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(hub_challenge)
    else:
        logger.warning("Webhook verification failed")
        raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming Meta WhatsApp webhook messages."""
    try:
        # Get JSON data (Meta sends JSON, not form data)
        body = await request.body()
        data = await request.json()

        # Skip signature verification for now to debug
        # TODO: Implement proper signature verification later
        logger.info(f"Received webhook from Meta: {data}")

        # Handle webhook verification (Meta sends this on setup)
        if data.get("object") == "whatsapp_business_account":
            entries = data.get("entry", [])

            for entry in entries:
                changes = entry.get("changes", [])

                for change in changes:
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        messages = value.get("messages", [])

                        for message in messages:
                            # Extract message information from Meta webhook
                            message_id = message.get("id")
                            from_number = message.get("from")
                            timestamp = message.get("timestamp")

                            # Determine message type and content
                            message_type = message.get("type", "text")
                            content = None
                            audio_url = None
                            image_url = None

                            if message_type == "text":
                                content = message.get("text", {}).get("body")
                            elif message_type == "audio":
                                audio_info = message.get("audio", {})
                                audio_url = audio_info.get("id")  # Media ID for Meta
                            elif message_type == "image":
                                image_info = message.get("image", {})
                                image_url = image_info.get("id")  # Media ID for Meta

                            if not all([message_id, from_number]):
                                logger.warning("Missing required message fields from Meta")
                                continue

                            # Create WhatsApp message object
                            whatsapp_message = WhatsAppMessage(
                                message_id=message_id,
                                from_number=from_number,
                                message_type=message_type,
                                content=content,
                                audio_url=audio_url,
                                image_url=image_url,
                                timestamp=datetime.fromtimestamp(int(timestamp)) if timestamp else datetime.utcnow(),
                            )

                            # Process the message
                            await process_message(whatsapp_message)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing Meta webhook: {e}")
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

        # Get updated balance and cash flow estimation
        balance = await app.state.db.get_balance(phone_number)
        daily_expenses = await app.state.db.get_daily_expense_average(phone_number)
        
        # Calculate cash flow duration
        days_remaining = None
        if balance.current_balance > 0 and daily_expenses > 0:
            days_remaining = float(balance.current_balance / daily_expenses)

        # Generate response with correction option
        if processed_transaction.transaction_type.value == "venta":
            transaction_type_es = "VENTA"
            opposite_type = "GASTO"
        elif processed_transaction.transaction_type.value == "gasto":
            transaction_type_es = "GASTO"
            opposite_type = "VENTA"
        else:  # ajuste_caja
            transaction_type_es = "AJUSTE DE CAJA"
            opposite_type = "VENTA o GASTO"

        response_message = f"""✅ Registré {transaction_type_es} de ${processed_transaction.amount} ({processed_transaction.description})

💰 Saldo actual: ${balance.current_balance:.2f} MXN
📈 Total ventas: ${balance.total_sales:.2f}
📉 Total gastos: ${balance.total_expenses:.2f}
🔄 Total ajustes: ${balance.total_adjustments:.2f}"""

        # Add cash flow estimation
        if days_remaining is not None:
            if days_remaining >= 1:
                response_message += f"\n📅 Tu efectivo te rinde ~{days_remaining:.1f} días"
            elif days_remaining > 0:
                hours = days_remaining * 24
                response_message += f"\n⏰ Tu efectivo te rinde ~{hours:.1f} horas"
            else:
                response_message += f"\n🚨 ¡Sin fondos para gastos!"

        response_message += f"\n\n❌ ¿Está mal? Responde {opposite_type} para corregir"

        # Send regular message directly (skip template for now)
        logger.info(f"Sending confirmation message to {phone_number}")
        await app.state.whatsapp_client.send_message(phone_number, response_message)

        # Store transaction ID for potential correction
        pending_manager.add_pending(phone_number, processed_transaction, saved_transaction.id)

        # Check for low balance alert
        if await app.state.db.check_low_balance_alert(phone_number):
            alert_message = f"🚨 ¡Aguas! Tu saldo está muy bajo: ${balance.current_balance:.2f}. Considera hacer más ventas o reducir gastos."
            await app.state.whatsapp_client.send_message(phone_number, alert_message)

    except Exception as e:
        logger.error(f"Error processing transaction with confirmation: {e}")


def is_correction_command(text: str) -> str | None:
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

        # If we have a transaction ID, update the existing transaction
        if pending.transaction_id:
            success = await app.state.db.update_transaction_type(pending.transaction_id, new_type)

            if not success:
                await app.state.whatsapp_client.send_message(
                    phone_number,
                    "Error al corregir la transacción. Intenta de nuevo 😕"
                )
                return

            logger.info(f"Updated transaction {pending.transaction_id} to {new_type.value}")
        else:
            # Fallback: create new transaction (shouldn't happen with new flow)
            transaction = Transaction(
                phone_number=phone_number,
                transaction_type=new_type,
                amount=pending.amount,
                description=pending.description,
            )

            saved_transaction = await app.state.db.create_transaction(transaction)
            logger.info(f"Created corrected transaction: {saved_transaction}")

        # Get updated balance
        balance = await app.state.db.get_balance(phone_number)

        # Generate response
        if correction_type == "venta":
            transaction_type_es = "VENTA"
        elif correction_type == "gasto":
            transaction_type_es = "GASTO"
        else:  # ajuste_caja
            transaction_type_es = "AJUSTE DE CAJA"

        response_message = f"""✅ Corregido a {transaction_type_es} de ${pending.amount} ({pending.description})

💰 Saldo actual: ${balance.current_balance:.2f} MXN
📈 Total ventas: ${balance.total_sales:.2f}
📉 Total gastos: ${balance.total_expenses:.2f}
🔄 Total ajustes: ${balance.total_adjustments:.2f}"""

        # Send regular message directly (skip template for now)
        logger.info(f"Sending correction confirmation to {phone_number}")
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

        # Now check for special commands (works for both text and transcribed audio)
        # Check if it's a welcome/help inquiry
        if is_welcome_inquiry(text_to_process):
            await handle_welcome_inquiry(message.from_number)
            return

        # Check if it's a search inquiry
        is_search, search_term, transaction_type = is_search_inquiry(text_to_process)
        if is_search:
            await handle_search_inquiry(message.from_number, search_term, transaction_type)
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


def is_welcome_inquiry(text: str) -> bool:
    """Check if the message is a greeting or help request."""
    welcome_keywords = [
        "hola", "hello", "hi", "buenas", "buenos días", "buenas tardes", "buenas noches",
        "ayuda", "help", "cómo funciona", "como funciona", "qué hace", "que hace",
        "instrucciones", "tutorial", "empezar", "iniciar", "comenzar"
    ]
    
    text_lower = text.lower().strip()
    return any(keyword in text_lower for keyword in welcome_keywords)


def is_search_inquiry(text: str) -> tuple[bool, str, str]:
    """Check if the message is a search request. Returns (is_search, search_term, transaction_type)."""
    text_lower = text.lower().strip()
    
    # Search patterns for expenses
    expense_patterns = [
        "cuánto gasté en", "cuanto gaste en", "gastos de", "gasté de", "gaste de",
        "compré de", "compre de", "cuánto pagué", "cuanto pague"
    ]
    
    # Search patterns for sales  
    sales_patterns = [
        "cuánto vendí de", "cuanto vendi de", "ventas de", "vendí de", "vendi de",
        "cuánto gané", "cuanto gane", "cuánto saqué", "cuanto saque"
    ]
    
    # Check for expense searches
    for pattern in expense_patterns:
        if pattern in text_lower:
            # Extract search term after the pattern
            search_term = text_lower.split(pattern, 1)[1].strip()
            # Remove common endings like "?", "hoy", "ayer"
            search_term = search_term.replace("?", "").replace("hoy", "").replace("ayer", "").strip()
            if search_term:
                return True, search_term, "gasto"
    
    # Check for sales searches
    for pattern in sales_patterns:
        if pattern in text_lower:
            search_term = text_lower.split(pattern, 1)[1].strip()
            search_term = search_term.replace("?", "").replace("hoy", "").replace("ayer", "").strip()
            if search_term:
                return True, search_term, "venta"
    
    return False, "", ""


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


async def handle_search_inquiry(phone_number: str, search_term: str, transaction_type: str) -> None:
    """Handle search requests for transactions."""
    try:
        transactions = await app.state.db.search_transactions(phone_number, search_term, transaction_type)
        
        if not transactions:
            await app.state.whatsapp_client.send_message(
                phone_number,
                f"No encontré transacciones de {transaction_type} con '{search_term}' 🔍\n\nPrueba con otros términos o revisa tus registros."
            )
            return

        # Calculate total
        total = sum(t.amount for t in transactions)
        count = len(transactions)
        
        # Generate response
        tipo_es = "gastos" if transaction_type == "gasto" else "ventas"
        
        response = f"🔍 **Búsqueda: {tipo_es} de '{search_term}'**\n\n"
        response += f"💰 Total: ${total:.2f} MXN ({count} transacciones)\n\n"
        
        # Show recent transactions (max 5)
        response += "📋 **Últimas transacciones:**\n"
        for i, transaction in enumerate(transactions[:5]):
            date = transaction.created_at.strftime("%d/%m")
            response += f"• {date}: ${transaction.amount} - {transaction.description}\n"
        
        if len(transactions) > 5:
            response += f"\n... y {len(transactions) - 5} más"

        await app.state.whatsapp_client.send_message(phone_number, response)
        
    except Exception as e:
        logger.error(f"Error handling search inquiry for {phone_number}: {e}")
        await app.state.whatsapp_client.send_message(
            phone_number,
            f"¡Órale! No pude buscar '{search_term}'. Intenta de nuevo 🔍",
        )


async def handle_welcome_inquiry(phone_number: str) -> None:
    """Handle welcome/help requests."""
    try:
        welcome_message = """¡Órale! Soy LanaBot 🤖, tu asistente de caja en WhatsApp

📝 **¿Cómo funciono?**
• **Ventas**: "Vendí 3 refrescos a 15 pesos cada uno"
• **Gastos**: "Compré mercancía por 200 pesos"
• **Saldo inicial**: "Empiezo el día con 500 pesos"
• **Consultar**: "¿Cuánto tengo?" o "saldo"
• **Tickets**: Manda foto de tu ticket y lo proceso automáticamente

🎯 **Tips:**
• Usa audios o texto, como prefieras
• Te digo cuántos días te rinde tu efectivo
• Si cometo errores, responde VENTA o GASTO para corregir

¡Empecemos! Prueba decirme una venta o gasto 💰"""

        await app.state.whatsapp_client.send_message(phone_number, welcome_message)
        
    except Exception as e:
        logger.error(f"Error handling welcome inquiry for {phone_number}: {e}")
        await app.state.whatsapp_client.send_message(
            phone_number,
            "¡Hola! Soy LanaBot, te ayudo con tu caja. Prueba: 'Vendí 3 refrescos a 10 pesos' 🤖",
        )


async def handle_balance_inquiry(phone_number: str) -> None:
    """Handle balance inquiry request."""
    try:
        balance = await app.state.db.get_balance(phone_number)
        daily_expenses = await app.state.db.get_daily_expense_average(phone_number)
        
        # Calculate cash flow duration
        days_remaining = None
        if balance.current_balance > 0 and daily_expenses > 0:
            days_remaining = float(balance.current_balance / daily_expenses)

        balance_info = {
            "current_balance": balance.current_balance,
            "total_sales": balance.total_sales,
            "total_expenses": balance.total_expenses,
            "total_adjustments": balance.total_adjustments,
            "days_remaining": days_remaining,
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
