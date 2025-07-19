"""OpenAI client for transcription and text processing."""

import logging
from decimal import Decimal
from typing import Optional

from openai import AsyncOpenAI

from .config import get_settings
from .models import ProcessedTransaction, TransactionType


logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client for audio transcription and text processing."""

    def __init__(self) -> None:
        """Initialize OpenAI client."""
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe_audio(self, audio_file_path: str) -> str | None:
        """Transcribe audio file to text using Whisper."""
        try:
            # Try different approaches to handle audio format

            # First, try sending the file as-is with different extensions
            file_attempts = [
                (audio_file_path, "original"),
                # Try copying with different extensions that Whisper accepts
            ]

            import os
            import shutil
            import tempfile

            # Try with .ogg extension (should work with Whisper)
            ogg_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
                    ogg_path = temp_file.name

                # Copy the original file with .ogg extension
                shutil.copy2(audio_file_path, ogg_path)

                logger.info(f"Trying transcription with .ogg extension: {ogg_path}")

                # Try transcribing as .ogg
                with open(ogg_path, "rb") as audio_file:
                    transcript = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="es"
                    )

                transcribed_text = transcript.text
                logger.info(f"Whisper transcription: '{transcribed_text}'")
                return transcribed_text

            except Exception as ogg_error:
                logger.warning(f"OGG transcription failed: {ogg_error}")

                # Try with .wav extension as fallback
                wav_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                        wav_path = temp_file.name

                    shutil.copy2(audio_file_path, wav_path)

                    logger.info(f"Trying transcription with .wav extension: {wav_path}")

                    with open(wav_path, "rb") as audio_file:
                        transcript = await self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="es"
                        )

                    transcribed_text = transcript.text
                    logger.info(f"Whisper transcription: '{transcribed_text}'")
                    return transcribed_text

                finally:
                    if wav_path and os.path.exists(wav_path):
                        try:
                            os.unlink(wav_path)
                        except Exception:
                            pass

            finally:
                if ogg_path and os.path.exists(ogg_path):
                    try:
                        os.unlink(ogg_path)
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

    async def process_ticket_image(self, image_file_path: str) -> Optional["ProcessedTransaction"]:
        """Process ticket image to extract transaction information using GPT-4o Vision."""
        try:
            import base64

            # Read and encode image
            with open(image_file_path, "rb") as image_file:
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode("utf-8")

            # Prompt for ticket analysis
            system_prompt = """
Eres un experto en leer tickets mexicanos para tenderos. Tu trabajo es extraer información y clasificar con alta precisión.

REGLAS DE CLASIFICACIÓN:
1. GASTO (alta confianza 0.9+):
   - Tickets de: OXXO, Walmart, Soriana, Chedraui, Costco, Sam's Club
   - Tickets de: Coca-Cola, Bimbo, Sabritas, Modelo, etc.
   - Tickets de gasolineras (Pemex, Shell, BP)
   - Tickets de mayoristas o distribuidores

2. VENTA (alta confianza 0.9+):
   - Tickets con logo/nombre de tienda local pequeña
   - Layout de punto de venta básico
   - Sin códigos de barras de grandes cadenas

3. DUDOSO (confianza 0.3-0.6):
   - Tickets borrosos o poco legibles
   - Sin identificación clara del establecimiento
   - Tickets de servicios (luz, agua, teléfono)

FORMATO DE RESPUESTA (JSON EXACTO):
{
    "transaction_type": "venta" o "gasto",
    "amount": número decimal del total,
    "description": "descripción breve",
    "confidence": número entre 0.0 y 1.0
}

IMPORTANTE: 
- Extrae siempre el TOTAL más claro
- Confianza 0.9+ solo si es MUY obvio
- Si dudas, asigna confianza 0.3-0.6
"""

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analiza este ticket de compra:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=300,
            )

            content = response.choices[0].message.content
            logger.info(f"GPT-4o Vision response: {content}")

            if not content or content.strip().lower() == "null":
                return None

            # Clean up and extract JSON
            content = content.strip()
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content

            import json
            try:
                data = json.loads(json_str)
                # Return ProcessedTransaction directly
                from decimal import Decimal

                from .models import ProcessedTransaction, TransactionType

                return ProcessedTransaction(
                    transaction_type=TransactionType(data["transaction_type"]),
                    amount=Decimal(str(data["amount"])),
                    description=data["description"],
                    confidence=float(data["confidence"]),
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Error parsing Vision response: {e}")
                return None

        except Exception as e:
            logger.error(f"Error processing ticket image: {e}")
            return None

    async def process_transaction_text(self, text: str) -> ProcessedTransaction | None:
        """Process text to extract transaction information using GPT-4o."""
        try:
            system_prompt = """
