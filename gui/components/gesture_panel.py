"""
Gesture Control Panel component for R2 Assistant V2.1
"""

import customtkinter as ctk
from typing import Optional, Callable, List
import threading

class GesturePanel(ctk.CTkFrame):
    """Gesture control panel"""
    
    def __init__(self, parent, gesture_controller=None, theme=None,
                 start_callback: Optional[Callable] = None,
                 stop_callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.gesture_controller = gesture_controller
        self.theme = theme
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.is_running = False
        
        # Colors
        if theme:
            self.colors = theme.colors
        else:
            self.colors = {
                'bg_dark': '#0a0a12',
                'bg_panel': '#0d0d1a',
                'primary': '#00ffff',
                'text': '#ffffff',
                'text_dim': '#8888aa',
                'success': '#00ff88',
                'danger': '#ff0066',
                'warning': '#ffaa00'
            }
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup gesture panel UI"""
        self.configure(
            fg_color=self.colors['bg_panel'],
            corner_radius=8,
            border_width=1,
            border_color=self.colors['primary']
        )
        
        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            title_frame,
            text="👋 GESTURE CONTROL",
            font=("Consolas", 14, "bold"),
            text_color=self.colors['primary']
        ).pack(side="left")
        
        # Status
        self.status_label = ctk.CTkLabel(
            title_frame,
            text="OFFLINE",
            font=("Consolas", 10, "bold"),
            text_color=self.colors['warning']
        )
        self.status_label.pack(side="right")
        
        # Info text
        info_text = """Gesture control allows you to control R2 Assistant using hand gestures.

Available gestures:
• ✋ Open hand: Activate voice
• ✊ Fist: Stop/Deactivate
• 👆 Point up: Volume up
• 👇 Point down: Volume down
• 👈👉 Left/Right: Navigate

Requires webcam and OpenCV."""
        
        info_label = ctk.CTkLabel(
            self,
            text=info_text,
            font=("Consolas", 9),
            text_color=self.colors['text_dim'],
            justify="left"
        )
        info_label.pack(fill="x", padx=10, pady=10)
        
        # Control buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.start_btn = ctk.CTkButton(
            button_frame,
            text="START",
            width=100,
            height=35,
            font=("Consolas", 12, "bold"),
            fg_color=self.colors['success'],
            hover_color="#00cc66",
            command=self._start_gestures
        )
        self.start_btn.pack(side="left", padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="STOP",
            width=100,
            height=35,
            font=("Consolas", 12, "bold"),
            fg_color=self.colors['danger'],
            hover_color="#cc0055",
            command=self._stop_gestures,
            state="disabled"
        )
        self.stop_btn.pack(side="left")
        
        # Gesture display
        gesture_frame = ctk.CTkFrame(self, fg_color=self.colors['bg_dark'], height=60)
        gesture_frame.pack(fill="x", padx=10, pady=(0, 10))
        gesture_frame.pack_propagate(False)
        
        self.gesture_label = ctk.CTkLabel(
            gesture_frame,
            text="No gesture detected",
            font=("Consolas", 16),
            text_color=self.colors['text_dim']
        )
        self.gesture_label.pack(expand=True)
        
        # Settings
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            settings_frame,
            text="Sensitivity:",
            font=("Consolas", 10),
            text_color=self.colors['text_dim']
        ).pack(side="left")
        
        self.sensitivity_slider = ctk.CTkSlider(
            settings_frame,
            from_=0.1,
            to=1.0,
            number_of_steps=10,
            width=150
        )
        self.sensitivity_slider.pack(side="left", padx=(10, 0))
        self.sensitivity_slider.set(0.7)
    
    def _start_gestures(self):
        """Start gesture recognition"""
        if self.start_callback:
            self.start_callback()
        
        self.is_running = True
        self.status_label.configure(text="ACTIVE", text_color=self.colors['success'])
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Update gesture label
        self.gesture_label.configure(text="👋 Gestures active", text_color=self.colors['primary'])
    
    def _stop_gestures(self):
        """Stop gesture recognition"""
        if self.stop_callback:
            self.stop_callback()
        
        self.is_running = False
        self.status_label.configure(text="OFFLINE", text_color=self.colors['warning'])
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        # Update gesture label
        self.gesture_label.configure(text="No gesture detected", text_color=self.colors['text_dim'])
    
    def update_gesture(self, gesture_name: str):
        """Update current gesture display"""
        if self.is_running:
            gesture_icons = {
                "open": "✋",
                "fist": "✊",
                "point_up": "👆",
                "point_down": "👇",
                "point_left": "👈",
                "point_right": "👉"
            }
            
            icon = gesture_icons.get(gesture_name, "❓")
            self.gesture_label.configure(text=f"{icon} {gesture_name.upper()}", 
                                       text_color=self.colors['primary'])
    
    def set_gesture_controller(self, gesture_controller):
        """Set gesture controller"""
        self.gesture_controller = gesture_controller
        
        if gesture_controller and hasattr(gesture_controller, 'is_running'):
            if gesture_controller.is_running:
                self._start_gestures()
            else:
                self._stop_gestures()
    
    def get_settings(self) -> dict:
        """Get gesture settings"""
        return {
            'sensitivity': self.sensitivity_slider.get(),
            'is_running': self.is_running
        }