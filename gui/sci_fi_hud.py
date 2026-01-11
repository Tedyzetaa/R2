"""
Main Sci-Fi/HUD interface for R2 Assistant
V2.1: Integração com novos módulos
"""

import customtkinter as ctk
import threading
import time
import random
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

from core.config import AppConfig, Language
from core.history_manager import HistoryManager, EventType
from core.analytics import Analytics
from core.voice_engine import VoiceEngine
from core.audio_processor import AudioProcessor
from core.command_system import CommandSystem, CommandType
from core.alert_system import AlertSystem, AlertLevel
from core.module_manager import ModuleManager, ModuleStatus
from features.osint.pizzint_service import PizzaINTService

from .theme import SciFiTheme, ThemeManager
from .components.wave_animation import WaveAnimation
from .components.circular_gauge import CircularGauge
from .components.datastream import DataStreamVisualization
from .components.alert_panel import AlertPanel
from .components.module_panel import ModulePanel
from .components.chat_panel import ChatPanel
from .components.ai_panel import AIPanel
from .components.weather_panel import WeatherPanel
from .components.gesture_panel import GesturePanel

class R2SciFiGUI(ctk.CTk):
    """Main Sci-Fi/HUD interface window - V2.1"""
    
    def __init__(self, config=None):
        """Initialize the Sci-Fi HUD interface"""
        print("🚀 Initializing R2 Sci-Fi HUD V2.1...")
        
        # Load configuration
        self.config = config if config else AppConfig.load()
        
        super().__init__()
        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.theme
        
        # Initialize core components
        self._init_core_components()
        
        # Initialize voice state
        self.voice_active = False
        
        # Initialize new V2.1 modules
        self.ai_manager = None
        self.weather_service = None
        self.gesture_controller = None
        self.web_dashboard = None
        
        # Load language
        self._load_language()
        
        # Build interface
        self._build_interface()
        
        # Start system
        self._start_system()
        
    def _init_core_components(self):
        """Initialize core components with fallbacks"""
        print("🔧 Initializing core components...")
        
        # History manager
        max_size = getattr(self.config, 'MAX_HISTORY_SIZE', 1000)
        persist_file = self.config.DATA_DIR / 'history.json'
        self.history = HistoryManager(max_size=max_size, persist_file=persist_file)
        
        # Initialize new V2.1 modules
        self._init_v21_modules()
        
        # Existing components with fallbacks
        try:
            from core.voice_engine import VoiceEngine
            self.voice_engine = VoiceEngine(self.config)
        except:
            print("⚠️ VoiceEngine falhou")
            self.voice_engine = None
        
        try:
            from core.alert_system import AlertSystem
            self.alert_system = AlertSystem(self.config, notification_callback=None)
            self.alert_system.is_monitoring = False
        except:
            print("⚠️ AlertSystem falhou")
            self.alert_system = None
        
        try:
            self.command_system = CommandSystem(self.config)
        except:
            print("⚠️ CommandSystem falhou")
            self.command_system = None
        
        try:
            self.module_manager = ModuleManager(self.config)
        except:
            print("⚠️ ModuleManager falhou")
            self.module_manager = None
        
        # Initialize metrics
        self.metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'network_speed': 0.0,
            'response_time': 0.0,
            'ai_requests': 0,
            'weather_requests': 0
        }
        
        print("✅ Core components initialized")
    
    def _init_v21_modules(self):
        """Initialize V2.1 modules"""
        print("🆕 Initializing V2.1 modules...")
        
        # AI Integration
        if self.config.ENABLE_AI and self.config.AI_ENABLED:
            try:
                from features.ai_integration.openrouter_client import AIIntegrationManager
                self.ai_manager = AIIntegrationManager(self.config)
                print("✅ AI Integration initialized")
            except Exception as e:
                print(f"⚠️ AI Integration failed: {e}")
                self.ai_manager = None
        
        # Weather Service
        if self.config.ENABLE_WEATHER:
            try:
                from features.weather.weather_service import WeatherService
                self.weather_service = WeatherService(self.config)
                print("✅ Weather Service initialized")
            except Exception as e:
                print(f"⚠️ Weather Service failed: {e}")
                self.weather_service = None
        
        # Gesture Control (optional)
        if self.config.ENABLE_GESTURE_CONTROL and self.config.GESTURE_CONTROL_ENABLED:
            try:
                from features.gesture_control.gesture_controller import GestureController
                self.gesture_controller = GestureController(self.config)
                print("✅ Gesture Controller initialized")
            except ImportError:
                print("⚠️ Gesture Control dependencies not installed")
                self.gesture_controller = None
            except Exception as e:
                print(f"⚠️ Gesture Controller failed: {e}")
                self.gesture_controller = None
        
        # Web Dashboard
        if self.config.ENABLE_WEB_DASHBOARD and self.config.WEB_DASHBOARD_ENABLED:
            try:
                from features.web_dashboard.web_server import WebDashboard
                self.web_dashboard = WebDashboard(self.config)
                print("✅ Web Dashboard initialized")
            except Exception as e:
                print(f"⚠️ Web Dashboard failed: {e}")
                self.web_dashboard = None

        # PizzaINT OSINT Monitor
        try:
            self.pizzint_service = PizzaINTService(self.config)
            self.pizzint_service.start()
            print("✅ PizzaINT OSINT Service initialized")
        except Exception as e:
            print(f"⚠️ PizzaINT Service failed: {e}")
            self.pizzint_service = None
    
    def _load_language(self):
        """Load language strings"""
        lang_file = self.config.LOCALES_DIR / f"{self.config.LANGUAGE.value}.json"
        self.translations = {}
        
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                print(f"✅ Loaded language: {self.config.LANGUAGE.value}")
            except:
                print(f"⚠️ Failed to load language file: {lang_file}")
        
        # Fallback to English if empty
        if not self.translations:
            en_file = self.config.LOCALES_DIR / "en-US.json"
            if en_file.exists():
                with open(en_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
    
    def _build_interface(self):
        """Build the complete interface"""
        try:
            self._setup_window()
            self._build_main_layout()
            print("✅ Interface construída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na construção da interface: {e}")
            self._create_simple_interface()
    
    def _setup_window(self):
        """Setup window properties"""
        self.title("R2 ASSISTANT V2.1 - SCI-FI/HUD INTERFACE")
        self.geometry(f"{self.config.WINDOW_WIDTH}x{self.config.WINDOW_HEIGHT}")
        
        # Configure theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Make window resizable
        self.minsize(1200, 700)
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def _build_main_layout(self):
        """Build main layout with new V2.1 panels"""
        # Main container with grid layout
        self.main_container = ctk.CTkFrame(self, fg_color=self.theme.colors['bg_dark'])
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Configure grid (4x3 for more panels)
        for i in range(4):
            self.main_container.grid_rowconfigure(i, weight=1)
        for i in range(3):
            self.main_container.grid_columnconfigure(i, weight=1)
        
        # Top bar
        self._create_top_bar()
        
        # Left column - AI Panel & Weather
        self._create_left_column()
        
        # Center column - Main chat and controls
        self._create_center_column()
        
        # Right column - System info and modules
        self._create_right_column()
        
        # Bottom bar
        self._create_bottom_bar()
    
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
            text="⚡ R2 ASSISTANT V2.1 - SCI-FI/HUD",
            font=self.theme.fonts['title'],
            text_color=self.theme.colors['primary']
        )
        self.title_label.pack()
        
        # Center section - AI Status
        ai_status_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        ai_status_frame.pack(side="left", padx=20, pady=10, expand=True)
        
        self.ai_status_label = ctk.CTkLabel(
            ai_status_frame,
            text="🧠 AI: OFFLINE",
            font=self.theme.fonts['status'],
            text_color=self.theme.colors['warning']
        )
        self.ai_status_label.pack()
        
        # Right section - Weather
        weather_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        weather_frame.pack(side="right", padx=20, pady=10)
        
        self.weather_label = ctk.CTkLabel(
            weather_frame,
            text="🌤️ --°C",
            font=self.theme.fonts['status'],
            text_color=self.theme.colors['info']
        )
        self.weather_label.pack()
    
    def _create_left_column(self):
        """Create left column with AI and Weather panels"""
        left_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.theme.colors['bg_panel'],
            corner_radius=8
        )
        left_frame.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(10, 5), pady=5)
        
        # AI Panel
        if self.config.SHOW_AI_PANEL and self.ai_manager:
            self.ai_panel = AIPanel(
                left_frame,
                ai_manager=self.ai_manager,
                theme=self.theme,
                send_callback=self._on_ai_message
            )
            self.ai_panel.pack(fill="both", expand=True, pady=(0, 10))
        
        # Weather Panel
        if self.config.SHOW_WEATHER_PANEL and self.weather_service:
            self.weather_panel = WeatherPanel(
                left_frame,
                weather_service=self.weather_service,
                theme=self.theme,
                refresh_callback=self._on_weather_refresh
            )
            self.weather_panel.pack(fill="both", expand=True)
    
    def _create_center_column(self):
        """Create center column with chat and controls"""
        center_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.theme.colors['bg_panel'],
            corner_radius=8
        )
        center_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        # Chat Panel
        self.chat_panel = ChatPanel(
            center_frame,
            theme=self.theme,
            send_callback=self._on_chat_message,
            voice_callback=self._toggle_voice,
            ai_callback=self._on_ai_request
        )
        self.chat_panel.pack(fill="both", expand=True, pady=(0, 10))
        
        # Gesture Panel (if enabled)
        if self.config.SHOW_GESTURE_PANEL and self.gesture_controller:
            self.gesture_panel = GesturePanel(
                center_frame,
                gesture_controller=self.gesture_controller,
                theme=self.theme,
                start_callback=self._on_gesture_start,
                stop_callback=self._on_gesture_stop
            )
            self.gesture_panel.pack(fill="both", expand=True)
    
    def _create_right_column(self):
        """Create right column with system info"""
        right_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.theme.colors['bg_panel'],
            corner_radius=8
        )
        right_frame.grid(row=1, column=2, rowspan=2, sticky="nsew", padx=(5, 10), pady=5)
        
        # System Metrics
        metrics_frame = self._create_panel(right_frame, "SYSTEM METRICS", height=250)
        metrics_frame.pack(fill="both", expand=True, pady=(0, 10))
        self._create_performance_gauges(metrics_frame)
        
        # PizzaINT Widget
        self._create_pizzint_widget(right_frame)
        
        # Module Panel
        if self.config.SHOW_MODULE_PANEL:
            module_frame = self._create_panel(right_frame, "ACTIVE MODULES", height=200)
            module_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            self.module_panel = ModulePanel(
                module_frame,
                module_manager=self.module_manager,
                theme=self.theme
            )
            self.module_panel.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Datastream
        stream_frame = self._create_panel(right_frame, "DATA STREAM", height=150)
        stream_frame.pack(fill="both", expand=True)
        
        self.data_stream = DataStreamVisualization(stream_frame, width=280, height=120)
        self.data_stream.pack(pady=10)
    
    def _create_bottom_bar(self):
        """Create bottom control bar"""
        bottom_frame = ctk.CTkFrame(
            self.main_container,
            height=80,
            fg_color=self.theme.colors['bg_medium'],
            corner_radius=0
        )
        bottom_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        bottom_frame.grid_propagate(False)
        
        # Control buttons
        controls_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        controls_frame.pack(side="left", padx=20, pady=10)
        self._create_control_buttons(controls_frame)
        
        # Alert panel
        alert_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        alert_frame.pack(side="left", padx=20, pady=10, expand=True)
        
        self.alert_panel = AlertPanel(alert_frame, max_alerts=3, theme=self.theme)
        self.alert_panel.pack(fill="both", expand=True)
        
        # System info
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
    
    def _create_performance_gauges(self, parent):
        """Create performance gauges"""
        gauges_frame = ctk.CTkFrame(parent, fg_color="transparent")
        gauges_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure grid for gauges (2x2)
        for i in range(2):
            gauges_frame.grid_rowconfigure(i, weight=1)
            gauges_frame.grid_columnconfigure(i, weight=1)
        
        # Create gauges
        self.cpu_gauge = CircularGauge(
            gauges_frame,
            title="CPU",
            value=self.metrics['cpu_usage'],
            max_value=100,
            unit="%",
            size=80,
            theme=self.theme
        )
        self.cpu_gauge.grid(row=0, column=0, padx=5, pady=5)
        
        self.memory_gauge = CircularGauge(
            gauges_frame,
            title="MEM",
            value=self.metrics['memory_usage'],
            max_value=100,
            unit="%",
            size=80,
            theme=self.theme
        )
        self.memory_gauge.grid(row=0, column=1, padx=5, pady=5)
        
        self.ai_gauge = CircularGauge(
            gauges_frame,
            title="AI",
            value=self.metrics.get('ai_requests', 0),
            max_value=100,
            unit="req",
            size=80,
            theme=self.theme
        )
        self.ai_gauge.grid(row=1, column=0, padx=5, pady=5)
        
        self.network_gauge = CircularGauge(
            gauges_frame,
            title="NET",
            value=self.metrics['network_speed'],
            max_value=100,
            unit="%",
            size=80,
            theme=self.theme
        )
        self.network_gauge.grid(row=1, column=1, padx=5, pady=5)
    
    def _create_pizzint_widget(self, parent):
        """Cria o widget monitor do Pizza Meter"""
        frame = ctk.CTkFrame(parent, fg_color=self.theme.colors['bg_dark'], border_width=1, border_color="#FF5555")
        frame.pack(fill="x", pady=5, padx=5)
        
        # Título
        lbl_title = ctk.CTkLabel(frame, text="🍕 OSINT / PIZZA METER", 
                                font=self.theme.fonts['monospace_small'], text_color="#FF5555")
        lbl_title.pack(anchor="w", padx=5, pady=2)
        
        # Valor e Status
        self.pizzint_value_label = ctk.CTkLabel(frame, text="WAITING DATA...", 
                                               font=("Arial", 20, "bold"), text_color="white")
        self.pizzint_value_label.pack(pady=5)
        
        self.pizzint_status_label = ctk.CTkLabel(frame, text="NORMAL ACTIVITY", 
                                                font=self.theme.fonts['monospace_small'], text_color="gray")
        self.pizzint_status_label.pack(pady=(0,5))

    def _create_control_buttons(self, parent):
        """Create control buttons"""
        buttons = [
            ("🎤 VOICE", self._toggle_voice, self.theme.colors['primary']),
            ("🧠 AI", self._toggle_ai, self.theme.colors['accent']),
            ("🌤️ WEATHER", self._refresh_weather, self.theme.colors['info']),
            ("👋 GESTURES", self._toggle_gestures, self.theme.colors['secondary']),
            ("🌐 WEB", self._toggle_web_dashboard, self.theme.colors['warning']),
            ("⚙️ SETTINGS", self._open_settings, self.theme.colors['text_dim']),
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
            btn.pack(side="left", padx=2)
            
            if text == "🎤 VOICE":
                self.voice_control_button = btn
            elif text == "🧠 AI":
                self.ai_control_button = btn
            elif text == "👋 GESTURES":
                self.gesture_control_button = btn
    
    def _create_system_info(self, parent):
        """Create system information display"""
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack()
        
        self.time_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=self.theme.fonts['monospace_small'],
            text_color=self.theme.colors['text_dim']
        )
        self.time_label.pack()
        
        self.version_label = ctk.CTkLabel(
            info_frame,
            text="V2.1",
            font=self.theme.fonts['monospace_small'],
            text_color=self.theme.colors['primary']
        )
        self.version_label.pack()
    
    def _start_system(self):
        """Start system components"""
        print("🚀 Starting R2 Assistant V2.1...")
        
        # Add startup messages
        self._add_chat_message("SYSTEM", "⚡ R2 Assistant V2.1 inicializando...")
        self._add_chat_message("SYSTEM", "✅ Núcleo do sistema: Online")
        
        if self.ai_manager:
            self._add_chat_message("SYSTEM", "🧠 Integração IA: Pronta")
            # Initialize AI async
            threading.Thread(target=self._init_ai_async, daemon=True).start()
        
        if self.weather_service:
            self._add_chat_message("SYSTEM", "🌤️ Serviço de clima: Ativo")
            # Get initial weather
            threading.Thread(target=self._get_initial_weather, daemon=True).start()
        
        if self.gesture_controller:
            self._add_chat_message("SYSTEM", "👋 Controle por gestos: Disponível")
        
        if self.web_dashboard:
            self._add_chat_message("SYSTEM", "🌐 Dashboard web: Disponível")
        
        self._add_chat_message("R2", "🌌 Sistema V2.1 operacional! Como posso ajudá-lo?")
        
        # Configure and start alert system
        if self.alert_system:
            self.alert_system.notification_callback = self._on_alert_received
            self.alert_system.start_monitoring()
        
        # Start updates
        self._start_updates()
    
    def _init_ai_async(self):
        """Initialize AI asynchronously"""
        import asyncio
        
        async def init():
            try:
                await self.ai_manager.initialize()
                self.after(0, self._update_ai_status, True)
                self._add_chat_message("SYSTEM", "✅ IA: Conectada e pronta")
            except Exception as e:
                self.after(0, self._update_ai_status, False)
                self._add_chat_message("SYSTEM", f"⚠️ IA: Modo offline - {e}")
        
        asyncio.run(init())
    
    def _get_initial_weather(self):
        """Get initial weather data"""
        if self.weather_service:
            try:
                # Try to get weather for default location
                weather_data = asyncio.run(self.weather_service.get_weather("São Paulo"))
                if weather_data:
                    self.after(0, self._update_weather_display, weather_data)
            except:
                pass
    
    def _start_updates(self):
        """Start periodic UI updates"""
        self._update_time()
        self._update_metrics()
        self._update_datastream()
        self._update_system_status()
        
        print("✅ UI updates started")
    
    # Event Handlers
    def _on_chat_message(self, message: str):
        """Handle chat message"""
        if not message:
            return
        
        self._add_chat_message("YOU", message)
        
        # Process command if starts with /
        if message.startswith('/'):
            command = message[1:]
            threading.Thread(
                target=self._process_command,
                args=(command,),
                daemon=True
            ).start()
        else:
            # Regular chat - use AI if available
            threading.Thread(
                target=self._process_ai_chat,
                args=(message,),
                daemon=True
            ).start()
    
    def _on_ai_message(self, message: str):
        """Handle AI panel message"""
        self._add_chat_message("AI", message)
    
    def _on_ai_request(self, prompt: str):
        """Handle AI request from chat"""
        if self.ai_manager:
            threading.Thread(
                target=self._process_ai_request,
                args=(prompt,),
                daemon=True
            ).start()
        else:
            self._add_chat_message("SYSTEM", "IA não disponível no momento")
    
    def _on_weather_refresh(self, location: str):
        """Handle weather refresh request"""
        if self.weather_service:
            threading.Thread(
                target=self._process_weather_request,
                args=(location,),
                daemon=True
            ).start()
    
    def _on_gesture_start(self):
        """Start gesture recognition"""
        if self.gesture_controller:
            try:
                self.gesture_controller.start()
                self._add_chat_message("SYSTEM", "👋 Reconhecimento de gestos iniciado")
            except Exception as e:
                self._add_chat_message("SYSTEM", f"❌ Erro ao iniciar gestos: {e}")
    
    def _on_gesture_stop(self):
        """Stop gesture recognition"""
        if self.gesture_controller:
            self.gesture_controller.stop()
            self._add_chat_message("SYSTEM", "🛑 Reconhecimento de gestos parado")
    
    def _process_command(self, command: str):
        """Process system command"""
        try:
            success, result = self.command_system.process_command(command)
            
            if success:
                self.after(0, self._add_chat_message, "SYSTEM", result)
            else:
                self.after(0, self._add_chat_message, "SYSTEM", f"❌ {result}")
                
        except Exception as e:
            self.after(0, self._add_chat_message, "SYSTEM", f"💥 Erro: {e}")
    
    def _process_ai_chat(self, message: str):
        """Process chat with AI"""
        if not self.ai_manager:
            self.after(0, self._add_chat_message, "R2", 
                      "Desculpe, o serviço de IA não está disponível no momento.")
            return
        
        try:
            import asyncio
            
            async def get_response():
                response = await self.ai_manager.chat(
                    user_id="main",
                    message=message
                )
                return response
            
            response = asyncio.run(get_response())
            
            self.after(0, self._add_chat_message, "R2", response.content)
            self.metrics['ai_requests'] += 1
            
        except Exception as e:
            self.after(0, self._add_chat_message, "R2", 
                      f"Desculpe, ocorreu um erro: {str(e)}")
    
    def _process_ai_request(self, prompt: str):
        """Process AI request"""
        if self.ai_manager:
            try:
                import asyncio
                
                async def process():
                    response = await self.ai_manager.chat(
                        user_id="request",
                        message=prompt,
                        use_history=False
                    )
                    return response
                
                response = asyncio.run(process())
                self.after(0, self._add_chat_message, "AI", response.content)
                self.metrics['ai_requests'] += 1
                
            except Exception as e:
                self.after(0, self._add_chat_message, "SYSTEM", f"Erro IA: {e}")
    
    def _process_weather_request(self, location: str):
        """Process weather request"""
        if self.weather_service:
            try:
                import asyncio
                
                async def get_weather():
                    return await self.weather_service.get_weather(location)
                
                weather_data = asyncio.run(get_weather())
                
                if weather_data:
                    message = self.weather_service.format_weather_message(weather_data)
                    self.after(0, self._add_chat_message, "WEATHER", message)
                    self.after(0, self._update_weather_display, weather_data)
                    self.metrics['weather_requests'] += 1
                else:
                    self.after(0, self._add_chat_message, "WEATHER", 
                              "Não foi possível obter dados do tempo.")
                    
            except Exception as e:
                self.after(0, self._add_chat_message, "WEATHER", f"Erro: {e}")
    
    # Control button handlers
    def _toggle_voice(self):
        """Toggle voice recognition"""
        self.voice_active = not self.voice_active
        
        if self.voice_active:
            self.voice_control_button.configure(
                text="🔴 VOICE ACTIVE",
                fg_color=self.theme.colors['danger']
            )
            self._add_chat_message("SYSTEM", "🎤 Reconhecimento de voz ativado")
            
            if self.voice_engine:
                self.voice_engine.start_listening(self._on_voice_command)
        else:
            self.voice_control_button.configure(
                text="🎤 VOICE",
                fg_color=self.theme.colors['primary']
            )
            self._add_chat_message("SYSTEM", "🎤 Reconhecimento de voz desativado")
            
            if self.voice_engine:
                self.voice_engine.stop_listening()
    
    def _toggle_ai(self):
        """Toggle AI panel visibility"""
        if hasattr(self, 'ai_panel'):
            if self.ai_panel.winfo_ismapped():
                self.ai_panel.pack_forget()
                self.ai_control_button.configure(text="🧠 SHOW AI")
            else:
                self.ai_panel.pack(fill="both", expand=True, pady=(0, 10))
                self.ai_control_button.configure(text="🧠 HIDE AI")
    
    def _refresh_weather(self):
        """Refresh weather display"""
        if hasattr(self, 'weather_panel'):
            self.weather_panel.refresh()
    
    def _toggle_gestures(self):
        """Toggle gesture control"""
        if self.gesture_controller:
            if self.gesture_controller.is_running:
                self._on_gesture_stop()
                self.gesture_control_button.configure(
                    text="👋 START GESTURES",
                    fg_color=self.theme.colors['secondary']
                )
            else:
                self._on_gesture_start()
                self.gesture_control_button.configure(
                    text="🛑 STOP GESTURES",
                    fg_color=self.theme.colors['danger']
                )
    
    def _toggle_web_dashboard(self):
        """Toggle web dashboard"""
        if self.web_dashboard:
            if self.web_dashboard.is_running:
                self.web_dashboard.stop()
                self._add_chat_message("SYSTEM", "🌐 Dashboard web parado")
            else:
                self.web_dashboard.start()
                self._add_chat_message("SYSTEM", f"🌐 Dashboard web iniciado em http://{self.config.WEB_HOST}:{self.config.WEB_PORT}")
    
    def _open_settings(self):
        """Open settings window"""
        from .windows.settings_window import SettingsWindow
        SettingsWindow(self, self.config)
    
    # Update methods
    def _update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=f"TIME: {current_time}")
        self.after(1000, self._update_time)
    
    def _update_metrics(self):
        """Atualiza interface com DADOS REAIS"""
        try:
            import psutil
            
            # --- 1. MONITORAMENTO CPU (NÚCLEO AI) ---
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            # Atualiza gráficos numéricos
            self.metrics['cpu_usage'] = cpu
            self.metrics['memory_usage'] = ram
            self.cpu_gauge.set_value(cpu)
            
            # >>> AQUI: O Anel Central reage à CPU <<<
            if hasattr(self, 'wave_animation'): # Ou o nome do seu widget do Núcleo AI
                self.wave_animation.set_load_level(cpu)

            # --- 2. MONITORAMENTO DE REDE (MATRIX RAIN) ---
            net = psutil.net_io_counters()
            # Calcula velocidade em MB/s (diferença desde a última checagem)
            bytes_recv = net.bytes_recv
            if hasattr(self, '_last_bytes_recv'):
                speed = (bytes_recv - self._last_bytes_recv) / 1024 / 1024 # MB
                
                # >>> AQUI: Chuva de dados reage à velocidade <<<
                # Se speed > 1MB/s, chuva rápida. Se 0, lenta.
                rain_speed = min(10, max(1, int(speed * 5))) 
                if hasattr(self, 'data_stream'): # Widget Fluxo de Dados
                    self.data_stream.set_speed(rain_speed) 
            
            self._last_bytes_recv = bytes_recv

            # --- 3. PIZZAINT OSINT (RADAR) ---
            if self.pizzint_service:
                is_anomaly, msg = self.pizzint_service.check_anomaly()
                status = self.pizzint_service.get_status()
                orders = status['level']

                # >>> AQUI: Radar mostra "inimigos" se houver pico de pizza <<<
                if hasattr(self, 'radar_view'): # Widget Radar
                    if is_anomaly:
                        # Adiciona blips vermelhos agressivos
                        self.radar_view.add_threat(intensity=1.0)
                        self.radar_view.configure(bg="#1a0000") # Fundo levemente vermelho
                    elif orders > 45: 
                        # Adiciona blips amarelos de alerta
                        if random.random() < 0.1:
                            self.radar_view.add_threat(intensity=0.3)
                        self.radar_view.configure(bg="black")

        except Exception as e:
            print(f"Erro update metrics: {e}")
        
        # Chama a função novamente em 1 segundo (1000ms)
        self.after(1000, self._update_metrics)
    
    def _update_datastream(self):
        """Update datastream visualization"""
        try:
            value = random.uniform(0, 100)
            self.data_stream.add_data_point(value)
        except:
            pass
        
        self.after(100, self._update_datastream)
    
    def _update_system_status(self):
        """Update system status display"""
        try:
            # Update AI status
            if self.ai_manager and self.ai_manager.active:
                self.ai_status_label.configure(
                    text="🧠 AI: ONLINE",
                    text_color=self.theme.colors['success']
                )
            else:
                self.ai_status_label.configure(
                    text="🧠 AI: OFFLINE",
                    text_color=self.theme.colors['warning']
                )
            
        except:
            pass
        
        self.after(5000, self._update_system_status)
    
    def _update_ai_status(self, online: bool):
        """Update AI status display"""
        if online:
            self.ai_status_label.configure(
                text="🧠 AI: ONLINE",
                text_color=self.theme.colors['success']
            )
        else:
            self.ai_status_label.configure(
                text="🧠 AI: OFFLINE",
                text_color=self.theme.colors['warning']
            )
    
    def _update_weather_display(self, weather_data):
        """Update weather display"""
        if weather_data:
            temp = weather_data.current.temperature
            self.weather_label.configure(text=f"🌤️ {temp:.0f}°C")
    
    def _add_chat_message(self, sender: str, message: str):
        """Add message to chat display"""
        if hasattr(self, 'chat_panel'):
            self.chat_panel.add_message(sender, message)
    
    def _on_alert_received(self, alert_data: Dict[str, Any]):
        """Handle alert received"""
        self.after(0, self._on_alert_received_thread_safe, alert_data)
    
    def _on_alert_received_thread_safe(self, alert_data: Dict[str, Any]):
        """Thread-safe alert handler"""
        if hasattr(self, 'alert_panel'):
            self.alert_panel.add_alert(alert_data)
            self._add_chat_message("ALERT", alert_data.get('message', 'Novo alerta'))
    
    def _on_voice_command(self, command: str):
        """Handle voice command"""
        self.after(0, self._add_chat_message, "YOU (VOICE)", command)
        self.after(0, lambda: self._process_command(command))
    
    def _create_simple_interface(self):
        """Create simple fallback interface"""
        # Implementation similar to original but updated
        pass
    
    def run(self):
        """Run the application"""
        self.mainloop()
    
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up...")
        
        if self.voice_engine and self.voice_active:
            self.voice_engine.stop_listening()
        
        if self.alert_system:
            self.alert_system.stop_monitoring()
        
        if self.gesture_controller:
            self.gesture_controller.stop()
        
        if self.web_dashboard:
            self.web_dashboard.stop()