"""
Circular gauge component for metrics display
"""

import customtkinter as ctk
import math
from typing import Optional, Tuple

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
        self._draw_gauge()
        
    def _draw_gauge(self):
        """Draw the circular gauge"""
        self.canvas.delete("all")
        
        center = self.size // 2
        radius = self.size // 2 - 10
        thickness = 8
        
        # Calculate percentage
        percentage = min(self.value / self.max_value, 1.0)
        angle = 360 * percentage
        
        # Determine color based on value
        if percentage < 0.3:
            color = self.colors['success']
        elif percentage < 0.7:
            color = self.colors['warning']
        else:
            color = self.colors['danger']
        
        # Draw background arc
        self._draw_arc(
            center, radius,
            start_angle=90,
            end_angle=90 + 360,
            color=self.colors['text_dim'],
            thickness=thickness,
            alpha=0.3
        )
        
        # Draw value arc
        self._draw_arc(
            center, radius,
            start_angle=90,
            end_angle=90 - angle,  # Negative for clockwise
            color=color,
            thickness=thickness,
            alpha=1.0
        )
        
        # Draw center value
        value_text = f"{self.value:.1f}{self.unit}"
        self.canvas.create_text(
            center, center,
            text=value_text,
            font=("Consolas", 12, "bold"),
            fill=self.colors['text'],
            justify="center"
        )
        
        # Update value label
        self.value_label.configure(text=value_text)
        
    def _draw_arc(self, center: int, radius: int, start_angle: float,
                 end_angle: float, color: str, thickness: int, alpha: float = 1.0):
        """Draw an arc on the canvas"""
        # Convert angles to radians
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        # Calculate bounding box
        bbox = (
            center - radius,
            center - radius,
            center + radius,
            center + radius
        )
        
        # Draw arc
        self.canvas.create_arc(
            bbox,
            start=start_angle,
            extent=end_angle - start_angle,
            style="arc",
            outline=color,
            width=thickness
        )
        
        # Add glow effect
        self.canvas.create_arc(
            bbox,
            start=start_angle,
            extent=end_angle - start_angle,
            style="arc",
            outline=color,
            width=1,
            stipple="gray50"
        )
    
    def set_value(self, value: float):
        """Set gauge value and redraw"""
        self.value = value
        self._draw_gauge()
    
    def set_title(self, title: str):
        """Set gauge title"""
        self.title = title
        self.title_label.configure(text=title)
    
    def set_unit(self, unit: str):
        """Set gauge unit"""
        self.unit = unit
        self._draw_gauge()
    
    def set_max_value(self, max_value: float):
        """Set maximum value"""
        self.max_value = max_value
        self._draw_gauge()
    
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