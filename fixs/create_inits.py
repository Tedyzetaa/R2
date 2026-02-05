# create_inits.py
import os

def create_init_files():
    """Cria arquivos __init__.py em todos os diretórios do pacote"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    directories = [
        'core',
        'gui', 
        'gui/components',
        'gui/windows',
        'features',
        'features/noaa',
        'features/trading',
        'features/monitoring',
        'features/alerts',
        'commands',
        'modules',
        'utils',
    ]
    
    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        if os.path.exists(dir_path):
            init_file = os.path.join(dir_path, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write(f'# {directory} package\n')
                print(f"✅ Criado: {directory}/__init__.py")
            else:
                print(f"✅ Já existe: {directory}/__init__.py")
        else:
            print(f"⚠️  Diretório não existe: {directory}")

if __name__ == "__main__":
    create_init_files()