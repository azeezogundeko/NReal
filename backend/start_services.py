#!/usr/bin/env python3
"""
Startup script to run both the FastAPI server and LiveKit Agents worker.
This ensures both services are running for full translation functionality.
"""
import os
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_api_server():
    """Run the FastAPI server."""
    try:
        logger.info("🚀 Starting FastAPI Server...")
        cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        logger.info("👋 API Server stopped")
    except Exception as e:
        logger.error(f"❌ API Server failed: {e}")

def run_worker():
    """Run the LiveKit Agents worker."""
    try:
        logger.info("🤖 Starting LiveKit Agents Worker...")
        cmd = [sys.executable, "scripts/run_worker.py"]
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        logger.info("👋 Worker stopped")
    except Exception as e:
        logger.error(f"❌ Worker failed: {e}")

def main():
    """Run both services concurrently."""
    logger.info("🎯 Starting Translation Services...")
    logger.info("   - FastAPI Server (API endpoints)")
    logger.info("   - LiveKit Agents Worker (translation agents)")
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        logger.info("🛑 Shutting down services...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run both services in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            # Submit both tasks
            api_future = executor.submit(run_api_server)
            worker_future = executor.submit(run_worker)
            
            # Wait for both to complete (or fail)
            api_future.result()
            worker_future.result()
            
        except KeyboardInterrupt:
            logger.info("👋 Services stopped by user")
        except Exception as e:
            logger.error(f"❌ Service failed: {e}")

if __name__ == "__main__":
    main()
