"""
Real-time datastream visualization component
"""

import customtkinter as ctk
import random
import time
from typing import List, Optional, Tuple
from collections import deque

class DataStreamVisualization(ctk.CTkCanvas):
    """Real-time datastream visualization"""
    
    def __init__(self, parent, width: int = 300, height: int = 200, 
                 max_points: int = 100, theme=None, **kwargs):
        self.width = width
        self.height = height
        self.max_points = max_points
        
        super().__init__(
            parent,
            width=width,
            height=height,
            bg='#0a0a12',
            highlightthickness=0,
            **kwargs
        )
        
        # Colors
        if theme:
            self.colors = theme.colors
        else:
            self.colors = {
                'primary': '#00ffff',
                'secondary': '#0099ff',
                'accent': '#ff00ff',
                'bg_dark': '#0a0a12',
                'text': '#ffffff'
            }
        
        # Data storage
        self.data_points = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)
        
        # Visualization settings
        self.show_grid = True
        self.show_points = True
        self.smooth_lines = True
        self.show_glow = True
        
        # Initial data
        self._generate_initial_data()
        
        # Start updates
        self._update_visualization()
        
    def _generate_initial_data(self):
        """Generate initial data points"""
        for i in range(50):
            value = random.uniform(20, 80)
            self.data_points.append(value)
            self.timestamps.append(time.time() - (50 - i) * 0.1)
    
    def add_data_point(self, value: float):
        """Add new data point"""
        self.data_points.append(value)
        self.timestamps.append(time.time())
    
    def clear_data(self):
        """Clear all data points"""
        self.data_points.clear()
        self.timestamps.clear()
    
    def _update_visualization(self):
        """Update the visualization"""
        self.delete("all")
        
        if len(self.data_points) < 2:
            # Draw placeholder
            self._draw_placeholder()
        else:
            # Draw grid
            if self.show_grid:
                self._draw_grid()
            
            # Draw data line
            self._draw_data_line()
            
            # Draw data points
            if self.show_points:
                self._draw_data_points()
            
            # Draw axis labels
            self._draw_labels()
        
        # Schedule next update
        self.after(100, self._update_visualization)
    
    def _draw_placeholder(self):
        """Draw placeholder when no data"""
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Draw message
        self.create_text(
            center_x, center_y,
            text="WAITING FOR DATA...",
            font=("Consolas", 10),
            fill=self.colors['text'],
            justify="center"
        )
        
        # Draw pulsing dot
        pulse_size = 5 + 2 * abs((time.time() % 1) - 0.5)
        self.create_oval(
            center_x - pulse_size, center_y + 20 - pulse_size,
            center_x + pulse_size, center_y + 20 + pulse_size,
            fill=self.colors['primary'],
            outline=""
        )
    
    def _draw_grid(self):
        """Draw grid lines"""
        grid_color = '#1a1a2e'
        
        # Vertical lines
        for i in range(1, 5):
            x = self.width * i // 5
            self.create_line(
                x, 10, x, self.height - 30,
                fill=grid_color,
                width=1,
                dash=(2, 2)
            )
        
        # Horizontal lines
        for i in range(1, 5):
            y = 10 + (self.height - 40) * i // 5
            self.create_line(
                10, y, self.width - 10, y,
                fill=grid_color,
                width=1,
                dash=(2, 2)
            )
    
    def _draw_data_line(self):
        """Draw the main data line"""
        if len(self.data_points) < 2:
            return
        
        # Calculate data bounds
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        data_range = max_val - min_val if max_val > min_val else 1
        
        # Generate line points
        points = []
        for i, value in enumerate(self.data_points):
            # Calculate x position (time-based)
            x = 10 + (self.width - 20) * i / len(self.data_points)
            
            # Calculate y position (value-based, inverted)
            y = self.height - 30 - ((value - min_val) / data_range) * (self.height - 40)
            
            points.extend([x, y])
        
        # Draw main line
        line_options = {
            'fill': self.colors['primary'],
            'width': 2,
            'capstyle': 'round',
            'joinstyle': 'round'
        }
        
        if self.smooth_lines:
            line_options['smooth'] = True
        
        self.create_line(*points, **line_options)
        
        # Draw glow effect
        if self.show_glow:
            glow_options = {
                'fill': self.colors['primary'],
                'width': 1,
                'smooth': True if self.smooth_lines else False,
                'stipple': 'gray50'
            }
            self.create_line(*points, **glow_options)
    
    def _draw_data_points(self):
        """Draw data points as dots"""
        if len(self.data_points) < 1:
            return
        
        # Calculate data bounds
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        data_range = max_val - min_val if max_val > min_val else 1
        
        # Draw recent points (last 10)
        recent_points = min(10, len(self.data_points))
        
        for i in range(-recent_points, 0):
            value = self.data_points[i]
            
            # Calculate position
            x = 10 + (self.width - 20) * (len(self.data_points) + i) / len(self.data_points)
            y = self.height - 30 - ((value - min_val) / data_range) * (self.height - 40)
            
            # Draw point
            point_size = 4
            
            # Outer glow
            self.create_oval(
                x - point_size - 1, y - point_size - 1,
                x + point_size + 1, y + point_size + 1,
                fill=self.colors['accent'],
                outline="",
                alpha=0.3
            )
            
            # Main point
            self.create_oval(
                x - point_size, y - point_size,
                x + point_size, y + point_size,
                fill=self.colors['accent'],
                outline=self.colors['primary'],
                width=1
            )
    
    def _draw_labels(self):
        """Draw axis labels"""
        # X-axis label
        self.create_text(
            self.width // 2, self.height - 10,
            text="TIME →",
            font=("Consolas", 8),
            fill=self.colors['text'],
            justify="center"
        )
        
        # Y-axis label
        self.create_text(
            10, self.height // 2,
            text="VALUE",
            font=("Consolas", 8),
            fill=self.colors['text'],
            angle=90,
            justify="center"
        )
        
        # Current value
        if self.data_points:
            current_value = self.data_points[-1]
            self.create_text(
                self.width - 20, 20,
                text=f"{current_value:.1f}",
                font=("Consolas", 10, "bold"),
                fill=self.colors['primary'],
                anchor="ne"
            )
    
    def set_visualization_settings(self, show_grid: bool = None,
                                  show_points: bool = None,
                                  smooth_lines: bool = None,
                                  show_glow: bool = None):
        """Set visualization settings"""
        if show_grid is not None:
            self.show_grid = show_grid
        if show_points is not None:
            self.show_points = show_points
        if smooth_lines is not None:
            self.smooth_lines = smooth_lines
        if show_glow is not None:
            self.show_glow = show_glow
    
    def get_statistics(self) -> dict:
        """Get data statistics"""
        if not self.data_points:
            return {}
        
        return {
            'data_points': len(self.data_points),
            'current_value': self.data_points[-1] if self.data_points else 0,
            'min_value': min(self.data_points),
            'max_value': max(self.data_points),
            'avg_value': sum(self.data_points) / len(self.data_points),
            'data_rate': len(self.data_points) / max(1, self.timestamps[-1] - self.timestamps[0])
        }