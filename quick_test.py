import sys
import importlib
import subprocess

def test_import(module_name):
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False

def test_ffplay():
    try:
        result = subprocess.run(['ffplay', '-version'], 
                              capture_output=True, 
                              text=True,
                              creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            print("✅ ffplay disponível")
            return True
        else:
            print("❌ ffplay não funcionando")
            return False
    except FileNotFoundError:
        print("❌ ffplay não encontrado (instale ffmpeg)")
        return False

print("=== TESTE DE DEPENDÊNCIAS R2 ===")
print(f"Python: {sys.version}")

modules = [
    'speech_recognition',
    'gtts',
    'requests',
    'dotenv',
    'pyautogui',
    'pyperclip',
    'PIL',
    'bs4',
    'urllib3',
    'pygame'
]

print("\nTestando importações...")
results = [test_import(module) for module in modules]

print("\nTestando dependências de áudio...")
ffplay_ok = test_ffplay()

print(f"\nResultado: {sum(results)}/{len(modules)} dependências OK")
print(f"Áudio: {'✅' if ffplay_ok else '❌ (instale ffmpeg)'}")

if all(results):
    print("\n🎉 TODAS AS DEPENDÊNCIAS ESTÃO FUNCIONANDO!")
    print("Você pode executar: python main.py")
else:
    print("\n⚠️  Algumas dependências falharam.")
    print("Execute o setup.bat novamente.")