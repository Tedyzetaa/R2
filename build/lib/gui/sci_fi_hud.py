"""
Main Sci-Fi/HUD interface for R2 Assistant
"""

import customtkinter as ctk
import threading
import time
import random
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

from core.config import AppConfig
from core.history_manager import HistoryManager, EventType
from core.analytics import Analytics
from core.voice_engine import VoiceEngine
from core.audio_processor import AudioProcessor
from core.language_model import LanguageModel
from core.command_system import CommandSystem
from core.alert_system import AlertSystem, AlertLevel
from core.function_handler import FunctionHandler
from core.module_manager import ModuleManager, ModuleStatus

from .theme import SciFiTheme
from .components.wave_animation import WaveAnimation
from .components.circular_gauge import CircularGauge
from .components.datastream import DataStreamVisualization
from .components.alert_panel import AlertPanel
from .components.module_panel import ModulePanel
from .components.network_map import NetworkMap

class R2SciFiGUI(ctk.CTk):
    """Main Sci-Fi/HUD interface window"""
    
    def __init__(self, config: AppConfig):
        super().__init__()
        
        self.config = config
        self.theme = SciFiTheme()
        
        # Initialize core components
        self._init_core_components()
        
        # Setup window
        self._setup_window()
        
        # Build UI
        self._build_ui()
        
        # Start system
        self._start_system()
        
    def _init_core_components(self):
        """Initialize core system components"""
        print("🔧 Initializing core components...")
        
        # History and analytics
        self.history = HistoryManager(config=self.config)
        self.analytics = Analytics()
        
        # Voice and audio
        self.voice_engine = VoiceEngine(self.config)
        self.audio_processor = AudioProcessor(self.config)
        
        # AI and command system
        self.language_model = LanguageModel(self.config)
        self.command_system = CommandSystem()
        self.function_handler = FunctionHandler(self.config)
        
        # Alert system
        self.alert_system = AlertSystem(self.config, self._on_alert_received)
        
        # Module manager
        self.module_manager = ModuleManager(self.config)
        
        # System state
        self.system_status = "operational"
        self.voice_active = False
        self.last_update = time.time()
        
        # Real-time data
        self.metrics = {
            'cpu_usage': 15.0,
            'memory_usage': 45.0,
            'network_speed': 85.0,
            'response_time': 0.12,
            'ai_accuracy': 92.5,
            'voice_accuracy': 88.0
        }
        
    def _setup_window(self):
        """Setup main window properties"""
        self.title("R2 ASSISTANT - SCI-FI/HUD INTERFACE")
        self.geometry(f"{self.config.WINDOW_WIDTH}x{self.config.WINDOW_HEIGHT}")
        
        # Configure theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Make window fullscreen optional
        self.attributes('-fullscreen', False)
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
    def _build_ui(self):
        """Build the complete UI"""
        print("🎨 Building Sci-Fi/HUD interface...")
        
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color=self.theme.colors['bg_dark'])
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Create main grid (3x3)
        self._create_main_grid()
        
        # Top bar
        self._create_top_bar()
        
        # Left panel
        self._create_left_panel()
        
        # Center panel
        self._create_center_panel()
        
        # Right panel
        self._create_right_panel()
        
        # Bottom bar
        self._create_bottom_bar()
        
    def _create_main_grid(self):
        """Create the main 3x3 grid layout"""
        # Configure grid weights
        for i in range(3):
            self.main_container.grid_rowconfigure(i, weight=1)
            self.main_container.grid_columnconfigure(i, weight=1)
        
    def _create_top_bar(self):
        """Create top status bar"""
        top_frame = ctk.CTkFrame(
            self.main_container,
            height=60,
            fg_color=self.theme.colors['bg_medium'],
            corner_radius=0
        )
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        top_frame.grid_propagate(False)
        
        # Left section - Title
        title_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="⚡ R2 ASSISTANT - SCI-FI/HUD INTERFACE",
            font=self.theme.fonts['title'],
            text_color=self.theme.colors['primary']
        )
        self.title_label.pack()
        
        # Center section - System status
        status_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        status_frame.pack(side="left", padx=20, pady=10, expand=True)
        
        self.system_status_label = ctk.CTkLabel(
            status_frame,
            text="🟢 SYSTEM STATUS: OPERATIONAL",
            font=self.theme.fonts['status'],
            text_color=self.theme.colors['success']
        )
        self.system_status_label.pack()
        
        # Right section - Connection status
        conn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        conn_frame.pack(side="right", padx=20, pady=10)
        
        self.connection_label = ctk.CTkLabel(
            conn_frame,
            text="🌐 CONNECTION: ESTABLISHED",
            font=self.theme.fonts['status_small'],
            text_color=self.theme.colors['info']
        )
        self.connection_label.pack()
        
    def _create_left_panel(self):
        """Create left panel (Communication Log & Analysis)"""
        left_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.theme.colors['bg_panel'],
            corner_radius=8
        )
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)
        
        # Communication Log
        comm_frame = self._create_panel(
            left_frame,
            "COMMUNICATION LOG",
            height=250
        )
        comm_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.comm_log = ctk.CTkTextbox(
            comm_frame,
            font=self.theme.fonts['monospace'],
            text_color=self.theme.colors['text_bright'],
            fg_color=self.theme.colors['bg_dark'],
            border_width=0
        )
        self.comm_log.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Analysis Charts
        analysis_frame = self._create_panel(
            left_frame,
            "ANALYSIS CHARTS",
            height=200
        )
        analysis_frame.pack(fill="both", expand=True)
        
        self._create_analysis_charts(analysis_frame)
        
    def _create_center_panel(self):
        """Create center panel (AI Core & Chat)"""
        center_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.theme.colors['bg_panel'],
            corner_radius=8
        )
        center_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # AI Core Animation
        core_frame = self._create_panel(
            center_frame,
            "AI CORE - REAL-TIME ACTIVITY",
            height=200
        )
        core_frame.pack(fill="x", pady=(0, 10))
        
        # Wave animation
        self.wave_animation = WaveAnimation(core_frame, size=180)
        self.wave_animation.pack(pady=10)
        
        # Chat interface
        chat_frame = self._create_panel(
            center_frame,
            "CHAT INTERFACE",
            height=300
        )
        chat_frame.pack(fill="both", expand=True)
        
        self._create_chat_interface(chat_frame)
        
    def _create_right_panel(self):
        """Create right panel (Performance Metrics & Datastream)"""
        right_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.theme.colors['bg_panel'],
            corner_radius=8
        )
        right_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 10), pady=5)
        
        # Performance Metrics
        metrics_frame = self._create_panel(
            right_frame,
            "PERFORMANCE METRICS",
            height=300
        )
        metrics_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self._create_performance_gauges(metrics_frame)
        
        # Datastream
        stream_frame = self._create_panel(
            right_frame,
            "REAL-TIME DATASTREAM",
            height=250
        )
        stream_frame.pack(fill="both", expand=True)
        
        self.data_stream = DataStreamVisualization(stream_frame, width=280, height=200)
        self.data_stream.pack(pady=10)
        
    def _create_bottom_bar(self):
        """Create bottom control bar"""
        bottom_frame = ctk.CTkFrame(
            self.main_container,
            height=80,
            fg_color=self.theme.colors['bg_medium'],
            corner_radius=0
        )
        bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        bottom_frame.grid_propagate(False)
        
        # Left section - Control buttons
        controls_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        controls_frame.pack(side="left", padx=20, pady=10)
        
        self._create_control_buttons(controls_frame)
        
        # Center section - Alert panel
        alert_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        alert_frame.pack(side="left", padx=20, pady=10, expand=True)
        
        self.alert_panel = AlertPanel(alert_frame, max_alerts=3)
        self.alert_panel.pack(fill="both", expand=True)
        
        # Right section - System info
        info_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        info_frame.pack(side="right", padx=20, pady=10)
        
        self._create_system_info(info_frame)
        
    def _create_panel(self, parent, title: str, **kwargs) -> ctk.CTkFrame:
        """Create a styled panel with title"""
        panel = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors['bg_dark'],
            corner_radius=6,
            border_width=1,
            border_color=self.theme.colors['primary'],
            **kwargs
        )
        
        if title:
            title_label = ctk.CTkLabel(
                panel,
                text=title,
                font=self.theme.fonts['panel_title'],
                text_color=self.theme.colors['primary']
            )
            title_label.pack(pady=(8, 4), padx=8, anchor="w")
        
        return panel
    
    def _create_analysis_charts(self, parent):
        """Create analysis charts"""
        # Simple bar charts simulation
        charts_data = [
            ("INPUT ANALYSIS", 78, self.theme.colors['primary']),
            ("OUTPUT ANALYSIS", 65, self.theme.colors['secondary']),
            ("EFFICIENCY", 92, self.theme.colors['success']),
            ("ACCURACY", 88, self.theme.colors['accent'])
        ]
        
        for title, value, color in charts_data:
            chart_frame = ctk.CTkFrame(parent, fg_color="transparent", height=25)
            chart_frame.pack(fill="x", padx=10, pady=2)
            
            # Title
            ctk.CTkLabel(
                chart_frame,
                text=f"{title}:",
                font=self.theme.fonts['small'],
                text_color=self.theme.colors['text_dim'],
                width=120
            ).pack(side="left")
            
            # Progress bar
            progress = ctk.CTkProgressBar(
                chart_frame,
                fg_color=self.theme.colors['bg_medium'],
                progress_color=color,
                height=8
            )
            progress.pack(side="left", padx=(10, 5), fill="x", expand=True)
            progress.set(value / 100)
            
            # Value label
            ctk.CTkLabel(
                chart_frame,
                text=f"{value}%",
                font=self.theme.fonts['small_bold'],
                text_color=color,
                width=40
            ).pack(side="right")
            
    def _create_chat_interface(self, parent):
        """Create chat interface"""
        # Chat display
        self.chat_display = ctk.CTkTextbox(
            parent,
            font=self.theme.fonts['chat'],
            text_color=self.theme.colors['text'],
            fg_color=self.theme.colors['bg_dark'],
            border_width=0
        )
        self.chat_display.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Input frame
        input_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        input_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        # Message input
        self.message_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message or use voice command...",
            font=self.theme.fonts['input'],
            height=35,
            fg_color=self.theme.colors['bg_medium'],
            border_color=self.theme.colors['primary']
        )
        self.message_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.message_input.bind("<Return>", self._on_send_message)
        
        # Send button
        self.send_button = ctk.CTkButton(
            input_frame,
            text="SEND",
            width=80,
            height=35,
            font=self.theme.fonts['button'],
            fg_color=self.theme.colors['primary'],
            hover_color=self.theme.colors['secondary'],
            command=self._on_send_message
        )
        self.send_button.pack(side="right")
        
        # Voice button
        self.voice_button = ctk.CTkButton(
            input_frame,
            text="🎤",
            width=40,
            height=35,
            font=self.theme.fonts['button'],
            fg_color=self.theme.colors['accent'],
            hover_color=self.theme.colors['primary'],
            command=self._toggle_voice
        )
        self.voice_button.pack(side="right", padx=(0, 10))
        
    def _create_performance_gauges(self, parent):
        """Create performance gauges"""
        gauges_frame = ctk.CTkFrame(parent, fg_color="transparent")
        gauges_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure grid for gauges (2x2)
        for i in range(2):
            gauges_frame.grid_rowconfigure(i, weight=1)
            gauges_frame.grid_columnconfigure(i, weight=1)
        
        # Create gauges
        self.throughput_gauge = CircularGauge(
            gauges_frame,
            title="PROCESSING",
            value=self.metrics['cpu_usage'],
            max_value=100,
            unit="%",
            size=100,
            theme=self.theme
        )
        self.throughput_gauge.grid(row=0, column=0, padx=5, pady=5)
        
        self.queries_gauge = CircularGauge(
            gauges_frame,
            title="QUERIES",
            value=self.metrics['memory_usage'],
            max_value=100,
            unit="%",
            size=100,
            theme=self.theme
        )
        self.queries_gauge.grid(row=0, column=1, padx=5, pady=5)
        
        self.response_gauge = CircularGauge(
            gauges_frame,
            title="RESPONSE",
            value=99.5,
            max_value=100,
            unit="%",
            size=100,
            theme=self.theme
        )
        self.response_gauge.grid(row=1, column=0, padx=5, pady=5)
        
        self.network_gauge = CircularGauge(
            gauges_frame,
            title="NETWORK",
            value=self.metrics['network_speed'],
            max_value=100,
            unit="%",
            size=100,
            theme=self.theme
        )
        self.network_gauge.grid(row=1, column=1, padx=5, pady=5)
        
    def _create_control_buttons(self, parent):
        """Create control buttons"""
        buttons = [
            ("🎤 VOICE", self._toggle_voice, self.theme.colors['primary']),
            ("⚙️ MODULES", self._open_modules, self.theme.colors['secondary']),
            ("📊 ANALYTICS", self._open_analytics, self.theme.colors['accent']),
            ("⚡ TRADING", self._open_trading, self.theme.colors['warning']),
            ("🔧 SETTINGS", self._open_settings, self.theme.colors['info']),
        ]
        
        for text, command, color in buttons:
            btn = ctk.CTkButton(
                parent,
                text=text,
                width=100,
                height=40,
                font=self.theme.fonts['button'],
                fg_color=color,
                hover_color=self.theme.colors['highlight'],
                command=command
            )
            btn.pack(side="left", padx=5)
            
            if text == "🎤 VOICE":
                self.voice_control_button = btn
    
    def _create_system_info(self, parent):
        """Create system information display"""
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack()
        
        # Time display
        self.time_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=self.theme.fonts['monospace_small'],
            text_color=self.theme.colors['text_dim']
        )
        self.time_label.pack()
        
        # System load
        self.load_label = ctk.CTkLabel(
            info_frame,
            text="LOAD: 15%",
            font=self.theme.fonts['monospace_small'],
            text_color=self.theme.colors['text_dim']
        )
        self.load_label.pack()
        
    def _start_system(self):
        """Start system components and updates"""
        print("🚀 Starting R2 Assistant system...")
        
        # Add startup messages
        self._add_comm_log("⚡ SYSTEM INITIALIZATION STARTED")
        self._add_comm_log("✅ AI Core: Online")
        self._add_comm_log("✅ Voice Engine: Ready")
        self._add_comm_log("✅ Alert System: Active")
        self._add_comm_log("🌌 R2 ASSISTANT: OPERATIONAL")
        
        # Welcome message
        self._add_chat_message("R2", "🔊 *System initialization complete*")
        self._add_chat_message("R2", "🌌 Welcome to R2 Assistant - Sci-Fi/HUD Interface")
        self._add_chat_message("R2", "🎯 All systems operational and ready")
        self._add_chat_message("R2", "💬 Type your message or use voice commands...")
        
        # Start updates
        self._start_updates()
        
        # Start alert monitoring
        self.alert_system.start_monitoring()
        
    def _start_updates(self):
        """Start periodic UI updates"""
        self._update_time()
        self._update_metrics()
        self._update_datastream()
        self._update_system_status()
        
    def _update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=f"TIME: {current_time}")
        self.after(1000, self._update_time)
        
    def _update_metrics(self):
        """Update performance metrics"""
        try:
            # Simulate metric updates
            self.metrics['cpu_usage'] = random.uniform(10, 80)
            self.metrics['memory_usage'] = random.uniform(30, 90)
            self.metrics['network_speed'] = random.uniform(70, 100)
            self.metrics['response_time'] = random.uniform(0.1, 0.5)
            
            # Update gauges
            self.throughput_gauge.set_value(self.metrics['cpu_usage'])
            self.queries_gauge.set_value(self.metrics['memory_usage'])
            self.response_gauge.set_value(100 - (self.metrics['response_time'] * 100))
            self.network_gauge.set_value(self.metrics['network_speed'])
            
            # Update load label
            self.load_label.configure(
                text=f"LOAD: {int(self.metrics['cpu_usage'])}%"
            )
            
        except Exception as e:
            print(f"❌ Error updating metrics: {e}")
        
        self.after(2000, self._update_metrics)
        
    def _update_datastream(self):
        """Update datastream visualization"""
        try:
            # Add random data point
            value = random.uniform(0, 100)
            self.data_stream.add_data_point(value)
            
        except Exception as e:
            print(f"❌ Error updating datastream: {e}")
        
        self.after(100, self._update_datastream)
        
    def _update_system_status(self):
        """Update system status display"""
        try:
            # Determine status based on metrics
            if self.metrics['cpu_usage'] > 80:
                status = "🔴 CRITICAL"
                color = self.theme.colors['danger']
            elif self.metrics['cpu_usage'] > 60:
                status = "🟡 WARNING"
                color = self.theme.colors['warning']
            else:
                status = "🟢 OPERATIONAL"
                color = self.theme.colors['success']
            
            self.system_status_label.configure(
                text=f"SYSTEM STATUS: {status}",
                text_color=color
            )
            
            # Random connection status for demo
            connections = ["ESTABLISHED", "ACTIVE", "CONNECTED", "STABLE"]
            self.connection_label.configure(
                text=f"🌐 CONNECTION: {random.choice(connections)}"
            )
            
        except Exception as e:
            print(f"❌ Error updating system status: {e}")
        
        self.after(3000, self._update_system_status)
        
    # Event Handlers
    
    def _on_send_message(self, event=None):
        """Handle send message"""
        message = self.message_input.get().strip()
        if not message:
            return
        
        # Clear input
        self.message_input.delete(0, "end")
        
        # Add to chat
        self._add_chat_message("YOU", message)
        
        # Process in background
        threading.Thread(
            target=self._process_message,
            args=(message,),
            daemon=True
        ).start()
        
    def _process_message(self, message: str):
        """Process chat message"""
        try:
            # Simulate AI processing
            time.sleep(random.uniform(0.5, 1.5))
            
            # Get AI response
            response = self.language_model.get_response(message)
            
            # Add response to chat
            self.after(0, self._add_chat_message, "R2", response.content)
            
            # Record in history
            self.history.add_chat_message("user", message)
            self.history.add_chat_message("assistant", response.content)
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self.after(0, self._add_chat_message, "SYSTEM", error_msg)
            
    def _toggle_voice(self):
        """Toggle voice recognition"""
        if not self.voice_active:
            # Activate voice
            self.voice_active = True
            self.voice_control_button.configure(
                text="🔴 VOICE ACTIVE",
                fg_color=self.theme.colors['danger']
            )
            
            self._add_comm_log("🎤 Voice recognition: ACTIVATED")
            self._add_chat_message("SYSTEM", "Voice recognition activated")
            
            # Start voice engine
            self.voice_engine.start_listening(self._on_voice_command)
            
        else:
            # Deactivate voice
            self.voice_active = False
            self.voice_control_button.configure(
                text="🎤 VOICE",
                fg_color=self.theme.colors['primary']
            )
            
            self._add_comm_log("🎤 Voice recognition: DEACTIVATED")
            self._add_chat_message("SYSTEM", "Voice recognition deactivated")
            
            # Stop voice engine
            self.voice_engine.stop_listening()
            
    def _on_voice_command(self, command: str):
        """Handle voice command"""
        self.after(0, self._add_chat_message, "YOU (VOICE)", command)
        
        # Process command in background
        threading.Thread(
            target=self._process_voice_command,
            args=(command,),
            daemon=True
        ).start()
        
    def _process_voice_command(self, command: str):
        """Process voice command"""
        try:
            # Use command system
            success, result = self.command_system.execute_command(command)
            
            if success:
                response = f"Command executed: {result}"
            else:
                response = f"Error: {result}"
                
            self.after(0, self._add_chat_message, "R2", response)
            
        except Exception as e:
            error_msg = f"Error processing voice command: {str(e)}"
            self.after(0, self._add_chat_message, "SYSTEM", error_msg)
            
    def _on_alert_received(self, alert: Dict[str, Any]):
        """Handle received alert"""
        self.after(0, self.alert_panel.add_alert, alert)
        self.after(0, self._add_comm_log, f"🚨 ALERT: {alert['title']}")
        
    def _add_comm_log(self, message: str):
        """Add message to communication log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        
        self.comm_log.insert("end", formatted)
        self.comm_log.see("end")
        
    def _add_chat_message(self, sender: str, message: str):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {sender}: {message}\n\n"
        
        self.chat_display.insert("end", formatted)
        self.chat_display.see("end")
        
    # Window Openers
    
    def _open_modules(self):
        """Open modules window"""
        from .windows.modules_window import ModulesWindow
        ModulesWindow(self, self.module_manager)
        
    def _open_analytics(self):
        """Open analytics window"""
        from .windows.analytics_window import AnalyticsWindow
        AnalyticsWindow(self, self.analytics, self.history)
        
    def _open_trading(self):
        """Open trading window"""
        from .windows.trading_window import TradingWindow
        trading_module = self.module_manager.get_module("trading")
        TradingWindow(self, trading_module.instance if trading_module else None)
        
    def _open_settings(self):
        """Open settings window"""
        from .windows.settings_window import SettingsWindow
        SettingsWindow(self, self.config)
        
    def run(self):
        """Run the application"""
        self.mainloop()
        
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up GUI resources...")
        
        # Stop voice engine
        if self.voice_active:
            self.voice_engine.stop_listening()
            
        # Stop alert system
        self.alert_system.stop_monitoring()
        
        # Cleanup audio
        self.audio_processor.cleanup()