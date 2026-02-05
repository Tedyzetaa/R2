# install_deps.py
import subprocess
import sys

def install_dependencies():
    """Install missing dependencies"""
    dependencies = [
        "gTTS",
        "pygame",
        "requests",
        "customtkinter",
        "pillow",
        "numpy",
        "matplotlib"
    ]
    
    print("📦 Installing missing dependencies...")
    
    for dep in dependencies:
        try:
            __import__(dep.replace("-", "_"))
            print(f"✅ {dep} already installed")
        except ImportError:
            print(f"⬇️ Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} installed")
    
    print("\n🎉 All dependencies installed!")

if __name__ == "__main__":
    install_dependencies()