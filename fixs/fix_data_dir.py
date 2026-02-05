# fix_data_dir.py
import os

def fix_data_dir_issue():
    """Corrige o problema de DATA_DIR no sci_fi_hud.py"""
    
    filepath = os.path.join('gui', 'sci_fi_hud.py')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Localizar e corrigir a linha problemática
    if 'persist_file = self.config.DATA_DIR /' in content:
        # Substituir a seção problemática
        old_section = '''        # History and analytics - CORRIGIDO
        max_size = getattr(self.config, 'MAX_HISTORY_SIZE', 1000)
        persist_file = None
        if hasattr(self.config, 'DATA_DIR'):
            persist_file = self.config.DATA_DIR / 'history.json'
        self.history = HistoryManager(max_size=max_size, persist_file=persist_file)'''
        
        new_section = '''        # History and analytics - CORRIGIDO
        max_size = getattr(self.config, 'MAX_HISTORY_SIZE', 1000)
        
        # Corrigir o problema de DATA_DIR sendo string
        persist_file = None
        if hasattr(self.config, 'DATA_DIR'):
            data_dir = self.config.DATA_DIR
            # Se for string, converter para Path
            if isinstance(data_dir, str):
                from pathlib import Path
                data_dir = Path(data_dir)
            persist_file = data_dir / 'history.json'
        
        self.history = HistoryManager(max_size=max_size, persist_file=persist_file)'''
        
        content = content.replace(old_section, new_section)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Problema de DATA_DIR corrigido no sci_fi_hud.py")
    else:
        print("✅ O arquivo já parece estar corrigido")

if __name__ == "__main__":
    fix_data_dir_issue()