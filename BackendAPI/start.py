#!/usr/bin/env python3
"""
Startup script for Robot Framework Test Manager Backend API.

This script can be used to start the FastAPI application with proper
initialization and configuration.
"""

import os
import sys
import uvicorn
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main entry point for starting the application."""
    parser = argparse.ArgumentParser(description="Robot Framework Test Manager API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Load environment variables
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
    
    print(f"Starting Robot Framework Test Manager API on {args.host}:{args.port}")
    
    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()
