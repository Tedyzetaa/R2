"""
Chat Panel component for R2 Assistant V2.1
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

class ChatPanel(ctk.CTkFrame):
    """Chat interface panel"""
    
    def __init__(self, parent, theme=None, send_callback: Optional[Callable] = None,
                 voice_callback: Optional[Callable] = None, 
                 ai_callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.theme = theme
        self.send_callback = send_callback
        self.voice_callback = voice_callback
        self.ai_callback = ai_callback
        self.message_history = []
        
        # Colors
        if theme:
            self.colors = theme.colors
        else:
            self.colors = {
                'bg_dark': '#0a0a12',
                'bg_panel': '#0d0d1a',
                'primary': '#00ffff',
                'secondary': '#0099ff',
                'text': '#ffffff',
                'text_dim': '#8888aa',
                'success': '#00ff88',
                'warning': '#ffaa00'
            }
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup chat panel UI"""
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
            text="💬 CHAT INTERFACE",
            font=("Consolas", 14, "bold"),
            text_color=self.colors['primary']
        ).pack(side="left")
        
        # Clear button
        clear_btn = ctk.CTkButton(
            title_frame,
            text="Clear",
            width=60,
            height=25,
            font=("Consolas", 9),
            fg_color=self.colors['text_dim'],
            hover_color=self.colors['warning'],
            command=self.clear_chat
        )
        clear_btn.pack(side="right")
        
        # Chat display
        self.chat_display = ctk.CTkTextbox(
            self,
            font=("Consolas", 11),
            text_color=self.colors['text'],
            fg_color=self.colors['bg_dark'],
            border_width=0,
            wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=5)
        self.chat_display.configure(state="disabled")
        
        # Configure tags for different senders
        self.chat_display.tag_config("system", foreground=self.colors['text_dim'])
        self.chat_display.tag_config("user", foreground=self.colors['primary'])
        self.chat_display.tag_config("ai", foreground=self.colors['success'])
        self.chat_display.tag_config("assistant", foreground=self.colors['secondary'])
        self.chat_display.tag_config("alert", foreground=self.colors['warning'])
        
        # Input area
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Voice button
        voice_btn = ctk.CTkButton(
            input_frame,
            text="🎤",
            width=50,
            height=40,
            font=("Arial", 16),
            fg_color=self.colors['secondary'],
            hover_color=self.colors['primary'],
            command=self._toggle_voice
        )
        voice_btn.pack(side="left", padx=(0, 5))
        
        # Input field
        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message here...",
            font=("Consolas", 12),
            height=40
        )
        self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.input_field.bind("<Return>", lambda e: self._send_message())
        
        # Send button
        send_btn = ctk.CTkButton(
            input_frame,
            text="Send",
            width=80,
            height=40,
            font=("Consolas", 12, "bold"),
            fg_color=self.colors['primary'],
            hover_color=self.colors['secondary'],
            command=self._send_message
        )
        send_btn.pack(side="right", padx=(0, 5))
        
        # AI button
        ai_btn = ctk.CTkButton(
            input_frame,
            text="🧠",
            width=50,
            height=40,
            font=("Arial", 16),
            fg_color=self.colors['success'],
            hover_color="#00cc66",
            command=self._call_ai
        )
        ai_btn.pack(side="right")
    
    def _send_message(self):
        """Send message from input field"""
        message = self.input_field.get().strip()
        if not message:
            return
        
        self.input_field.delete(0, "end")
        self.add_message("You", message)
        
        if self.send_callback:
            self.send_callback(message)
    
    def _toggle_voice(self):
        """Toggle voice recognition"""
        if self.voice_callback:
            self.voice_callback()
    
    def _call_ai(self):
        """Call AI with current input"""
        message = self.input_field.get().strip()
        if not message:
            self.add_message("SYSTEM", "Please type something for the AI.")
            return
        
        if self.ai_callback:
            self.ai_callback(message)
    
    def add_message(self, sender: str, message: str):
        """Add message to chat display"""
        self.chat_display.configure(state="normal")
        
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Determine tag based on sender
        if sender.lower() in ["system", "alert", "warning"]:
            tag = "system"
        elif sender.lower() in ["you", "user"]:
            tag = "user"
        elif sender.lower() in ["ai", "assistant", "r2"]:
            tag = "ai"
        else:
            tag = "assistant"
        
        # Format message
        formatted = f"[{timestamp}] {sender}: {message}\n\n"
        
        self.chat_display.insert("end", formatted, tag)
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        
        # Store in history
        self.message_history.append({
            "timestamp": timestamp,
            "sender": sender,
            "message": message,
            "tag": tag
        })
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.message_history.clear()
        
        # Add welcome message
        self.add_message("SYSTEM", "Chat cleared. Welcome to R2 Assistant!")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get chat history"""
        return self.message_history
    
    def set_callbacks(self, send_callback: Optional[Callable] = None,
                     voice_callback: Optional[Callable] = None,
                     ai_callback: Optional[Callable] = None):
        """Update callbacks"""
        if send_callback:
            self.send_callback = send_callback
        if voice_callback:
            self.voice_callback = voice_callback
        if ai_callback:
            self.ai_callback = ai_callback