"""OpenAI client for transcription and text processing."""

import logging
from decimal import Decimal
from typing import Optional

import httpx
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

    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribe audio file to text using Whisper."""
        try:
            # Open the audio file directly from the local path
            with open(audio_file_path, "rb") as audio_file:
                # Transcribe using Whisper
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file, 
                    language="es"
                )

            transcribed_text = transcript.text
            logger.info(f"Whisper transcription: '{transcribed_text}'")
            return transcribed_text

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

    async def process_transaction_text(self, text: str) -> Optional[ProcessedTransaction]:
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

FORMATO DE RESPUESTA (JSON EXACTO):
{
    "transaction_type": "venta",
    "amount": 30.0,
    "description": "3 refrescos",
    "confidence": 0.95
}

IMPORTANTE: 
- SIEMPRE incluye los 4 campos
- NO uses markdown, SOLO JSON puro
- Calcula el monto total (3 × 10 = 30)
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
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
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
"""
            else:
                base_message = f"""
Aquí tienes tu saldo actual, jefe 📊

💰 Saldo: ${balance_info['current_balance']:.2f} MXN
📈 Ventas: ${balance_info['total_sales']:.2f}
📉 Gastos: ${balance_info['total_expenses']:.2f}
"""

            # Add low balance warning if needed
            settings = get_settings()
            if balance_info["current_balance"] < settings.minimum_balance_alert:
                base_message += f"\n⚠️ ¡Ojo! Tu saldo está bajito (menos de ${settings.minimum_balance_alert:.2f})"

            return base_message.strip()

        except Exception as e:
            logger.error(f"Error generating response message: {e}")
            return "¡Órale! Algo salió mal, pero no te preocupes. Intenta de nuevo 🤔"