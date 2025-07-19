# 🤖 LanaBot

Bot de WhatsApp inteligente para registro automático de ventas y gastos de tienditas mexicanas.

## 🚀 Características

- **Transcripción de audio**: Convierte mensajes de voz a texto usando Whisper API
- **Procesamiento inteligente**: Extrae automáticamente montos, tipos de transacción y descripciones
- **Lenguaje mexicano**: Entiende expresiones coloquiales mexicanas
- **Respuestas en tiempo real**: Calcula saldo y responde instantáneamente por WhatsApp
- **Alertas automáticas**: Notifica cuando el saldo baja del límite configurado
- **Base de datos en tiempo real**: Almacenamiento en Supabase con sincronización instantánea

## 🛠️ Stack Tecnológico

- **Python 3.12+** con gestión de dependencias ultrarrápida usando **uv**
- **FastAPI** con async/await para máximo rendimiento
- **OpenAI API** (Whisper + GPT-4o) para transcripción y procesamiento
- **Supabase** (PostgreSQL) para base de datos
- **WhatsApp Cloud API** para integración
- **Railway** para deployment automático
- **ruff** para linting y formatting

## 📦 Instalación Rápida

### Prerrequisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) instalado
- Cuenta en OpenAI, Supabase y WhatsApp Business

### 1. Clonar y configurar

```bash
git clone <repo-url>
cd lanabot
```

### 2. Instalar dependencias con uv

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias
uv sync
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 4. Configurar base de datos

Crear tabla en Supabase:

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('venta', 'gasto')),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para mejor rendimiento
CREATE INDEX idx_transactions_phone_number ON transactions(phone_number);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
```

### 5. Ejecutar aplicación

```bash
# Desarrollo
uv run python -m src.lanabot.main

# O usando uvicorn directamente
uv run uvicorn src.lanabot.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Configuración

### Variables de Entorno Requeridas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Clave de OpenAI API | `sk-...` |
| `SUPABASE_URL` | URL del proyecto Supabase | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Clave anónima de Supabase | `eyJ...` |
| `WHATSAPP_ACCESS_TOKEN` | Token de WhatsApp Cloud API | `EAAx...` |
| `WHATSAPP_PHONE_NUMBER_ID` | ID del número de WhatsApp | `123456789` |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Token de verificación del webhook | `mi_token_secreto` |
| `MINIMUM_BALANCE_ALERT` | Límite para alertas de saldo bajo | `500.0` |

### Configuración de WhatsApp Webhook

1. En la consola de Meta Developers, configurar webhook:
   - **URL**: `https://tu-dominio.com/webhook`
   - **Verify Token**: El valor de `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
   - **Campos**: `messages`

## 🚀 Deployment en Railway

### Archivo railway.toml ya configurado

```bash
# Conectar con Railway
railway login
railway init
railway up
```

### Variables de entorno en Railway

Configurar todas las variables del archivo `.env` en el dashboard de Railway.

## 🧪 Testing

```bash
# Ejecutar todos los tests
uv run pytest

# Con coverage
uv run pytest --cov=src/lanabot --cov-report=html

# Tests específicos
uv run pytest tests/test_models.py -v
```

## 🔍 Desarrollo

### Comandos útiles

```bash
# Linting y formatting con ruff
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Ejecutar en modo desarrollo
uv run uvicorn src.lanabot.main:app --reload

# Ver logs en tiempo real (Railway)
railway logs --follow
```

### Estructura del Proyecto

```
lanabot/
├── src/lanabot/           # Código fuente principal
│   ├── __init__.py
│   ├── main.py           # Aplicación FastAPI
│   ├── config.py         # Configuración
│   ├── models.py         # Modelos Pydantic
│   ├── database.py       # Operaciones de base de datos
│   ├── openai_client.py  # Cliente OpenAI
│   └── whatsapp_client.py # Cliente WhatsApp
├── tests/                # Tests
├── pyproject.toml        # Configuración del proyecto
├── railway.toml         # Configuración de Railway
├── .env.example         # Variables de entorno ejemplo
└── README.md
```

## 💬 Ejemplos de Uso

### Mensajes que entiende LanaBot:

**Ventas:**
- "Vendí 3 coca colas a 15 pesos cada una"
- "Se llevaron 2 sabritas de 12 pesos"
- "Gané 150 pesos hoy de dulces"

**Gastos:**
- "Compré mercancía por 500 pesos"
- "Pagué 80 pesos de luz"
- "Gasté 200 en el súper"

**Consultas de saldo:**
- "¿Cuánto tengo?"
- "Mi saldo"
- "Estado de cuenta"

### Respuestas de LanaBot:

```
¡Órale! Tu transacción ya quedó registrada 🎯

💰 Saldo actual: $1,250.00 MXN
📈 Total ventas: $2,500.00
📉 Total gastos: $1,250.00
```

## 🔧 Troubleshooting

### Problemas comunes:

1. **Error de transcripción de audio**
   - Verificar que `OPENAI_API_KEY` esté configurada
   - Comprobar formato de audio (WhatsApp envía OGG)

2. **Webhook no recibe mensajes**
   - Verificar `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
   - Comprobar URL del webhook en Meta Developers
   - Revisar logs: `railway logs --follow`

3. **Error de base de datos**
   - Verificar credenciales de Supabase
   - Confirmar que la tabla `transactions` existe

## 🎯 Roadmap

- [ ] Integración con múltiples monedas
- [ ] Reportes automáticos por WhatsApp
- [ ] Dashboard web para visualización
- [ ] Integración con sistemas de facturación
- [ ] Soporte para múltiples tiendas

## 📄 Licencia

MIT License - Ver archivo `LICENSE` para más detalles.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

**¡Hecho con ❤️ para las tienditas mexicanas!** 🇲🇽