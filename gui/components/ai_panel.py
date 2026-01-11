"""
AI Panel component for R2 Assistant V2.1
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Any
import threading

class AIPanel(ctk.CTkFrame):
    """AI Chat Panel for interacting with AI models"""
    
    def __init__(self, parent, ai_manager=None, theme=None, send_callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.ai_manager = ai_manager
        self.theme = theme
        self.send_callback = send_callback
        
        # History for this panel
        self.message_history = []
        
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
                'warning': '#ffaa00'
            }
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup AI panel UI"""
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
            text="🧠 AI ASSISTANT",
            font=("Consolas", 14, "bold"),
            text_color=self.colors['primary']
        ).pack(side="left")
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            title_frame,
            text="●",
            font=("Arial", 12),
            text_color=self.colors['warning']
        )
        self.status_label.pack(side="right")
        
        # Model selector
        model_frame = ctk.CTkFrame(self, fg_color="transparent")
        model_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            model_frame,
            text="Model:",
            font=("Consolas", 10),
            text_color=self.colors['text_dim']
        ).pack(side="left")
        
        self.model_var = ctk.StringVar(value="mistral-7b")
        model_menu = ctk.CTkOptionMenu(
            model_frame,
            values=["mistral-7b", "gpt-3.5", "local"],
            variable=self.model_var,
            width=120
        )
        model_menu.pack(side="right")
        
        # Chat display
        self.chat_display = ctk.CTkTextbox(
            self,
            height=150,
            font=("Consolas", 10),
            text_color=self.colors['text'],
            fg_color=self.colors['bg_dark'],
            border_width=0,
            wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=5)
        self.chat_display.configure(state="disabled")
        
        # Input area
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ask the AI...",
            font=("Consolas", 11),
            height=35
        )
        self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.input_field.bind("<Return>", lambda e: self._send_message())
        
        send_btn = ctk.CTkButton(
            input_frame,
            text="Send",
            width=80,
            height=35,
            font=("Consolas", 11),
            fg_color=self.colors['primary'],
            command=self._send_message
        )
        send_btn.pack(side="right")
        
        # Add initial message
        self._add_to_display("AI", "Hello! I'm your AI assistant. How can I help you?")
    
    def _send_message(self):
        """Send message to AI"""
        message = self.input_field.get().strip()
        if not message:
            return
        
        self.input_field.delete(0, "end")
        self._add_to_display("You", message)
        
        # Call callback if provided
        if self.send_callback:
            self.send_callback(message)
        
        # Process with AI if manager available
        if self.ai_manager:
            self.status_label.configure(text="●", text_color=self.colors['warning'])
            threading.Thread(target=self._process_with_ai, args=(message,), daemon=True).start()
    
    def _process_with_ai(self, message: str):
        """Process message with AI"""
        try:
            import asyncio
            
            async def get_response():
                if hasattr(self.ai_manager, 'chat'):
                    response = await self.ai_manager.chat(
                        user_id="ai_panel",
                        message=message,
                        model=self.model_var.get()
                    )
                    return response.content
                return "AI service not available"
            
            # Run async in thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_text = loop.run_until_complete(get_response())
            loop.close()
            
            self.status_label.configure(text="●", text_color=self.colors['success'])
            self._add_to_display("AI", response_text)
            
        except Exception as e:
            self.status_label.configure(text="●", text_color=self.colors['warning'])
            self._add_to_display("AI", f"Error: {str(e)}")
    
    def _add_to_display(self, sender: str, message: str):
        """Add message to chat display"""
        self.chat_display.configure(state="normal")
        
        # Add sender with color
        if sender == "You":
            color = self.colors['primary']
        elif sender == "AI":
            color = self.colors['success']
        else:
            color = self.colors['text']
        
        self.chat_display.insert("end", f"{sender}: ", ("sender",))
        self.chat_display.insert("end", f"{message}\n\n")
        
        # Configure tags for coloring
        self.chat_display.tag_config("sender", foreground=color)
        
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        
        # Store in history
        self.message_history.append({
            "sender": sender,
            "message": message,
            "timestamp": __import__('datetime').datetime.now()
        })
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.message_history.clear()
        
        # Add initial message
        self._add_to_display("AI", "Chat cleared. How can I help you?")
    
    def set_ai_manager(self, ai_manager):
        """Set AI manager"""
        self.ai_manager = ai_manager
        if ai_manager and hasattr(ai_manager, 'active') and ai_manager.active:
            self.status_label.configure(text="●", text_color=self.colors['success'])
        else:
            self.status_label.configure(text="●", text_color=self.colors['warning'])
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get chat history"""
        return self.message_history