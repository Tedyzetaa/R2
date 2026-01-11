"""
Alert panel component for displaying system alerts
"""

import customtkinter as ctk
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

class AlertPanel(ctk.CTkFrame):
    """Panel for displaying system alerts"""
    
    def __init__(self, parent, max_alerts: int = 3, theme=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.max_alerts = max_alerts
        self.active_alerts: List[Dict[str, Any]] = []
        
        # Colors
        if theme:
            self.colors = theme.colors
        else:
            self.colors = {
                'primary': '#00ffff',
                'danger': '#ff0066',
                'warning': '#ffaa00',
                'info': '#0099ff',
                'bg_dark': '#0a0a12',
                'text': '#ffffff',
                'text_dim': '#8888aa'
            }
        
        # Alert colors by level
        self.alert_colors = {
            'critical': self.colors['danger'],
            'warning': self.colors['warning'],
            'info': self.colors['info']
        }
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup alert panel UI"""
        self.configure(
            fg_color=self.colors['bg_dark'],
            corner_radius=6,
            border_width=1,
            border_color=self.colors['primary']
        )
        
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="🚨 ACTIVE ALERTS",
            font=("Consolas", 10, "bold"),
            text_color=self.colors['primary']
        )
        self.title_label.pack(pady=(5, 5))
        
        # Alert container
        self.alert_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=60
        )
        self.alert_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.alert_container,
            text="No active alerts",
            font=("Consolas", 9),
            text_color=self.colors['text_dim']
        )
        self.empty_label.pack(pady=10)
        
    def add_alert(self, alert: Dict[str, Any]):
        """Add a new alert"""
        # Remove oldest alert if at max capacity
        if len(self.active_alerts) >= self.max_alerts:
            self._remove_oldest_alert()
        
        # Add timestamp if not present
        if 'timestamp' not in alert:
            alert['timestamp'] = time.time()
        
        # Add to list
        self.active_alerts.append(alert)
        
        # Update display
        self._update_display()
        
        # Auto-remove after timeout
        if alert.get('level') != 'critical':
            self.after(10000, lambda: self.remove_alert(alert.get('id')))
    
    def remove_alert(self, alert_id: str):
        """Remove an alert by ID"""
        self.active_alerts = [
            alert for alert in self.active_alerts 
            if alert.get('id') != alert_id
        ]
        self._update_display()
    
    def _remove_oldest_alert(self):
        """Remove the oldest alert"""
        if self.active_alerts:
            self.active_alerts.pop(0)
    
    def _update_display(self):
        """Update the alert display"""
        # Clear container
        for widget in self.alert_container.winfo_children():
            widget.destroy()
        
        # Show empty state or alerts
        if not self.active_alerts:
            self.empty_label = ctk.CTkLabel(
                self.alert_container,
                text="No active alerts",
                font=("Consolas", 9),
                text_color=self.colors['text_dim']
            )
            self.empty_label.pack(pady=10)
        else:
            # Display active alerts
            for alert in self.active_alerts:
                self._create_alert_widget(alert)
    
    def _create_alert_widget(self, alert: Dict[str, Any]):
        """Create widget for a single alert"""
        alert_frame = ctk.CTkFrame(
            self.alert_container,
            fg_color=self.colors['bg_dark'],
            corner_radius=4,
            border_width=1,
            border_color=self.alert_colors.get(alert.get('level', 'info'), self.colors['info'])
        )
        alert_frame.pack(fill="x", pady=2, padx=2)
        
        # Header with title and timestamp
        header_frame = ctk.CTkFrame(alert_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(3, 0))
        
        # Alert icon based on level
        level = alert.get('level', 'info')
        icon = self._get_alert_icon(level)
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=("Consolas", 10),
            text_color=self.alert_colors.get(level, self.colors['info']),
            width=20
        )
        icon_label.pack(side="left")
        
        # Alert title
        title_text = alert.get('title', 'Alert')[:30]
        if len(alert.get('title', '')) > 30:
            title_text += "..."
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title_text,
            font=("Consolas", 9, "bold"),
            text_color=self.colors['text'],
            justify="left"
        )
        title_label.pack(side="left", padx=(5, 0))
        
        # Timestamp
        timestamp = alert.get('timestamp', time.time())
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        
        time_label = ctk.CTkLabel(
            header_frame,
            text=time_str,
            font=("Consolas", 8),
            text_color=self.colors['text_dim'],
            justify="right"
        )
        time_label.pack(side="right")
        
        # Alert message
        message = alert.get('message', '')
        if message:
            message_frame = ctk.CTkFrame(alert_frame, fg_color="transparent")
            message_frame.pack(fill="x", padx=25, pady=(0, 3))
            
            message_label = ctk.CTkLabel(
                message_frame,
                text=message[:50] + ("..." if len(message) > 50 else ""),
                font=("Consolas", 8),
                text_color=self.colors['text_dim'],
                justify="left",
                wraplength=200
            )
            message_label.pack(anchor="w")
        
        # Dismiss button
        dismiss_button = ctk.CTkButton(
            alert_frame,
            text="×",
            width=20,
            height=20,
            font=("Consolas", 10, "bold"),
            fg_color="transparent",
            hover_color=self.colors['danger'],
            text_color=self.colors['text_dim'],
            command=lambda: self.remove_alert(alert.get('id'))
        )
        dismiss_button.place(relx=1.0, rely=0.0, x=-5, y=5, anchor="ne")
    
    def _get_alert_icon(self, level: str) -> str:
        """Get icon for alert level"""
        icons = {
            'critical': '🔴',
            'warning': '🟡',
            'info': '🔵'
        }
        return icons.get(level, '⚪')
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts"""
        return self.active_alerts.copy()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.active_alerts.clear()
        self._update_display()
    
    def set_max_alerts(self, max_alerts: int):
        """Set maximum number of alerts to display"""
        self.max_alerts = max_alerts
        while len(self.active_alerts) > max_alerts:
            self._remove_oldest_alert()
        self._update_display()
    
    def pulse(self):
        """Pulse animation for new alerts"""
        original_color = self.title_label.cget("text_color")
        
        def pulse_effect(step: int, total_steps: int = 5):
            if step < total_steps:
                # Calculate pulse intensity
                intensity = abs((step % 2) - 0.5) * 2
                
                # Update title color
                pulse_color = self._interpolate_color(
                    original_color,
                    self.colors['danger'],
                    intensity
                )
                
                self.title_label.configure(text_color=pulse_color)
                
                # Schedule next step
                self.after(200, lambda: pulse_effect(step + 1, total_steps))
            else:
                # Restore original color
                self.title_label.configure(text_color=original_color)
        
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