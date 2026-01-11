"""
Radar/Threat display component, formerly a circular gauge.
"""

import customtkinter as ctk
import math
from typing import Optional, Tuple
import random

class CircularGauge(ctk.CTkFrame):
    """Circular gauge for displaying metrics"""
    
    def __init__(self, parent, title: str, value: float, max_value: float = 100,
                 unit: str = "%", size: int = 120, theme=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.title = title
        self.value = value
        self.max_value = max_value
        self.unit = unit
        self.size = size
        self.theme = theme

        # Radar-specific attributes
        self.blips = []  # List of threats
        self.scan_angle = 0
        
        # Colors
        if theme:
            self.colors = theme.colors
        else:
            self.colors = {
                'primary': '#00ffff',
                'secondary': '#0099ff',
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff0066',
                'text': '#ffffff',
                'text_dim': '#8888aa',
                'bg_dark': '#0a0a12'
            }
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup gauge UI"""
        self.configure(fg_color="transparent")
        
        # Canvas for gauge
        self.canvas = ctk.CTkCanvas(
            self,
            width=self.size,
            height=self.size,
            bg=self.colors['bg_dark'],
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Value label
        self.value_label = ctk.CTkLabel(
            self,
            text="",
            font=("Consolas", 10),
            text_color=self.colors['text_dim']
        )
        self.value_label.pack(pady=(5, 0))
        
        # Title label
        self.title_label = ctk.CTkLabel(
            self,
            text=self.title,
            font=("Consolas", 9, "bold"),
            text_color=self.colors['text_dim']
        )
        self.title_label.pack()
        
        # Initial draw
        self._animate_radar()

    def add_threat(self, intensity: float):
        """Adds a blip on the radar based on the anomaly intensity."""
        # intensity 0.0 to 1.0
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(10, self.size // 2 - 15)  # Distance from center

        # Color based on intensity (Yellow -> Red)
        color = "#FFFF00" if intensity < 0.5 else "#FF0000"

        # Add to list to be drawn in the animation loop
        self.blips.append({'angle': angle, 'dist': distance, 'life': 100, 'color': color})

    def _animate_radar(self):
        """Animation loop for the radar."""
        self._draw_radar()
        self.after(100, self._animate_radar)
        
    def _draw_radar(self):
        """Draw the radar screen, sweep line, and blips."""
        self.canvas.delete("all")
        
        center = self.size // 2
        radius = self.size // 2 - 10

        # Draw radar grid
        for r_offset in [0, 20, 40, 60]:
            r = radius - r_offset
            if r > 0:
                self.canvas.create_oval(center - r, center - r, center + r, center + r, outline="#003333", width=1)

        # Draw sweep line
        self.scan_angle = (self.scan_angle + 5) % 360
        angle_rad = math.radians(self.scan_angle)
        x_end = center + radius * math.cos(angle_rad)
        y_end = center + radius * math.sin(angle_rad)
        self.canvas.create_line(center, center, x_end, y_end, fill="#00FF00", width=1)

        # Draw and update blips
        for blip in self.blips[:]:
            x = center + math.cos(blip['angle']) * blip['dist']
            y = center + math.sin(blip['angle']) * blip['dist']
            
            size = 2 + (blip['life'] % 4)
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=blip['color'], outline="")
            
            blip['life'] -= 1
            if blip['life'] <= 0:
                self.blips.remove(blip)

        # Update labels to show threat count
        self.value_label.configure(text=f"{len(self.blips)} threats")
    
    def set_value(self, value: float):
        """Set gauge value and redraw"""
        self.value = value
        # Repurpose this to add a threat if value is high
        if self.value > 80: # Example threshold
            self.add_threat(self.value / 100.0)
    
    def set_title(self, title: str):
        """Set gauge title"""
        self.title = title
        self.title_label.configure(text=title)
    
    def set_unit(self, unit: str):
        """Set gauge unit"""
        self.unit = unit
        # self._draw_radar() # No longer needed, animation loop handles it
    
    def set_max_value(self, max_value: float):
        """Set maximum value"""
        self.max_value = max_value
        # self._draw_radar() # No longer needed, animation loop handles it
    
    def get_value(self) -> float:
        """Get current value"""
        return self.value
    
    def get_percentage(self) -> float:
        """Get value as percentage"""
        return (self.value / self.max_value) * 100
    
    def set_color_scheme(self, low_color: str, mid_color: str, high_color: str):
        """Set custom color scheme"""
        # Store custom colors for percentage-based coloring
        self.custom_colors = {
            'low': low_color,
            'mid': mid_color,
            'high': high_color
        }
    
    def pulse(self, duration: int = 1000):
        """Pulse animation effect"""
        original_color = self.title_label.cget("text_color")
        
        def pulse_effect(step: int, total_steps: int = 10):
            if step < total_steps:
                # Calculate pulse intensity
                intensity = abs(math.sin(step * math.pi / total_steps))
                
                # Update label color
                pulse_color = self._interpolate_color(
                    original_color,
                    self.colors['primary'],
                    intensity
                )
                
                self.title_label.configure(text_color=pulse_color)
                self.value_label.configure(text_color=pulse_color)
                
                # Schedule next step
                self.after(duration // total_steps, 
                          lambda: pulse_effect(step + 1, total_steps))
            else:
                # Restore original color
                self.title_label.configure(text_color=original_color)
                self.value_label.configure(text_color=self.colors['text_dim'])
        
        # Start pulse animation
        pulse_effect(0)
    
    def _interpolate_color(self, color1: str, color2: str, factor: float) -> str:
        """Interpolate between two colors"""
        # Convert hex to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Convert RGB to hex
        def rgb_to_hex(rgb):
            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        
        # Interpolate
        rgb = tuple(int(rgb1[i] + (rgb2[i] - rgb1[i]) * factor) for i in range(3))
        
        return rgb_to_hex(rgb)