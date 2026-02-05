# fix_datastream.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def fix_datastream():
    """Corrige o erro -alpha no datastream.py"""
    try:
        import gui.components.datastream as ds_module
        
        # Sobrescrever o método problemático
        def safe_draw_data_points(self):
            """Versão segura sem parâmetro alpha"""
            try:
                if not self.data_points:
                    return
                
                self.delete("data_point")
                
                for i, point in enumerate(self.data_points):
                    x = i * (self.width / len(self.data_points))
                    y = self.height - (point * self.height / 100)
                    
                    # Cores sem transparência
                    if point > 80:
                        color = "#ff5555"
                    elif point > 60:
                        color = "#ffaa00"
                    elif point > 40:
                        color = "#ffff55"
                    elif point > 20:
                        color = "#55ff55"
                    else:
                        color = "#5555ff"
                    
                    point_size = 6
                    self.create_oval(
                        x - point_size, y - point_size,
                        x + point_size, y + point_size,
                        fill=color, outline=color,
                        tags="data_point"
                    )
                    
            except Exception as e:
                print(f"⚠️  safe_draw_data_points: {e}")
        
        # Aplicar o patch
        ds_module.DataStreamVisualization._draw_data_points = safe_draw_data_points
        print("✅ Patch aplicado: datastream.py corrigido")
        
    except Exception as e:
        print(f"❌ Erro ao aplicar patch datastream: {e}")

def fix_wave_animation():
    """Corrige o erro no wave_animation.py"""
    try:
        import gui.components.wave_animation as wave_module
        
        def safe_pulse_circles(self):
            """Versão segura que evita erro NoneType"""
            try:
                if not self.is_animating:
                    return
                
                for circle_id in self.circle_ids:
                    try:
                        # Verificar se o círculo existe
                        self.canvas.itemcget(circle_id, 'outline')
                        
                        # Alternar cores de forma simples
                        current_color = self.canvas.itemcget(circle_id, 'outline')
                        if current_color == self.pulse_color:
                            new_color = self.highlight_color
                        else:
                            new_color = self.pulse_color
                        
                        self.canvas.itemconfig(circle_id, outline=new_color)
                    except:
                        continue
                
                if self.is_animating:
                    self.after(self.pulse_speed, self._pulse_circles)
                    
            except Exception as e:
                print(f"⚠️  safe_pulse_circles: {e}")
                self.is_animating = False
        
        wave_module.WaveAnimation._pulse_circles = safe_pulse_circles
        print("✅ Patch aplicado: wave_animation.py corrigido")
        
    except Exception as e:
        print(f"⚠️  Não foi possível aplicar patch wave_animation: {e}")

if __name__ == "__main__":
    print("🔧 Aplicando patches nos componentes...")
    fix_datastream()
    fix_wave_animation()
    print("\n🎉 Patches aplicados! Execute o start_r2.py novamente.")