"""
Setup script for Patient Appointment System
Author: Vinod Yadav
Date: 7-25-2025
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: {result.stderr}")
        return False
    print(f"Success!")
    return True

def setup_environment():
    """Setup the Python environment"""
    print("🏥 Setting up Patient Appointment System...")
    
    # Uninstall conflicting packages
    print("\n📦 Cleaning up existing packages...")
    packages_to_uninstall = [
        "langchain", "langchain-openai", "langchain-core", 
        "langchain-community", "langsmith", "langgraph"
    ]
    
    for package in packages_to_uninstall:
        run_command(f"pip uninstall {package} -y")
    
    # Install core dependencies first
    print("\n📦 Installing core dependencies...")
    core_deps = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "pydantic==2.5.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "openai==1.12.0",
        "python-multipart==0.0.6",
        "typing-extensions==4.8.0"
    ]
    
    for dep in core_deps:
        print(f"Installing {dep}...")
        if not run_command(f"pip install {dep}"):
            print(f"⚠️  Warning: Failed to install {dep}, continuing...")
    
    print("\n✅ Environment setup complete!")
    return True

if __name__ == "__main__":
    if setup_environment():
        print("\n🎉 Setup successful!")
        print("\n📝 Next steps:")
        print("1. Add your OpenAI API key to .env file")
        print("2. Run: python main_simple.py")
        print("3. Open browser to: http://localhost:8000")
    else:
        print("\n❌ Setup had some issues, but you can try running the app anyway.")