#!/usr/bin/env python3
"""
Startup script for Customer Service AI Agent Dashboard
This script initializes the database and starts the application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_files():
    """Check if required configuration files exist"""
    required_files = [
        ".env",
        "config.yaml",
        "data/faqs.csv",
        "data/menu.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
            if file == ".env":
                print("     Run: cp .env.example .env")
            elif file == "config.yaml":
                print("     Run: cp config_example.yaml config.yaml")
        print("\n📖 See README.md for setup instructions")
        return False
    
    return True

def main():
    print("🤖 Customer Service AI Agent Dashboard")
    print("=====================================")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        print(f"   Current version: {sys.version}")
        return 1
    
    # Check files
    if not check_files():
        return 1
    
    print("✅ Configuration files found")
    
    # Create directories
    directories = ["data/docs", "faiss_index", "app/static"]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")
    
    # Start the application
    print("🚀 Starting application...")
    print("   Admin Panel: http://localhost:8000/admin")
    print("   Chat Demo: http://localhost:8000/demo")
    print("   Health Check: http://localhost:8000/healthz")
    print("\n📖 Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--port", "8000",
            "--host", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
    
    return 0

if __name__ == "__main__":
    exit(main())