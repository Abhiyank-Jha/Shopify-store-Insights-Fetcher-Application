#!/usr/bin/env python3
"""
Startup script for Shopify Store Insights Fetcher
This script helps you start the application with proper configuration.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import requests
        import beautifulsoup4
        import sqlalchemy
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_environment():
    """Setup environment variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file from template...")
        try:
            with open(".env.example", "r") as f:
                template = f.read()
            with open(".env", "w") as f:
                f.write(template)
            print("✅ .env file created. Please edit it with your configuration.")
        except FileNotFoundError:
            print("⚠️  .env.example not found. Using default configuration.")
    
    # Set default environment variables
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("RELOAD", "true")
    os.environ.setdefault("LOG_LEVEL", "INFO")

def check_database():
    """Check database connectivity"""
    try:
        from app.database.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("The application will run without database persistence")
        return False

def start_application():
    """Start the FastAPI application"""
    print("\n🚀 Starting Shopify Store Insights Fetcher...")
    print("=" * 50)
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Auto-reload: {reload}")
    print(f"📊 Log level: {os.getenv('LOG_LEVEL', 'INFO')}")
    
    # Start the application
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

def show_help():
    """Show help information"""
    print("""
Shopify Store Insights Fetcher - Startup Script

Usage:
    python start.py [options]

Options:
    --help, -h          Show this help message
    --check, -c         Check system requirements only
    --test, -t          Run test script after startup
    --docker, -d        Use Docker Compose (if available)

Examples:
    python start.py                    # Start the application
    python start.py --check           # Check requirements only
    python start.py --test            # Start and run tests
    python start.py --docker          # Use Docker Compose

Environment Variables:
    HOST                Server host (default: 0.0.0.0)
    PORT                Server port (default: 8000)
    RELOAD              Enable auto-reload (default: true)
    LOG_LEVEL           Logging level (default: INFO)
    DATABASE_URL        Database connection string

For more information, see README.md
""")

def run_tests():
    """Run the test script"""
    print("\n🧪 Running API tests...")
    try:
        subprocess.run([sys.executable, "test_api.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
    except FileNotFoundError:
        print("⚠️  test_api.py not found")

def main():
    """Main function"""
    print("🏪 Shopify Store Insights Fetcher")
    print("=" * 40)
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        show_help()
        return
    
    # Check system requirements
    check_python_version()
    
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Check database (optional)
    check_database()
    
    if "--check" in args or "-c" in args:
        print("✅ System check completed")
        return
    
    # Start application
    if "--docker" in args or "-d" in args:
        print("🐳 Starting with Docker Compose...")
        try:
            subprocess.run(["docker-compose", "up", "--build"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Docker Compose failed")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ Docker Compose not found. Starting without Docker...")
            start_application()
    else:
        start_application()
    
    # Run tests if requested
    if "--test" in args or "-t" in args:
        time.sleep(3)  # Wait for application to start
        run_tests()

if __name__ == "__main__":
    main() 