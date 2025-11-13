# deploy.py
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

if __name__ == '__main__':
    install_requirements()
    print("Backend dependencies installed successfully!")
    print("Run: python app.py")