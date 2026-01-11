"""
Solar Monitor - Monitoramento em tempo real de atividade solar
Dashboard e alertas para eventos solares significativos
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import asyncio
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from .noaa_service import NOAAService, SpaceWeatherData, SolarFlare, GeomagneticStorm, AlertLevel

logger = logging.getLogger(__name__)

@dataclass
class SolarActivity:
    """Atividade solar consolidada para monitoramento"""
    timestamp: datetime
    flare_probability: float  # 0-100%
    cme_probability: float    # 0-100% (Coronal Mass Ejection)
    active_regions: int
    sunspot_number: int
    solar_flux: float  # Fluxo solar em SFU
    rotation_phase: float  # Fase da rotação solar (0-1)
    activity_trend: str  # 'increasing', 'decreasing', 'stable'
    
    @property
    def overall_activity(self) -> str:
        """Nível geral de atividade solar"""
        if self.flare_probability > 70 or self.cme_probability > 70:
            return "high"
        elif self.flare_probability > 40 or self.cme_probability > 40:
            return "moderate"
        else:
            return "low"

@dataclass
class MonitorAlert:
    """Alerta do sistema de monitoramento"""
    id: str
    type: str  # 'flare', 'cme', 'storm', 'radiation'
    level: AlertLevel
    message: str
    timestamp: datetime
    expires: Optional[datetime] = None
    acknowledged: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Verifica se o alerta ainda está ativo"""
        if self.expires:
            return datetime.now() < self.expires
        return not self.acknowledged

