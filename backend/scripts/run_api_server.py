#!/usr/bin/env python3
"""
Script to run the FastAPI server for the Translation Service.
"""
import uvicorn
from app.core.config import get_settings


def main():
    """Run the FastAPI server."""
    settings = get_settings()

    print("Starting Translation Service API server...")
    print(f"Host: {settings.api_host}")
    print(f"Port: {settings.api_port}")
    print(f"Debug mode: {settings.api_debug}")

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()
