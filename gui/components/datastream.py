"""
Data Stream Visualization Component - Sci-Fi HUD
CORRECTED VERSION - No alpha parameter
"""

import tkinter as tk
import random
import time
from typing import List, Optional

class DataStreamVisualization(tk.Canvas):
    """Sci-Fi data stream visualization - FIXED VERSION"""
    
    def __init__(self, parent, width: int = 300, height: int = 200, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        
        self.width = width
        self.height = height
        self.data_points: List[float] = []
        self.max_points = 50
        self.delay = 200  # Velocidade padrão (ms)
        
        # Sci-Fi colors
        self.bg_color = "#0a0a12"
        self.grid_color = "#1a1a3a"
        self.data_color = "#00ffff"
        self.pulse_color = "#9d00ff"
        self.text_color = "#a0a0c0"
        
        # Configure canvas
        self.configure(
            bg=self.bg_color,
            highlightthickness=0,
            borderwidth=0
        )
        
        # Initialize
        self._initialize_data()
        self._draw_background()
        self._update_visualization()
        
        # Start updates
        self.is_running = True
        self._schedule_update()
    
    def _initialize_data(self):
        """Initialize with random data"""
        for _ in range(self.max_points):
            self.data_points.append(random.uniform(10, 90))
    
    def _draw_background(self):
        """Draw the static background"""
        # Background
        self.create_rectangle(0, 0, self.width, self.height, 
                            fill=self.bg_color, outline="")
        
        # Grid
        grid_spacing = 20
        for x in range(0, self.width, grid_spacing):
            self.create_line(x, 0, x, self.height, 
                           fill=self.grid_color, width=1, dash=(2, 4))
        
        for y in range(0, self.height, grid_spacing):
            self.create_line(0, y, self.width, y, 
                           fill=self.grid_color, width=1, dash=(2, 4))
        
        # Border
        self.create_rectangle(2, 2, self.width-2, self.height-2,
                            outline=self.grid_color, width=2)
        
        # Title
        self.create_text(10, 10, text="DATA STREAM", anchor="nw",
                        fill=self.text_color, font=("Consolas", 9, "bold"))
        
        # Status
        self.create_text(self.width-10, 10, text="LIVE", anchor="ne",
                        fill="#00ff00", font=("Consolas", 8, "bold"))
    
    def _update_visualization(self):
        """Update the data visualization"""
        try:
            # Clear dynamic elements
            self.delete("data_line")
            self.delete("data_point")
            self.delete("pulse")
            
            # Add new data point
            new_value = random.uniform(10, 90)
            self.data_points.append(new_value)
            
            # Keep within max points
            if len(self.data_points) > self.max_points:
                self.data_points = self.data_points[-self.max_points:]
            
            # Draw data line
            if len(self.data_points) > 1:
                points = []
                for i, value in enumerate(self.data_points):
                    x = i * (self.width / len(self.data_points))
                    y = self.height - (value * self.height / 100)
                    points.extend([x, y])
                
                self.create_line(
                    points,
                    fill=self.data_color,
                    width=2,
                    smooth=True,
                    tags="data_line"
                )
            
            # Draw latest data point
            if self.data_points:
                last_value = self.data_points[-1]
                x = self.width - 10
                y = self.height - (last_value * self.height / 100)
                
                # Color based on value
                if last_value > 80:
                    point_color = "#ff5555"
                elif last_value > 60:
                    point_color = "#ffaa00"
                elif last_value > 40:
                    point_color = "#ffff55"
                elif last_value > 20:
                    point_color = "#55ff55"
                else:
                    point_color = "#5555ff"
                
                # Draw point WITHOUT ALPHA
                self.create_oval(
                    x-6, y-6, x+6, y+6,
                    fill=point_color,
                    outline=point_color,
                    tags="data_point"
                )
                
                # Draw value
                self.create_text(
                    x-10, y-15,
                    text=f"{last_value:.1f}",
                    fill=point_color,
                    font=("Consolas", 8, "bold"),
                    tags="data_point"
                )
            
            # Draw pulse effect
            self._draw_pulse_effect()
            
        except Exception as e:
            print(f"⚠️ Error in _update_visualization: {e}")
    
    def _draw_pulse_effect(self):
        """Draw pulse effect WITHOUT ALPHA"""
        try:
            center_x = self.width - 10
            center_y = self.height // 2
            
            # Draw pulse circle
            pulse_radius = 8
            self.create_oval(
                center_x - pulse_radius,
                center_y - pulse_radius,
                center_x + pulse_radius,
                center_y + pulse_radius,
                outline=self.pulse_color,
                width=2,
                tags="pulse"
            )
            
        except Exception as e:
            print(f"⚠️ Error in _draw_pulse_effect: {e}")
    
    def _schedule_update(self):
        """Schedule the next update"""
        if self.is_running:
            self._update_visualization()
            self.after(self.delay, self._schedule_update)
            
    def set_speed(self, speed_level: int):
        """Set animation speed (1-10)"""
        # 1 = lento (200ms), 10 = rápido (20ms)
        self.delay = max(20, 220 - (speed_level * 20))
    
    def stop(self):
        """Stop the visualization"""
        self.is_running = False
    
    def update_data(self, new_data: List[float]):
        """Update with real data"""
        self.data_points = new_data[-self.max_points:]
        self._update_visualization()
    
    def get_current_data(self) -> List[float]:
        """Get current data"""
        return self.data_points.copy()