Eres un asistente especializado en procesar mensajes de ventas de tienditas mexicanas.
Tu trabajo es extraer información de transacciones de texto en español mexicano coloquial.

INSTRUCCIONES:
1. Identifica si es una VENTA (ingreso) o GASTO (egreso)
2. Extrae el MONTO en pesos mexicanos
3. Extrae una DESCRIPCIÓN clara y concisa
4. Asigna un nivel de CONFIANZA (0.0 a 1.0)

EJEMPLOS DE VENTAS:
- "Vendí 3 coca colas a 15 pesos cada una" → VENTA, 45, "3 coca colas"
- "Se llevaron 2 sabritas de 12 pesos" → VENTA, 24, "2 sabritas"
- "Gané 150 pesos hoy de dulces" → VENTA, 150, "dulces"

EJEMPLOS DE GASTOS:
- "Compré mercancía por 500 pesos" → GASTO, 500, "mercancía"
- "Pagué 80 pesos de luz" → GASTO, 80, "luz"
- "Gasté 200 en el súper" → GASTO, 200, "súper"

EJEMPLOS DE AJUSTES DE CAJA:
- "Empiezo con 500 pesos" → AJUSTE_CAJA, 500, "saldo inicial"
- "Inicial: 300" → AJUSTE_CAJA, 300, "saldo inicial" 
- "Agregué 200 a caja" → AJUSTE_CAJA, 200, "agregado a caja"
- "Saqué 150 para gastos" → AJUSTE_CAJA, -150, "retirado de caja"
- "Metí 100 de mi bolsa" → AJUSTE_CAJA, 100, "agregado personal"
- "Ajuste: +100" → AJUSTE_CAJA, 100, "ajuste positivo"
- "Ajuste: -50" → AJUSTE_CAJA, -50, "ajuste negativo"

FORMATO DE RESPUESTA (JSON EXACTO):
{
    "transaction_type": "venta" | "gasto" | "ajuste_caja",
    "amount": 30.0,
    "description": "3 refrescos",
    "confidence": 0.95
}

IMPORTANTE: 
- SIEMPRE incluye los 4 campos
- NO uses markdown, SOLO JSON puro
- Calcula el monto total (3 × 10 = 30)
- Los ajustes de caja pueden ser negativos (retiros)
- Si no puedes extraer información clara, responde con null
"""

            user_prompt = f"Procesa este mensaje: '{text}'"

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=200,
            )

            content = response.choices[0].message.content
            logger.info(f"GPT-4o response: {content}")  # Debug: see what GPT returns

            if not content or content.strip().lower() == "null":
                return None

            # Clean up the response - sometimes GPT adds markdown or extra text
            content = content.strip()

            # Try to extract JSON from the response
            import json
            import re

            # Look for JSON block in the response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content

            try:
                data = json.loads(json_str)
                return ProcessedTransaction(
                    transaction_type=TransactionType(data["transaction_type"]),
                    amount=Decimal(str(data["amount"])),
                    description=data["description"],
                    confidence=float(data["confidence"]),
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Error parsing GPT response: {e}")
                logger.error(f"Raw response: '{content}'")
                logger.error(f"Extracted JSON: '{json_str}'")
                return None

        except Exception as e:
            logger.error(f"Error processing transaction text: {e}")
            return None

    async def generate_response_message(
        self, balance_info: dict, transaction_added: bool = True
    ) -> str:
        """Generate a response message in Mexican Spanish."""
        try:
            if transaction_added:
                base_message = f"""
¡Órale! Tu transacción ya quedó registrada 🎯

💰 Saldo actual: ${balance_info['current_balance']:.2f} MXN
📈 Total ventas: ${balance_info['total_sales']:.2f}
📉 Total gastos: ${balance_info['total_expenses']:.2f}
🔄 Total ajustes: ${balance_info.get('total_adjustments', 0):.2f}
"""
            else:
                base_message = f"""
Aquí tienes tu saldo actual, jefe 📊

💰 Saldo: ${balance_info['current_balance']:.2f} MXN
📈 Ventas: ${balance_info['total_sales']:.2f}
📉 Gastos: ${balance_info['total_expenses']:.2f}
🔄 Ajustes: ${balance_info.get('total_adjustments', 0):.2f}
"""

            # Add low balance warning if needed
            settings = get_settings()
            if balance_info["current_balance"] < settings.minimum_balance_alert:
                base_message += f"\n⚠️ ¡Ojo! Tu saldo está bajito (menos de ${settings.minimum_balance_alert:.2f})"

            return base_message.strip()

        except Exception as e:
            logger.error(f"Error generating response message: {e}")
            return "¡Órale! Algo salió mal, pero no te preocupes. Intenta de nuevo 🤔"
