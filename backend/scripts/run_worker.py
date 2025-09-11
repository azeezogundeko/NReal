#!/usr/bin/env python3
"""
Script to run the LiveKit worker for the Translation Service.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.worker_entrypoint import main

if __name__ == "__main__":
    main()
