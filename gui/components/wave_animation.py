"""
Wave animation component for AI core visualization
CORRIGIDO COM FALLBACKS ROBUSTOS
"""

import customtkinter as ctk
from typing import Optional, Tuple
import sys

# TRATAMENTO ROBUSTO DE IMPORTS COM FALLBACKS
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except (ImportError, AttributeError) as e:
    print(f"⚠️ Numpy não disponível ou corrompido: {e}")
    print("🔧 Usando fallback math para funcionalidade básica")
    NUMPY_AVAILABLE = False
    import math

# Fallback seguro para funções matemáticas
if NUMPY_AVAILABLE:
    _pi = np.pi
    _sin = np.sin
    _cos = np.cos
else:
    _pi = math.pi
    _sin = math.sin
    _cos = math.cos

class WaveAnimation(ctk.CTkCanvas):
    """Animated wave visualization for AI core com fallbacks robustos"""
    
    def __init__(self, parent, size: int = 200, **kwargs):
        self.size = size
        self.center = size // 2
        self.radius = size // 3
        
        super().__init__(
            parent,
            width=size,
            height=size,
            bg='#0a0a12',
            highlightthickness=0,
            **kwargs
        )
        
        # Animation parameters
        self.angle = 0
        self.amplitude = 15
        self.frequency = 0.15
        self.speed = 0.05
        self.color_mode = "normal"
        
        # Wave components
        self.wave_components = [
            {'freq': 5, 'amp': 0.5, 'phase': 0},
            {'freq': 3, 'amp': 0.3, 'phase': _pi/2},
            {'freq': 7, 'amp': 0.2, 'phase': _pi/4}
        ]
        
        # Drawing IDs
        self.circle_ids = []
        self.wave_id = None
        self.glow_id = None
        
        # Create animation (com tratamento de erro)
        try:
            self._create_circles()
            self._animate()
        except Exception as e:
            print(f"⚠️ Erro na inicialização da animação: {e}")
            self._create_fallback_display()
        
    def _create_fallback_display(self):
        """Cria uma exibição estática quando a animação falha"""
        try:
            # Círculo central estático
            self.create_oval(
                self.center - self.radius, self.center - self.radius,
                self.center + self.radius, self.center + self.radius,
                outline='#00ffff',
                width=2
            )
            
            # Texto informativo
            self.create_text(
                self.center, self.center,
                text="⚙️",
                fill='#00ffff',
                font=('Arial', 24)
            )
            
            self.create_text(
                self.center, self.center + 40,
                text="Animação\nFallback",
                fill='#666699',
                font=('Arial', 8),
                justify='center'
            )
        except:
            pass  # Fallback absoluto
    
    def _create_circles(self):
        """Create concentric circles"""
        colors = ['#00ffff', '#0099ff', '#0066ff']
        widths = [2, 1.5, 1]
        
        for i, (color, width) in enumerate(zip(colors, widths)):
            r = self.radius - (i * 20)
            
            # Main circle
            circle = self.create_oval(
                self.center - r, self.center - r,
                self.center + r, self.center + r,
                outline=color,
                width=width
            )
            self.circle_ids.append(circle)
            
            # Glow effect (somente se suportado)
            try:
                glow = self.create_oval(
                    self.center - r, self.center - r,
                    self.center + r, self.center + r,
                    outline=color,
                    width=1,
                    stipple="gray50"
                )
                self.circle_ids.append(glow)
            except:
                pass  # Ignora se stipple não for suportado
    
    def _generate_wave_points(self) -> list:
        """Generate wave points for current animation state com fallback seguro"""
        points = []
        num_points = 100
        
        for i in range(num_points):
            # USANDO FUNÇÕES SEGURAS COM FALLBACK
            angle = (2 * _pi * i / num_points) + self.angle
            
            # Calculate combined wave with safe sin function
            radius_offset = 0
            for comp in self.wave_components:
                try:
                    sin_value = _sin(comp['freq'] * self.frequency * angle + comp['phase'])
                    radius_offset += comp['amp'] * self.amplitude * sin_value
                except:
                    # Fallback simples se cálculo falhar
                    radius_offset += 0
            
            r = self.radius + radius_offset
            
            # Convert to coordinates com funções seguras
            try:
                x = self.center + r * _cos(angle)
                y = self.center + r * _sin(angle)
                points.extend([x, y])
            except:
                # Fallback: ponto circular
                fallback_angle = 2 * math.pi * i / num_points if not NUMPY_AVAILABLE else angle
                x = self.center + self.radius * math.cos(fallback_angle)
                y = self.center + self.radius * math.sin(fallback_angle)
                points.extend([x, y])
        
        return points
    
    def _animate(self):
        """Update animation com tratamento robusto de erros"""
        try:
            # Update angle
            self.angle += self.speed
            
            # Generate new wave
            points = self._generate_wave_points()
            
            # Remove old wave se existir
            if self.wave_id:
                try:
                    self.delete(self.wave_id)
                except:
                    pass
            
            if self.glow_id:
                try:
                    self.delete(self.glow_id)
                except:
                    pass
            
            # Draw new wave
            self.wave_id = self.create_line(
                *points,
                fill='#00ffff',
                width=2,
                smooth=True,
                joinstyle='round',
                tags='wave'
            )
            
            # Tentar glow effect (opcional)
            try:
                self.glow_id = self.create_line(
                    *points,
                    fill='#ffffff',
                    width=1,
                    smooth=True,
                    stipple="gray50",
                    joinstyle='round',
                    tags='wave_glow'
                )
            except:
                pass  # Glow é opcional
            
            # Add pulsing effect to circles
            self._pulse_circles()
            
        except Exception as e:
            print(f"⚠️ Erro na animação: {e}")
            # Não tentar animação novamente se falhou
            return
        
        # Schedule next frame
        self.after(50, self._animate)
    
    def _pulse_circles(self):
        """Animate pulse circles com safety checks robustos"""
        try:
            # USANDO FUNÇÃO SIN SEGURA
            pulse_factor = 1 + 0.1 * _sin(self.angle * 3)
            
            for i, circle_id in enumerate(self.circle_ids):
                if i % 2 != 0:  # Only affect main circles (not glows)
                    continue

                try:
                    # Obter configuração do item com fallback
                    item_config = self.itemconfig(circle_id)
                    if item_config and 'outline' in item_config:
                        color_info = item_config['outline']
                        if color_info and len(color_info) >= 5:
                            current_color = color_info[-1]
                        else:
                            current_color = '#00ffff'
                    else:
                        current_color = '#00ffff'
                except (AttributeError, ctk.TclError, IndexError, KeyError):
                    current_color = '#00ffff'

                # Ajustar cor
                pulse_color = self._adjust_brightness(current_color, pulse_factor)
                self.itemconfig(circle_id, outline=pulse_color)
                
        except Exception as e:
            # Log e continuar sem animação
            pass
    
    def _adjust_brightness(self, color: str, factor: float) -> str:
        """Adjust color brightness com fallback"""
        try:
            # Convert hex to RGB
            color = color.lstrip('#')
            if len(color) != 6:
                return color
            
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            
            # Apply factor with bounds
            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))
            
            # Convert back to hex
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            # Fallback para cor original
            return color if color else '#00ffff'
    
    def set_amplitude(self, amplitude: float):
        """Set wave amplitude"""
        try:
            self.amplitude = max(5, min(30, amplitude))
        except:
            self.amplitude = 15  # Valor padrão
    
    def set_frequency(self, frequency: float):
        """Set wave frequency"""
        try:
            self.frequency = max(0.05, min(0.5, frequency))
        except:
            self.frequency = 0.15  # Valor padrão
    
    def set_speed(self, speed: float):
        """Set animation speed"""
        try:
            self.speed = max(0.01, min(0.2, speed))
        except:
            self.speed = 0.05  # Valor padrão
    
    def set_load_level(self, cpu_percent):
        """Define a velocidade baseada na CPU (0-100)"""
        # Mapeia 0-100% para velocidade 0.02-0.2
        self.speed = 0.02 + (cpu_percent / 100.0) * 0.18
        
        if cpu_percent > 80:
            self.configure(bg="#550000") # Fundo avermelhado sutil
        else:
            self.configure(bg='#0a0a12')

    def get_animation_state(self) -> dict:
        """Get current animation state com fallback seguro"""
        try:
            angle_mod = self.angle % (2 * _pi)
        except:
            angle_mod = self.angle % (2 * math.pi) if hasattr(math, 'pi') else 0
            
        return {
            'amplitude': self.amplitude,
            'frequency': self.frequency,
            'speed': self.speed,
            'angle': angle_mod,
            'numpy_available': NUMPY_AVAILABLE
        }