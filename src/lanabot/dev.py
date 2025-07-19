"""Development server script."""

import uvicorn

from .config import get_settings


def main() -> None:
    """Run the development server with auto-reload."""
    settings = get_settings()
    
    uvicorn.run(
        "lanabot.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()