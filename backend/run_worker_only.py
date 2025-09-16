#!/usr/bin/env python3
"""
Simple script to run ONLY the LiveKit Agents worker.
Use this to test agent functionality separately from the API server.
"""
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run the LiveKit Agents worker."""
    try:
        # Import after path setup
        from agents.worker_entrypoint import cli, WorkerOptions, entrypoint
        
        print("🤖 Starting LiveKit Agents Worker for Translation Services")
        print("   - Agent Name: translation-agent")
        print("   - Ready to handle agent dispatches")
        print("   - Press Ctrl+C to stop")
        print("")
        
        # Run the worker
        cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint,
                agent_name="translation-agent",
            )
        )
        
    except KeyboardInterrupt:
        print("\n👋 Worker stopped by user")
    except Exception as e:
        print(f"❌ Worker failed: {e}")
        raise

if __name__ == "__main__":
    main()


