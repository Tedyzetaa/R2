# disable_problematic.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def disable_problematic_components():
    """Desativa componentes problemáticos na GUI"""
    
    try:
        # Carregar e modificar sci_fi_hud.py
        hud_path = Path("gui/sci_fi_hud.py")
        
        if not hud_path.exists():
            print("❌ sci_fi_hud.py não encontrado")
            return
        
        # Ler conteúdo
        with open(hud_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Desativar DataStreamVisualization
        old_line = 'self.data_stream = DataStreamVisualization(stream_frame, width=280, height=200)'
        new_line = '# self.data_stream = DataStreamVisualization(stream_frame, width=280, height=200)  # DISABLED DUE TO ERRORS\n        self.data_stream = None'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            print("✅ DataStreamVisualization desativado")
        else:
            print("⚠️  Linha DataStreamVisualization não encontrada")
        
        # Desativar WaveAnimation se estiver causando problemas
        wave_line = 'self.wave_animation = WaveAnimation(core_frame, size=180)'
        wave_disabled = '# self.wave_animation = WaveAnimation(core_frame, size=180)  # DISABLED DUE TO ERRORS\n        self.wave_animation = None'
        
        if wave_line in content:
            content = content.replace(wave_line, wave_disabled)
            print("✅ WaveAnimation desativado")
        
        # Escrever de volta
        with open(hud_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ sci_fi_hud.py modificado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao modificar sci_fi_hud.py: {e}")

if __name__ == "__main__":
    print("🔧 Desativando componentes problemáticos...")
    disable_problematic_components()
    print("\n🎉 Componentes desativados! Execute o start_r2.py novamente.")