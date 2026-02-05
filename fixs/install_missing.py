# install_missing.py
import subprocess
import sys
import importlib

def install_missing():
    """Instala dependências faltantes de forma interativa"""
    missing_packages = []
    
    # Verificar pacotes essenciais
    packages_to_check = [
        ("gTTS", "gtts"),
        ("pygame", "pygame"),
        ("requests", "requests"),
        ("customtkinter", "customtkinter"),
        ("matplotlib", "matplotlib"),
        ("numpy", "numpy"),
        ("pillow", "PIL"),
        ("aiohttp", "aiohttp")
    ]
    
    print("🔍 Verificando dependências...")
    
    for package_name, import_name in packages_to_check:
        try:
            importlib.import_module(import_name)
            print(f"✅ {package_name} já instalado")
        except ImportError:
            print(f"❌ {package_name} não encontrado")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n📦 Pacotes faltando: {', '.join(missing_packages)}")
        response = input("Deseja instalar? (s/n): ").strip().lower()
        
        if response == 's':
            for package in missing_packages:
                print(f"\n⬇️ Instalando {package}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(f"✅ {package} instalado com sucesso")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Falha ao instalar {package}: {e}")
        
        print("\n✅ Instalação concluída!")
    else:
        print("\n🎉 Todas as dependências estão instaladas!")

if __name__ == "__main__":
    install_missing()