class SolarMonitor:
    """
    Sistema de monitoramento solar em tempo real
    Interface gráfica com dashboard e alertas
    """
    
    def __init__(self, parent, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o monitor solar
        
        Args:
            parent: Widget pai (Tkinter)
            config: Configuração do monitor
        """
        self.parent = parent
        self.config = config or {}
        
        # Serviço NOAA
        self.noaa_service = NOAAService(self.config.get('noaa', {}))
        self.noaa_service.register_alert_callback(self._handle_noaa_alert)
        
        # Dados atuais
        self.current_weather: Optional[SpaceWeatherData] = None
        self.current_activity: Optional[SolarActivity] = None
        self.historical_data: List[SpaceWeatherData] = []
        
        # Alertas
        self.alerts: List[MonitorAlert] = []
        self.max_alerts = 50
        
        # Estado do monitor
        self.is_monitoring = False
        self.update_interval = self.config.get('update_interval', 300)  # 5 minutos
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Cores para tema Sci-Fi/HUD
        self.colors = {
            'bg_dark': '#0a0a12',
            'bg_medium': '#121225',
            'bg_light': '#1a1a35',
            'accent_blue': '#00ccff',
            'accent_purple': '#9d00ff',
            'accent_green': '#00ffaa',
            'accent_red': '#ff3366',
            'accent_orange': '#ff9900',
            'accent_yellow': '#ffff00',
            'text_primary': '#ffffff',
            'text_secondary': '#a0a0c0',
            'border': '#2a2a4a',
            'alert_severe': '#ff3366',
            'alert_warning': '#ff9900',
            'alert_watch': '#ffff00',
            'alert_normal': '#00ccff'
        }
        
        # Fontes
        self.fonts = {
            'title': ('Segoe UI', 16, 'bold'),
            'heading': ('Segoe UI', 12, 'bold'),
            'normal': ('Segoe UI', 10),
            'small': ('Segoe UI', 9),
            'mono': ('Consolas', 9)
        }
        
        # Configurar matplotlib
        plt.style.use('dark_background')
        self.setup_matplotlib_style()
        
        # Inicializar interface
        self.setup_ui()
        
        # Iniciar monitoramento
        self.start_monitoring()
        
        logger.info("Solar Monitor inicializado")
    
    def setup_matplotlib_style(self):
        """Configura estilo do matplotlib para tema Sci-Fi"""
        matplotlib.rcParams.update({
            'figure.facecolor': self.colors['bg_dark'],
            'axes.facecolor': self.colors['bg_medium'],
            'axes.edgecolor': self.colors['border'],
            'axes.labelcolor': self.colors['text_primary'],
            'axes.titlecolor': self.colors['accent_blue'],
            'xtick.color': self.colors['text_secondary'],
            'ytick.color': self.colors['text_secondary'],
            'grid.color': self.colors['border'],
            'text.color': self.colors['text_primary'],
            'lines.linewidth': 2,
            'grid.alpha': 0.3
        })
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal
        self.main_frame = tk.Frame(
            self.parent,
            bg=self.colors['bg_dark'],
            padx=10,
            pady=10
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Layout principal
        self.main_frame.grid_columnconfigure(0, weight=3)  # Esquerda: Gráficos
        self.main_frame.grid_columnconfigure(1, weight=1)  # Direita: Status
        self.main_frame.grid_rowconfigure(0, weight=1)     # Conteúdo principal
        
        # Painel esquerdo - Gráficos e métricas
        self.left_panel = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark']
        )
        self.left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # Painel direito - Status e alertas
        self.right_panel = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark']
        )
        self.right_panel.grid(row=0, column=1, sticky='nsew')
        
        # Criar componentes
        self.create_header()
        self.create_metrics_panel()
        self.create_charts_panel()
        self.create_status_panel()
        self.create_alerts_panel()
        
    def create_header(self):
        """Cria cabeçalho do monitor"""
        header_frame = tk.Frame(
            self.left_panel,
            bg=self.colors['bg_dark']
        )
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Título com ícone
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        title_frame.pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="☀️",
            font=('Segoe UI', 32),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_yellow']
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="MONITOR SOLAR - R2 ASSISTANT",
            font=self.fonts['title'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=10)
        
        # Controles
        controls_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        controls_frame.pack(side=tk.RIGHT)
        
        control_buttons = [
            ("🔄 Atualizar", self.force_update),
            ("⏸️ Pausar", self.toggle_monitoring),
            ("📊 Relatório", self.generate_report),
            ("⚙️ Config", self.open_settings)
        ]
        
        for text, command in control_buttons:
            btn = tk.Button(
                controls_frame,
                text=text,
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_blue'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                padx=12,
                pady=5,
                command=command
            )
            btn.pack(side=tk.LEFT, padx=2)
    
    def create_metrics_panel(self):
        """Cria painel de métricas principais"""
        metrics_frame = tk.Frame(
            self.left_panel,
            bg=self.colors['bg_medium'],
            relief=tk.RAISED,
            borderwidth=1
        )
        metrics_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            metrics_frame,
            text="MÉTRICAS SOLARES",
            font=self.fonts['heading'],
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_blue'],
            pady=10
        ).pack()
        
        # Grid de métricas (2x3)
        self.metrics_grid = tk.Frame(metrics_frame, bg=self.colors['bg_medium'])
        self.metrics_grid.pack(padx=10, pady=(0, 10))
        
        # Métricas a serem exibidas
        self.metric_widgets = {}
        metrics_config = [
            ('flare_index', 'Índice de Flares', 'N/A', self.colors['accent_red']),
            ('kp_index', 'Índice Kp', 'N/A', self.colors['accent_purple']),
            ('wind_speed', 'Vento Solar', 'N/A km/s', self.colors['accent_blue']),
            ('sunspots', 'Manchas Solares', 'N/A', self.colors['accent_yellow']),
            ('aurora', 'Aurora', 'N/A%', self.colors['accent_green']),
            ('activity', 'Atividade', 'N/A', self.colors['accent_orange'])
        ]
        
        for i, (key, label, default, color) in enumerate(metrics_config):
            row = i // 3
            col = i % 3
            
            metric_frame = tk.Frame(self.metrics_grid, bg=self.colors['bg_medium'])
            metric_frame.grid(row=row, column=col, padx=10, pady=5, sticky='w')
            
            # Label
            tk.Label(
                metric_frame,
                text=label,
                font=self.fonts['small'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_secondary']
            ).pack(anchor='w')
            
            # Valor
            value_label = tk.Label(
                metric_frame,
                text=default,
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['bg_medium'],
                fg=color
            )
            value_label.pack(anchor='w', pady=(2, 0))
            
            self.metric_widgets[key] = value_label
    
    def create_charts_panel(self):
        """Cria painel de gráficos"""
        charts_frame = tk.Frame(
            self.left_panel,
            bg=self.colors['bg_medium'],
            relief=tk.SUNKEN,
            borderwidth=2
        )
        charts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Notebook para múltiplos gráficos
        self.charts_notebook = ttk.Notebook(charts_frame)
        self.charts_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Aba 1: Atividade Solar
        self.chart1_frame = tk.Frame(self.charts_notebook, bg=self.colors['bg_medium'])
        self.charts_notebook.add(self.chart1_frame, text="📈 Atividade")
        self.create_solar_activity_chart()
        
        # Aba 2: Vento Solar
        self.chart2_frame = tk.Frame(self.charts_notebook, bg=self.colors['bg_medium'])
        self.charts_notebook.add(self.chart2_frame, text="🌪️ Vento Solar")
        self.create_solar_wind_chart()
        
        # Aba 3: Histórico
        self.chart3_frame = tk.Frame(self.charts_notebook, bg=self.colors['bg_medium'])
        self.charts_notebook.add(self.chart3_frame, text="📜 Histórico")
        self.create_historical_chart()
    
    def create_solar_activity_chart(self):
        """Cria gráfico de atividade solar"""
        # Criar figura matplotlib
        self.activity_fig = Figure(figsize=(8, 4), dpi=100, facecolor=self.colors['bg_medium'])
        self.activity_ax = self.activity_fig.add_subplot(111)
        
        # Configurar eixos vazios inicialmente
        self.activity_ax.set_title('Atividade Solar - Últimas 24h', 
                                  color=self.colors['text_primary'], pad=10)
        self.activity_ax.set_xlabel('Hora', color=self.colors['text_secondary'])
        self.activity_ax.set_ylabel('Intensidade', color=self.colors['text_secondary'])
        self.activity_ax.grid(True, alpha=0.3, linestyle='--')
        
        # Embed no tkinter
        self.activity_canvas = FigureCanvasTkAgg(self.activity_fig, self.chart1_frame)
        self.activity_canvas.draw()
        self.activity_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_solar_wind_chart(self):
        """Cria gráfico de vento solar"""
        self.wind_fig = Figure(figsize=(8, 4), dpi=100, facecolor=self.colors['bg_medium'])
        self.wind_ax = self.wind_fig.add_subplot(111)
        
        self.wind_ax.set_title('Vento Solar - Parâmetros', 
                              color=self.colors['text_primary'], pad=10)
        self.wind_ax.set_xlabel('Tempo', color=self.colors['text_secondary'])
        self.wind_ax.set_ylabel('Valor', color=self.colors['text_secondary'])
        self.wind_ax.grid(True, alpha=0.3, linestyle='--')
        
        self.wind_canvas = FigureCanvasTkAgg(self.wind_fig, self.chart2_frame)
        self.wind_canvas.draw()
        self.wind_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_historical_chart(self):
        """Cria gráfico histórico"""
        self.hist_fig = Figure(figsize=(8, 4), dpi=100, facecolor=self.colors['bg_medium'])
        self.hist_ax = self.hist_fig.add_subplot(111)
        
        self.hist_ax.set_title('Histórico - Índice Kp (7 dias)', 
                              color=self.colors['text_primary'], pad=10)
        self.hist_ax.set_xlabel('Data', color=self.colors['text_secondary'])
        self.hist_ax.set_ylabel('Kp Index', color=self.colors['text_secondary'])
        self.hist_ax.grid(True, alpha=0.3, linestyle='--')
        
        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, self.chart3_frame)
        self.hist_canvas.draw()
        self.hist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_status_panel(self):
        """Cria painel de status do sistema"""
        status_frame = tk.Frame(
            self.right_panel,
            bg=self.colors['bg_medium'],
            relief=tk.RAISED,
            borderwidth=1
        )
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            status_frame,
            text="STATUS DO SISTEMA",
            font=self.fonts['heading'],
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_blue'],
            pady=10
        ).pack()
        
        # Informações de status
        self.status_vars = {}
        status_items = [
            ('monitor_status', 'Monitoramento:', 'INICIANDO...', self.colors['accent_yellow']),
            ('last_update', 'Última Atualização:', 'Nunca', self.colors['text_secondary']),
            ('next_update', 'Próxima Atualização:', 'Calculando...', self.colors['text_secondary']),
            ('data_source', 'Fonte de Dados:', 'NOAA SWPC', self.colors['accent_green']),
            ('alerts_active', 'Alertas Ativos:', '0', self.colors['accent_red']),
            ('overall_status', 'Status Geral:', 'NORMAL', self.colors['accent_green'])
        ]
        
        for key, label, default, color in status_items:
            item_frame = tk.Frame(status_frame, bg=self.colors['bg_medium'])
            item_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(
                item_frame,
                text=label,
                font=self.fonts['small'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_secondary'],
                width=20,
                anchor='w'
            ).pack(side=tk.LEFT)
            
            value_label = tk.Label(
                item_frame,
                text=default,
                font=self.fonts['small'],
                bg=self.colors['bg_medium'],
                fg=color
            )
            value_label.pack(side=tk.RIGHT)
            
            self.status_vars[key] = value_label
    
    def create_alerts_panel(self):
        """Cria painel de alertas"""
        alerts_frame = tk.Frame(
            self.right_panel,
            bg=self.colors['bg_medium'],
            relief=tk.SUNKEN,
            borderwidth=2
        )
        alerts_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            alerts_frame,
            text="ALERTAS ATIVOS",
            font=self.fonts['heading'],
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_blue'],
            pady=10
        ).pack()
        
        # Canvas para scroll de alertas
        self.alerts_canvas = tk.Canvas(
            alerts_frame,
            bg=self.colors['bg_medium'],
            highlightthickness=0
        )
        
        scrollbar = ttk.Scrollbar(
            alerts_frame,
            orient=tk.VERTICAL,
            command=self.alerts_canvas.yview
        )
        
        self.alerts_content = tk.Frame(
            self.alerts_canvas,
            bg=self.colors['bg_medium']
        )
        
        self.alerts_content.bind(
            "<Configure>",
            lambda e: self.alerts_canvas.configure(scrollregion=self.alerts_canvas.bbox("all"))
        )
        
        self.alerts_canvas.create_window(
            (0, 0),
            window=self.alerts_content,
            anchor="nw"
        )
        
        self.alerts_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.alerts_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar scroll com mouse
        self.alerts_canvas.bind_all("<MouseWheel>", self._on_alerts_scroll)
        
        # Label para nenhum alerta
        self.no_alerts_label = tk.Label(
            self.alerts_content,
            text="Nenhum alerta ativo",
            font=self.fonts['normal'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary'],
            pady=20
        )
        self.no_alerts_label.pack()
    
    def _on_alerts_scroll(self, event):
        """Manipula scroll do mouse no canvas de alertas"""
        self.alerts_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def start_monitoring(self):
        """Inicia o monitoramento em background"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.status_vars['monitor_status'].config(
            text="ATIVO",
            fg=self.colors['accent_green']
        )
        
        logger.info("Monitoramento solar iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.status_vars['monitor_status'].config(
            text="PAUSADO",
            fg=self.colors['accent_orange']
        )
        
        logger.info("Monitoramento solar pausado")
    
    def toggle_monitoring(self):
        """Alterna estado do monitoramento"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        import time
        
        while self.is_monitoring:
            try:
                # Atualizar dados
                self.update_data()
                
                # Atualizar interface na thread principal
                self.parent.after(0, self.update_ui)
                
                # Calcular próxima atualização
                next_update = time.time() + self.update_interval
                
                # Aguardar até próxima atualização
                while self.is_monitoring and time.time() < next_update:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(30)  # Esperar antes de tentar novamente
    
    async def _fetch_data_async(self):
        """Busca dados de forma assíncrona"""
        try:
            # Obter dados atuais
            weather_data = await self.noaa_service.get_space_weather()
            
            if weather_data:
                self.current_weather = weather_data
                
                # Calcular atividade solar
                self.current_activity = self._calculate_solar_activity(weather_data)
                
                # Adicionar ao histórico (mantém apenas últimas 100 entradas)
                self.historical_data.append(weather_data)
                if len(self.historical_data) > 100:
                    self.historical_data = self.historical_data[-100:]
                
                logger.debug(f"Dados atualizados: {weather_data.overall_alert.value}")
                return True
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados: {e}")
        
        return False
    
    def update_data(self):
        """Atualiza dados (chamado da thread de monitoramento)"""
        try:
            # Criar novo loop de evento para thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Executar busca assíncrona
            success = loop.run_until_complete(self._fetch_data_async())
            loop.close()
            
            if success:
                self._last_update_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Erro na atualização de dados: {e}")
    
    def _calculate_solar_activity(self, weather_data: SpaceWeatherData) -> SolarActivity:
        """Calcula métricas de atividade solar baseado nos dados"""
        # Calcular probabilidade de flare
        flare_prob = 0.0
        if weather_data.solar_flares:
            max_flare_intensity = max(f.intensity_log for f in weather_data.solar_flares)
            flare_prob = min(max_flare_intensity * 20, 100)  # Escala aproximada
        
        # Calcular probabilidade de CME
        cme_prob = 0.0
        if weather_data.solar_wind.speed > 600:
            cme_prob = min((weather_data.solar_wind.speed - 600) / 2, 50)
        if weather_data.solar_flares:
            cme_prob += len([f for f in weather_data.solar_flares if f.class_value.value in ['M', 'X']]) * 10
        
        # Determinar tendência
        if len(self.historical_data) >= 2:
            recent_kp = [d.kp_index for d in self.historical_data[-5:]]
            if len(recent_kp) >= 2:
                if recent_kp[-1] > recent_kp[0] * 1.2:
                    trend = "increasing"
                elif recent_kp[-1] < recent_kp[0] * 0.8:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return SolarActivity(
            timestamp=datetime.now(),
            flare_probability=min(flare_prob, 100),
            cme_probability=min(cme_prob, 100),
            active_regions=len(set(f.active_region for f in weather_data.solar_flares if f.active_region)),
            sunspot_number=int(weather_data.solar_wind.density * 10),  # Aproximação
            solar_flux=weather_data.electron_flux / 100,  # Aproximação
            rotation_phase=(datetime.now().timetuple().tm_yday % 27) / 27,  # Rotação solar ~27 dias
            activity_trend=trend
        )
    
    def update_ui(self):
        """Atualiza todos os elementos da interface"""
        if not self.current_weather or not self.current_activity:
            return
        
        # Atualizar métricas
        self._update_metrics()
        
        # Atualizar gráficos
        self._update_charts()
        
        # Atualizar status
        self._update_status()
        
        # Atualizar alertas
        self._update_alerts()
    
    def _update_metrics(self):
        """Atualiza os widgets de métricas"""
        if not self.current_weather or not self.current_activity:
            return
        
        # Índice de flares
        if self.current_weather.solar_flares:
            max_flare = max(self.current_weather.solar_flares, key=lambda f: f.intensity)
            flare_text = f"{max_flare.class_value.value}{max_flare.intensity_log:.1f}"
            self.metric_widgets['flare_index'].config(text=flare_text)
        else:
            self.metric_widgets['flare_index'].config(text="Nenhum")
        
        # Índice Kp
        kp_color = self.colors['accent_green']
        if self.current_weather.kp_index >= 5:
            kp_color = self.colors['accent_red']
        elif self.current_weather.kp_index >= 4:
            kp_color = self.colors['accent_orange']
        
        self.metric_widgets['kp_index'].config(
            text=f"{self.current_weather.kp_index:.1f}",
            fg=kp_color
        )
        
        # Vento solar
        wind_speed = self.current_weather.solar_wind.speed
        wind_color = self.colors['accent_green']
        if wind_speed > 600:
            wind_color = self.colors['accent_red']
        elif wind_speed > 500:
            wind_color = self.colors['accent_orange']
        
        self.metric_widgets['wind_speed'].config(
            text=f"{wind_speed:.0f} km/s",
            fg=wind_color
        )
        
        # Manchas solares
        self.metric_widgets['sunspots'].config(
            text=str(self.current_activity.sunspot_number)
        )
        
        # Aurora
        aurora_prob = self.current_weather.aurora_probability.get('auroral', 0) * 100
        aurora_color = self.colors['accent_green']
        if aurora_prob > 50:
            aurora_color = self.colors['accent_purple']
        
        self.metric_widgets['aurora'].config(
            text=f"{aurora_prob:.0f}%",
            fg=aurora_color
        )
        
        # Atividade geral
        activity_level = self.current_activity.overall_activity
        activity_color = {
            'high': self.colors['accent_red'],
            'moderate': self.colors['accent_orange'],
            'low': self.colors['accent_green']
        }.get(activity_level, self.colors['text_secondary'])
        
        activity_text = {
            'high': 'ALTA',
            'moderate': 'MODERADA',
            'low': 'BAIXA'
        }.get(activity_level, 'DESCONHECIDA')
        
        self.metric_widgets['activity'].config(
            text=activity_text,
            fg=activity_color
        )
    
    def _update_charts(self):
        """Atualiza todos os gráficos"""
        self._update_activity_chart()
        self._update_wind_chart()
        self._update_historical_chart()
    
    def _update_activity_chart(self):
        """Atualiza gráfico de atividade solar"""
        if not self.historical_data:
            return
        
        self.activity_ax.clear()
        
        # Preparar dados das últimas 24 horas
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_data = [d for d in self.historical_data if d.timestamp > cutoff_time]
        
        if not recent_data:
            return
        
        times = [d.timestamp for d in recent_data]
        kp_values = [d.kp_index for d in recent_data]
        
        # Plotar
        self.activity_ax.plot(times, kp_values, 
                            color=self.colors['accent_blue'],
                            linewidth=2,
                            label='Kp Index')
        
        # Adicionar áreas de alerta
        self.activity_ax.axhspan(5, 9, alpha=0.2, color=self.colors['accent_red'], label='Tempestade')
        self.activity_ax.axhspan(4, 5, alpha=0.2, color=self.colors['accent_orange'], label='Alerta')
        
        # Configurar gráfico
        self.activity_ax.set_title('Atividade Solar - Últimas 24h', 
                                  color=self.colors['text_primary'], pad=10)
        self.activity_ax.set_xlabel('Hora', color=self.colors['text_secondary'])
        self.activity_ax.set_ylabel('Índice Kp', color=self.colors['text_secondary'])
        self.activity_ax.grid(True, alpha=0.3, linestyle='--')
        self.activity_ax.legend(loc='upper right')
        
        # Formatar eixo x
        self.activity_fig.autofmt_xdate()
        self.activity_canvas.draw()
    
    def _update_wind_chart(self):
        """Atualiza gráfico de vento solar"""
        if not self.historical_data:
            return
        
        self.wind_ax.clear()
        
        # Dados mais recentes
        recent_data = self.historical_data[-20:]  # Últimas 20 medições
        
        times = [d.timestamp for d in recent_data]
        speeds = [d.solar_wind.speed for d in recent_data]
        densities = [d.solar_wind.density for d in recent_data]
        
        # Normalizar densidades para mesma escala
        if densities:
            max_density = max(densities)
            if max_density > 0:
                densities = [d/max_density * max(speeds) for d in densities]
        
        # Plotar
        self.wind_ax.plot(times, speeds, 
                         color=self.colors['accent_blue'],
                         linewidth=2,
                         label='Velocidade (km/s)')
        
        if densities:
            self.wind_ax.plot(times, densities,
                            color=self.colors['accent_green'],
                            linewidth=2,
                            linestyle='--',
                            label='Densidade (normalizada)')
        
        # Linha de referência
        self.wind_ax.axhline(y=500, color=self.colors['accent_orange'], 
                           linestyle=':', alpha=0.5, label='Limite 500 km/s')
        
        # Configurar gráfico
        self.wind_ax.set_title('Vento Solar - Parâmetros', 
                              color=self.colors['text_primary'], pad=10)
        self.wind_ax.set_xlabel('Tempo', color=self.colors['text_secondary'])
        self.wind_ax.set_ylabel('Valor', color=self.colors['text_secondary'])
        self.wind_ax.grid(True, alpha=0.3, linestyle='--')
        self.wind_ax.legend(loc='upper right')
        
        self.wind_fig.autofmt_xdate()
        self.wind_canvas.draw()
    
    def _update_historical_chart(self):
        """Atualiza gráfico histórico"""
        if len(self.historical_data) < 2:
            return
        
        self.hist_ax.clear()
        
        # Agrupar por dia (média diária)
        daily_data = {}
        for data in self.historical_data:
            date_key = data.timestamp.date()
            if date_key not in daily_data:
                daily_data[date_key] = []
            daily_data[date_key].append(data.kp_index)
        
        dates = sorted(daily_data.keys())
        avg_kp = [np.mean(daily_data[date]) for date in dates]
        
        # Plotar
        bars = self.hist_ax.bar(range(len(dates)), avg_kp,
                               color=[self._get_kp_color(k) for k in avg_kp],
                               edgecolor=self.colors['border'])
        
        # Configurar gráfico
        self.hist_ax.set_title('Histórico - Índice Kp (7 dias)', 
                              color=self.colors['text_primary'], pad=10)
        self.hist_ax.set_xlabel('Data', color=self.colors['text_secondary'])
        self.hist_ax.set_ylabel('Kp Index (média)', color=self.colors['text_secondary'])
        self.hist_ax.set_xticks(range(len(dates)))
        self.hist_ax.set_xticklabels([d.strftime('%d/%m') for d in dates], rotation=45)
        self.hist_ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        self.hist_canvas.draw()
    
    def _get_kp_color(self, kp_value: float) -> str:
        """Retorna cor baseada no valor do Kp"""
        if kp_value >= 5:
            return self.colors['accent_red']
        elif kp_value >= 4:
            return self.colors['accent_orange']
        elif kp_value >= 3:
            return self.colors['accent_yellow']
        else:
            return self.colors['accent_green']
    
    def _update_status(self):
        """Atualiza painel de status"""
        if self._last_update_time:
            last_update_str = self._last_update_time.strftime("%H:%M:%S")
            self.status_vars['last_update'].config(text=last_update_str)
            
            # Calcular próxima atualização
            next_update = self._last_update_time + timedelta(seconds=self.update_interval)
            next_str = next_update.strftime("%H:%M:%S")
            self.status_vars['next_update'].config(text=next_str)
        
        # Alertas ativos
        active_alerts = len([a for a in self.alerts if a.is_active])
        self.status_vars['alerts_active'].config(
            text=str(active_alerts),
            fg=self.colors['accent_red'] if active_alerts > 0 else self.colors['text_secondary']
        )
        
        # Status geral
        if self.current_weather:
            alert_level = self.current_weather.overall_alert
            status_text = alert_level.value.upper()
            status_color = {
                AlertLevel.SEVERE: self.colors['accent_red'],
                AlertLevel.ALERT: self.colors['accent_orange'],
                AlertLevel.WARNING: self.colors['accent_yellow'],
                AlertLevel.WATCH: self.colors['accent_blue'],
                AlertLevel.NORMAL: self.colors['accent_green']
            }.get(alert_level, self.colors['text_secondary'])
            
            self.status_vars['overall_status'].config(
                text=status_text,
                fg=status_color
            )
    
    def _update_alerts(self):
        """Atualiza painel de alertas"""
        # Limpar alertas antigos
        for widget in self.alerts_content.winfo_children():
            widget.destroy()
        
        # Filtrar alertas ativos
        active_alerts = [a for a in self.alerts if a.is_active]
        
        if not active_alerts:
            # Mostrar mensagem "nenhum alerta"
            tk.Label(
                self.alerts_content,
                text="Nenhum alerta ativo",
                font=self.fonts['normal'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_secondary'],
                pady=20
            ).pack()
            return
        
        # Ordenar por severidade e tempo
        severity_order = {
            AlertLevel.SEVERE: 0,
            AlertLevel.ALERT: 1,
            AlertLevel.WARNING: 2,
            AlertLevel.WATCH: 3,
            AlertLevel.NORMAL: 4
        }
        
        active_alerts.sort(key=lambda a: (severity_order[a.level], a.timestamp), reverse=True)
        
        # Criar widget para cada alerta
        for alert in active_alerts[:10]:  # Limitar a 10 alertas visíveis
            self._create_alert_widget(alert)
    
    def _create_alert_widget(self, alert: MonitorAlert):
        """Cria widget para um alerta individual"""
        # Determinar cores baseadas no nível
        alert_colors = {
            AlertLevel.SEVERE: self.colors['alert_severe'],
            AlertLevel.ALERT: self.colors['alert_warning'],
            AlertLevel.WARNING: self.colors['alert_warning'],
            AlertLevel.WATCH: self.colors['alert_watch'],
            AlertLevel.NORMAL: self.colors['alert_normal']
        }
        
        bg_color = alert_colors.get(alert.level, self.colors['bg_light'])
        text_color = self.colors['text_primary']
        
        # Frame do alerta
        alert_frame = tk.Frame(
            self.alerts_content,
            bg=bg_color,
            relief=tk.RAISED,
            borderwidth=1
        )
        alert_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Cabeçalho do alerta
        header_frame = tk.Frame(alert_frame, bg=bg_color)
        header_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # Ícone baseado no tipo
        icons = {
            'flare': '☀️',
            'cme': '💥',
            'storm': '🌪️',
            'radiation': '☢️'
        }
        
        icon = icons.get(alert.type, '⚠️')
        
        tk.Label(
            header_frame,
            text=icon,
            font=('Segoe UI', 14),
            bg=bg_color,
            fg=text_color
        ).pack(side=tk.LEFT)
        
        # Título do alerta
        title_frame = tk.Frame(header_frame, bg=bg_color)
        title_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        tk.Label(
            title_frame,
            text=alert.message,
            font=self.fonts['small'],
            bg=bg_color,
            fg=text_color,
            anchor='w'
        ).pack(fill=tk.X)
        
        tk.Label(
            title_frame,
            text=alert.timestamp.strftime("%H:%M"),
            font=('Segoe UI', 8),
            bg=bg_color,
            fg=text_color,
            anchor='w'
        ).pack(fill=tk.X)
        
        # Botão de acknowledge
        if not alert.acknowledged:
            btn = tk.Button(
                header_frame,
                text="✓",
                font=self.fonts['small'],
                bg=bg_color,
                fg=text_color,
                activebackground=text_color,
                activeforeground=bg_color,
                relief=tk.FLAT,
                command=lambda a=alert: self._acknowledge_alert(a)
            )
            btn.pack(side=tk.RIGHT)
    
    def _acknowledge_alert(self, alert: MonitorAlert):
        """Marca um alerta como reconhecido"""
        alert.acknowledged = True
        self._update_alerts()
        logger.info(f"Alerta reconhecido: {alert.id}")
    
    def _handle_noaa_alert(self, alert_data: Dict[str, Any]):
        """Processa alertas recebidos do serviço NOAA"""
        try:
            # Criar alerta do monitor
            alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            alert = MonitorAlert(
                id=alert_id,
                type=alert_data['type'],
                level=AlertLevel[alert_data['level'].upper()],
                message=alert_data['message'],
                timestamp=datetime.now(),
                expires=datetime.now() + timedelta(hours=1),
                details=alert_data.get('details', {})
            )
            
            # Adicionar à lista
            self.alerts.insert(0, alert)
            
            # Manter limite máximo
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[:self.max_alerts]
            
            # Atualizar interface
            self.parent.after(0, self._update_alerts)
            
            # Notificação visual/sonora
            self._notify_alert(alert)
            
            logger.info(f"Novo alerta processado: {alert.message}")
            
        except Exception as e:
            logger.error(f"Erro ao processar alerta NOAA: {e}")
    
    def _notify_alert(self, alert: MonitorAlert):
        """Exibe notificação para alerta importante"""
        if alert.level in [AlertLevel.SEVERE, AlertLevel.ALERT]:
            # Piscar título da janela
            original_bg = self.parent.cget('bg')
            for _ in range(3):
                self.parent.after(500, lambda: self.parent.config(bg=self.colors['accent_red']))
                self.parent.after(1000, lambda: self.parent.config(bg=original_bg))
            
            # Mostrar mensagem
            messagebox.showwarning(
                "Alerta Solar",
                f"{alert.message}\n\nNível: {alert.level.value.upper()}"
            )
    
    def force_update(self):
        """Força uma atualização imediata dos dados"""
        logger.info("Atualização forçada solicitada")
        self.update_data()
        self.update_ui()
    
    def generate_report(self):
        """Gera relatório de atividade solar"""
        try:
            if not self.current_weather or not self.current_activity:
                messagebox.showinfo("Relatório", "Aguardando dados...")
                return
            
            # Criar conteúdo do relatório
            report = f"""
            RELATÓRIO DE ATIVIDADE SOLAR
            =============================
            
            Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            STATUS GERAL: {self.current_weather.overall_alert.value.upper()}
            
            MÉTRICAS PRINCIPAIS:
            ---------------------
            • Índice Kp: {self.current_weather.kp_index:.1f}
            • Vento Solar: {self.current_weather.solar_wind.speed:.0f} km/s
            • Densidade: {self.current_weather.solar_wind.density:.1f} p/cm³
            • Componente Bz: {self.current_weather.solar_wind.bz:.1f} nT
            
            ATIVIDADE SOLAR:
            -----------------
            • Probabilidade de Flare: {self.current_activity.flare_probability:.0f}%
            • Probabilidade de CME: {self.current_activity.cme_probability:.0f}%
            • Regiões Ativas: {self.current_activity.active_regions}
            • Número de Manchas: {self.current_activity.sunspot_number}
            • Tendência: {self.current_activity.activity_trend}
            
            FLARES RECENTES:
            -----------------
            """
            
            if self.current_weather.solar_flares:
                for flare in self.current_weather.solar_flares[:5]:  # Últimos 5 flares
                    report += f"• {flare.class_value.value} - {flare.peak_time.strftime('%H:%M')} - Duração: {flare.duration_minutes:.0f} min\n"
            else:
                report += "• Nenhum flare significativo nas últimas 24h\n"
            
            report += f"""
            
            AURORA:
            -------
            """
            
            for region, prob in self.current_weather.aurora_probability.items():
                if prob > 0:
                    report += f"• {region}: {prob*100:.0f}%\n"
            
            report += f"""
            
            RECOMENDAÇÕES:
            --------------
            """
            
            # Recomendações baseadas no status
            if self.current_weather.overall_alert == AlertLevel.SEVERE:
                report += """• EVITAR atividades espaciais extraveiculares
