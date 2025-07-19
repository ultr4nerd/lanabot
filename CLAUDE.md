# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LanaBot is a WhatsApp bot for Mexican small shops ("tienditas") to automatically track sales and expenses using voice messages and AI processing. Built with modern Python 3.12+ stack using FastAPI, OpenAI APIs, and Supabase.

## Development Commands

### Setup and Installation
```bash
# Install dependencies with uv (ultra-fast Python package manager)
uv sync

# Install development dependencies
uv sync --dev
```

### Running the Application
```bash
# Development server with reload
uv run uvicorn src.lanabot.main:app --reload --host 0.0.0.0 --port 8000

# Direct execution
uv run python -m src.lanabot.main
```

### Code Quality
```bash
# Lint and format with ruff (all-in-one tool)
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Fix auto-fixable issues
uv run ruff check --fix src/ tests/
```

### Testing
```bash
# Run all tests
uv run pytest

# With coverage report
uv run pytest --cov=src/lanabot --cov-report=term-missing

# Specific test file
uv run pytest tests/test_models.py -v
```

## Architecture

### Core Structure
- **src/lanabot/**: Main application package
  - `main.py`: FastAPI application with webhook endpoints
  - `config.py`: Settings management using Pydantic
  - `models.py`: Data models for transactions, messages, etc.
  - `database.py`: Supabase database operations
  - `openai_client.py`: OpenAI API integration (Whisper + GPT-4o)
  - `whatsapp_client.py`: WhatsApp Cloud API client

### Key Technologies
- **uv**: Ultra-fast Python package management
- **FastAPI**: Async web framework for webhook handling
- **Pydantic**: Data validation and settings management
- **OpenAI API**: Whisper for audio transcription, GPT-4o for text processing
- **Supabase**: PostgreSQL database with real-time features
- **WhatsApp Cloud API**: Message handling and sending

### Database Schema
Single `transactions` table with:
- `phone_number`: WhatsApp user identifier
- `transaction_type`: 'venta' (sale) or 'gasto' (expense)
- `amount`: Transaction amount (Decimal)
- `description`: Transaction description
- `created_at`/`updated_at`: Timestamps

## Configuration

### Environment Variables
Required variables in `.env` (see `.env.example`):
- OpenAI API credentials
- Supabase database credentials
- WhatsApp Cloud API tokens
- Business logic settings (minimum balance alert threshold)

### Token Management
WhatsApp Business API tokens expire regularly. When tokens expire:

1. **Manual Token Refresh**:
   ```bash
   # Run the token refresh script to diagnose issues
   uv run python refresh_token.py
   ```

2. **Meta Developers Console** (Recommended):
   - Visit: https://developers.facebook.com/apps/{APP_ID}/whatsapp-business/wa-dev-console/
   - Generate a new temporary access token
   - Update `.env` file with `META_ACCESS_TOKEN=new_token`
   - Restart the application

3. **Automatic Refresh** (implemented):
   - The WhatsApp client automatically detects 401 errors
   - Attempts token refresh and retries failed requests
   - Falls back to template messages when needed

### Key Features
- Processes Mexican Spanish colloquial expressions
- Transcribes WhatsApp voice messages to text
- Extracts transaction data using AI
- Maintains running balance calculations
- Sends automatic low-balance alerts
- Handles webhook verification and message processing

## Development Notes

- Uses Python 3.12+ features and type hints throughout
- Async/await pattern for all I/O operations
- Structured logging for debugging
- Comprehensive error handling
- Modular design for easy testing and maintenance
- Railway deployment configuration included