• MONITORAR sistemas de satélites
• PREPARAR para possíveis blackouts de rádio
• NOTIFICAR operações sensíveis à radiação
"""
            elif self.current_weather.overall_alert == AlertLevel.ALERT:
                report += """• MONITORAR sistemas de comunicação
• VERIFICAR sistemas de navegação
• ALERTAR operações em altas latitudes
"""
            else:
                report += "• Condições normais - operações rotineiras\n"
            
            # Mostrar relatório
            report_window = tk.Toplevel(self.parent)
            report_window.title("Relatório de Atividade Solar")
            report_window.geometry("600x700")
            report_window.configure(bg=self.colors['bg_dark'])
            
            # Text widget para relatório
            text_widget = tk.Text(
                report_window,
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                font=self.fonts['mono'],
                wrap=tk.WORD,
                padx=10,
                pady=10
            )
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, report)
            text_widget.config(state=tk.DISABLED)
            
            # Botões
            button_frame = tk.Frame(report_window, bg=self.colors['bg_dark'])
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            tk.Button(
                button_frame,
                text="💾 Salvar",
                font=self.fonts['normal'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                command=lambda: self._save_report(report)
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                button_frame,
                text="📋 Copiar",
                font=self.fonts['normal'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                command=lambda: self.parent.clipboard_clear() or self.parent.clipboard_append(report)
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                button_frame,
                text="Fechar",
                font=self.fonts['normal'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                command=report_window.destroy
            ).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Falha ao gerar relatório: {e}")
    
    def _save_report(self, report_content: str):
        """Salva relatório em arquivo"""
        import os
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Salvar Relatório",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar relatório: {e}")
    
    def open_settings(self):
        """Abre configurações do monitor"""
        settings_window = tk.Toplevel(self.parent)
        settings_window.title("Configurações do Monitor Solar")
        settings_window.geometry("500x400")
        settings_window.configure(bg=self.colors['bg_dark'])
        
        # Conteúdo das configurações
        tk.Label(
            settings_window,
            text="Configurações do Monitor Solar",
            font=self.fonts['heading'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary'],
            pady=20
        ).pack()
        
        # Intervalo de atualização
        interval_frame = tk.Frame(settings_window, bg=self.colors['bg_dark'])
        interval_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            interval_frame,
            text="Intervalo de Atualização (segundos):",
            font=self.fonts['normal'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT)
        
        interval_var = tk.StringVar(value=str(self.update_interval))
        interval_entry = tk.Entry(
            interval_frame,
            textvariable=interval_var,
            font=self.fonts['normal'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            width=10
        )
        interval_entry.pack(side=tk.RIGHT)
        
        # Botões
        button_frame = tk.Frame(settings_window, bg=self.colors['bg_dark'])
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def apply_settings():
            try:
                new_interval = int(interval_var.get())
                if new_interval < 30:
                    messagebox.showerror("Erro", "Intervalo mínimo: 30 segundos")
                    return
                
                self.update_interval = new_interval
                settings_window.destroy()
                messagebox.showinfo("Sucesso", "Configurações aplicadas!")
                
            except ValueError:
                messagebox.showerror("Erro", "Intervalo inválido")
        
        tk.Button(
            button_frame,
            text="Aplicar",
            font=self.fonts['normal'],
            bg=self.colors['accent_blue'],
            fg=self.colors['text_primary'],
            command=apply_settings
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancelar",
            font=self.fonts['normal'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            command=settings_window.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def get_monitor_status(self) -> Dict[str, Any]:
        """Retorna status completo do monitor"""
        return {
            'is_monitoring': self.is_monitoring,
            'update_interval': self.update_interval,
            'last_update': self._last_update_time.isoformat() if hasattr(self, '_last_update_time') else None,
            'current_weather': self.current_weather.to_dict() if self.current_weather else None,
            'current_activity': {
                'flare_probability': self.current_activity.flare_probability if self.current_activity else None,
                'cme_probability': self.current_activity.cme_probability if self.current_activity else None,
                'overall_activity': self.current_activity.overall_activity if self.current_activity else None
            },
            'active_alerts': len([a for a in self.alerts if a.is_active]),
            'total_alerts': len(self.alerts),
            'historical_data_points': len(self.historical_data)
        }