"""
Janela de Análise - Painel de análise quantitativa e visualização de dados
Interface de dashboard com métricas em tempo real
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import math

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class MetricData:
    """Estrutura para dados de métricas"""
    name: str
    value: float
    change: float
    unit: str
    timestamp: datetime
    trend: List[float]
    target: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

@dataclass 
class ChartConfig:
    """Configuração de gráficos"""
    title: str
    type: str  # line, bar, scatter, heatmap
    data: np.ndarray
    x_labels: List[str]
    y_label: str
    colors: List[str]

class AnalyticsWindow:
    """Janela de análise quantitativa com visualizações Sci-Fi"""
    
    def __init__(self, parent, config: Dict[str, Any]):
        """
        Inicializa a janela de análise
        
        Args:
            parent: Widget pai
            config: Configuração da aplicação
        """
        self.parent = parent
        self.config = config
        self.metrics: Dict[str, MetricData] = {}
        self.charts: Dict[str, ChartConfig] = {}
        
        # Cores e temas Sci-Fi
        self.colors = {
            'bg_dark': '#0a0a12',
            'bg_medium': '#121225',
            'bg_light': '#1a1a35',
            'accent_blue': '#00ccff',
            'accent_purple': '#9d00ff',
            'accent_green': '#00ffaa',
            'accent_red': '#ff3366',
            'accent_orange': '#ff9900',
            'text_primary': '#ffffff',
            'text_secondary': '#a0a0c0',
            'border': '#2a2a4a',
            'grid': '#2a2a4a'
        }
        
        # Configurar estilo matplotlib
        plt.style.use('dark_background')
        self.setup_matplotlib_style()
        
        # Fontes
        self.fonts = {
            'title': ('Segoe UI', 16, 'bold'),
            'heading': ('Segoe UI', 12, 'bold'),
            'normal': ('Segoe UI', 10),
            'small': ('Segoe UI', 9),
            'mono': ('Consolas', 9)
        }
        
        self.setup_ui()
        self.load_sample_data()
        
    def setup_matplotlib_style(self):
        """Configura o estilo do matplotlib para tema Sci-Fi"""
        matplotlib.rcParams.update({
            'figure.facecolor': self.colors['bg_dark'],
            'axes.facecolor': self.colors['bg_medium'],
            'axes.edgecolor': self.colors['border'],
            'axes.labelcolor': self.colors['text_primary'],
            'axes.titlecolor': self.colors['accent_blue'],
            'xtick.color': self.colors['text_secondary'],
            'ytick.color': self.colors['text_secondary'],
            'grid.color': self.colors['grid'],
            'text.color': self.colors['text_primary'],
            'lines.linewidth': 2,
            'grid.alpha': 0.3
        })
        
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal com scroll
        self.main_frame = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas e scrollbar
        self.canvas = tk.Canvas(
            self.main_frame,
            bg=self.colors['bg_dark'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            self.main_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(
            self.canvas,
            bg=self.colors['bg_dark']
        )
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar scroll com mouse
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Criar interface
        self.create_header()
        self.create_metrics_dashboard()
        self.create_charts_section()
        self.create_insights_panel()
        
    def _on_mousewheel(self, event):
        """Manipula scroll do mouse"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def create_header(self):
        """Cria o cabeçalho da janela"""
        header_frame = tk.Frame(
            self.scrollable_frame,
            bg=self.colors['bg_dark'],
            padx=20,
            pady=20
        )
        header_frame.pack(fill=tk.X)
        
        # Título
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            title_frame,
            text="📊",
            font=('Segoe UI', 32),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_blue']
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="ANÁLISE QUANTITATIVA - DASHBOARD HUD",
            font=self.fonts['title'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=15)
        
        # Filtros de tempo
        filters_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        filters_frame.pack(fill=tk.X)
        
        time_filters = [
            ("TEMPO REAL", "realtime"),
            ("24H", "24h"),
            ("7D", "7d"),
            ("30D", "30d"),
            ("3M", "3m"),
            ("1A", "1y")
        ]
        
        for text, value in time_filters:
            btn = tk.Button(
                filters_frame,
                text=text,
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_blue'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                borderwidth=1,
                padx=12,
                pady=5,
                command=lambda v=value: self.set_time_range(v)
            )
            btn.pack(side=tk.LEFT, padx=2)
            
        # Data atualização
        self.update_label = tk.Label(
            header_frame,
            text=f"ATUALIZADO: {datetime.now().strftime('%H:%M:%S')}",
            font=self.fonts['small'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_secondary']
        )
        self.update_label.pack(anchor='e', pady=(5, 0))
        
    def create_metrics_dashboard(self):
        """Cria o dashboard de métricas"""
        metrics_frame = tk.Frame(
            self.scrollable_frame,
            bg=self.colors['bg_dark'],
            padx=20,
            pady=10
        )
        metrics_frame.pack(fill=tk.X)
        
        tk.Label(
            metrics_frame,
            text="MÉTRICAS PRINCIPAIS",
            font=self.fonts['heading'],
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_blue']
        ).pack(anchor='w', pady=(0, 10))
        
        # Container para cards de métricas
        self.metrics_container = tk.Frame(metrics_frame, bg=self.colors['bg_dark'])
        self.metrics_container.pack(fill=tk.X)
        
        # Grid 2x2 para métricas
        self.metric_frames = {}
        for i in range(4):
            frame = tk.Frame(
                self.metrics_container,
                bg=self.colors['bg_medium'],
                relief=tk.RAISED,
                borderwidth=1
            )
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.metric_frames[f'metric_{i}'] = frame
            
    def create_charts_section(self):
        """Cria a seção de gráficos"""
        charts_frame = tk.Frame(
            self.scrollable_frame,
            bg=self.colors['bg_dark'],
            padx=20,
            pady=10
        )
        charts_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            charts_frame,
            text="VISUALIZAÇÕES",
            font=self.fonts['heading'],
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_blue']
        ).pack(anchor='w', pady=(0, 10))
        
        # Frame para gráficos
        self.charts_container = tk.Frame(charts_frame, bg=self.colors['bg_dark'])
        self.charts_container.pack(fill=tk.BOTH, expand=True)
        
        # Grid 2x1 para gráficos
        self.chart_frames = {}
        for i in range(2):
            frame = tk.Frame(
                self.charts_container,
                bg=self.colors['bg_medium'],
                relief=tk.SUNKEN,
                borderwidth=2
            )
            if i == 0:
                frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)
            else:
                frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
            self.chart_frames[f'chart_{i}'] = frame
            
    def create_insights_panel(self):
        """Cria o painel de insights"""
        insights_frame = tk.Frame(
            self.scrollable_frame,
            bg=self.colors['bg_dark'],
            padx=20,
            pady=10
        )
        insights_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            insights_frame,
            text="INSIGHTS E RECOMENDAÇÕES",
            font=self.fonts['heading'],
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_blue']
        ).pack(anchor='w', pady=(0, 10))
        
        # Frame para insights
        self.insights_container = tk.Frame(
            insights_frame,
            bg=self.colors['bg_medium'],
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.insights_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Text widget para insights
        self.insights_text = tk.Text(
            self.insights_container,
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary'],
            font=self.fonts['mono'],
            wrap=tk.WORD,
            height=8,
            borderwidth=0,
            padx=10,
            pady=10
        )
        self.insights_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.insights_text.insert(tk.END, "Gerando insights...\n")
        self.insights_text.config(state=tk.DISABLED)
        
    def load_sample_data(self):
        """Carrega dados de exemplo para demonstração"""
        # Métricas de exemplo
        now = datetime.now()
        self.metrics = {
            "profitability": MetricData(
                name="Lucratividade",
                value=85.7,
                change=2.3,
                unit="%",
                timestamp=now,
                trend=[82.1, 83.5, 84.2, 85.1, 85.7],
                target=90.0
            ),
            "risk_level": MetricData(
                name="Nível de Risco",
                value=22.4,
                change=-1.2,
                unit="",
                timestamp=now,
                trend=[25.1, 24.3, 23.8, 23.1, 22.4],
                target=20.0
            ),
            "efficiency": MetricData(
                name="Eficiência",
                value=94.2,
                change=0.8,
                unit="%",
                timestamp=now,
                trend=[92.5, 93.1, 93.8, 94.0, 94.2],
                target=95.0
            ),
            "volume": MetricData(
                name="Volume",
                value=1250000,
                change=15.7,
                unit="USD",
                timestamp=now,
                trend=[980000, 1050000, 1150000, 1200000, 1250000]
            )
        }
        
        # Dados para gráficos
        self.charts = {
            "performance": ChartConfig(
                title="Desempenho ao Longo do Tempo",
                type="line",
                data=np.array([
                    np.sin(np.linspace(0, 10, 100)) * 50 + 75,
                    np.cos(np.linspace(0, 10, 100)) * 30 + 50,
                    np.sin(np.linspace(0, 10, 100) + 1) * 40 + 60
                ]),
                x_labels=[f"Hora {i}" for i in range(100)],
                y_label="Desempenho (%)",
                colors=[self.colors['accent_green'], 
                       self.colors['accent_blue'],
                       self.colors['accent_purple']]
            ),
            "distribution": ChartConfig(
                title="Distribuição de Ativos",
                type="bar",
                data=np.array([25, 18, 15, 12, 10, 8, 7, 5]),
                x_labels=["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "OUTROS"],
                y_label="Alocação (%)",
                colors=[self.colors['accent_blue'],
                       self.colors['accent_purple'],
                       self.colors['accent_green'],
                       self.colors['accent_orange'],
                       self.colors['accent_red'],
                       '#00ffff', '#ff00ff', '#ffff00']
            )
        }
        
        # Atualizar UI
        self.update_metrics_display()
        self.create_charts()
        self.generate_insights()
        
    def update_metrics_display(self):
        """Atualiza a exibição das métricas"""
        metric_keys = list(self.metrics.keys())
        
        for i, frame_key in enumerate(self.metric_frames.keys()):
            if i < len(metric_keys):
                metric_key = metric_keys[i]
                metric = self.metrics[metric_key]
                self.create_metric_card(self.metric_frames[frame_key], metric)
                
    def create_metric_card(self, parent, metric: MetricData):
        """Cria um card de métrica"""
        # Limpar frame
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Frame interno
        inner_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Nome da métrica
        tk.Label(
            inner_frame,
            text=metric.name.upper(),
            font=self.fonts['small'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary'],
            anchor='w'
        ).pack(fill=tk.X, pady=(0, 5))
        
        # Valor principal
        value_str = f"{metric.value:,.2f}" if metric.value >= 1000 else f"{metric.value:.2f}"
        tk.Label(
            inner_frame,
            text=f"{value_str} {metric.unit}",
            font=('Segoe UI', 20, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        ).pack(anchor='w', pady=(0, 5))
        
        # Variação
        change_color = self.colors['accent_green'] if metric.change >= 0 else self.colors['accent_red']
        change_icon = "↗" if metric.change >= 0 else "↘"
        
        tk.Label(
            inner_frame,
            text=f"{change_icon} {abs(metric.change):.2f}%",
            font=self.fonts['normal'],
            bg=self.colors['bg_medium'],
            fg=change_color
        ).pack(anchor='w', pady=(0, 10))
        
        # Mini gráfico de tendência
        self.create_trend_chart(inner_frame, metric.trend)
        
        # Timestamp
        time_str = metric.timestamp.strftime("%H:%M:%S")
        tk.Label(
            inner_frame,
            text=f"Atualizado: {time_str}",
            font=self.fonts['small'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.BOTTOM, anchor='w')
        
    def create_trend_chart(self, parent, trend: List[float]):
        """Cria um mini gráfico de tendência"""
        canvas = tk.Canvas(
            parent,
            width=200,
            height=60,
            bg=self.colors['bg_medium'],
            highlightthickness=0
        )
        canvas.pack(fill=tk.X, pady=(0, 10))
        
        if len(trend) < 2:
            return
            
        # Normalizar dados
        min_val = min(trend)
        max_val = max(trend)
        if max_val == min_val:
            normalized = [0.5] * len(trend)
        else:
            normalized = [(v - min_val) / (max_val - min_val) for v in trend]
        
        # Desenhar linha
        width = canvas.winfo_reqwidth()
        height = canvas.winfo_reqheight()
        padding = 10
        
        points = []
        for i, val in enumerate(normalized):
            x = padding + i * (width - 2 * padding) / (len(trend) - 1)
            y = height - padding - val * (height - 2 * padding)
            points.extend([x, y])
        
        # Linha principal
        canvas.create_line(
            points,
            fill=self.colors['accent_blue'],
            width=2,
            smooth=True
        )
        
        # Pontos
        for i in range(0, len(points), 2):
            x, y = points[i], points[i+1]
            canvas.create_oval(
                x-2, y-2, x+2, y+2,
                fill=self.colors['accent_blue'],
                outline=""
            )
            
    def create_charts(self):
        """Cria os gráficos principais"""
        chart_keys = list(self.charts.keys())
        
        for i, frame_key in enumerate(self.chart_frames.keys()):
            if i < len(chart_keys):
                chart_key = chart_keys[i]
                chart = self.charts[chart_key]
                self.create_chart_in_frame(self.chart_frames[frame_key], chart)
                
    def create_chart_in_frame(self, parent, chart: ChartConfig):
        """Cria um gráfico matplotlib no frame"""
        # Limpar frame
        for widget in parent.winfo_children():
            widget.destroy()
            
        # Criar figura matplotlib
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plotar baseado no tipo
        if chart.type == "line":
            for i, data_line in enumerate(chart.data):
                ax.plot(
                    data_line,
                    label=f"Série {i+1}",
                    color=chart.colors[i % len(chart.colors)],
                    linewidth=2,
                    alpha=0.8
                )
        elif chart.type == "bar":
            bars = ax.bar(
                range(len(chart.data)),
                chart.data,
                color=chart.colors[:len(chart.data)],
                edgecolor=self.colors['border'],
                linewidth=1
            )
            ax.set_xticks(range(len(chart.data)))
            ax.set_xticklabels(chart.x_labels, rotation=45, ha='right')
            
        # Configurar gráfico
        ax.set_title(chart.title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel('Tempo' if chart.type == "line" else 'Categoria')
        ax.set_ylabel(chart.y_label)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper right')
        
        # Ajustar layout
        fig.tight_layout()
        
        # Embed no tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def generate_insights(self):
        """Gera insights baseados nos dados atuais"""
        insights = []
        
        # Análise de lucratividade
        profit_metric = self.metrics.get("profitability")
        if profit_metric:
            if profit_metric.value >= 85:
                insights.append("✅ ALTA LUCRO: Estratégia atual apresentando excelente performance.")
            elif profit_metric.value >= 70:
                insights.append("⚠️ LUCRO MODERADO: Considere ajustar parâmetros para melhorar resultados.")
            else:
                insights.append("❌ LUCRO BAIXO: Revisão urgente da estratégia necessária.")
                
        # Análise de risco
        risk_metric = self.metrics.get("risk_level")
        if risk_metric:
            if risk_metric.value <= 20:
                insights.append("✅ RISCO CONTROLADO: Perfil conservador mantido adequadamente.")
            elif risk_metric.value <= 30:
                insights.append("⚠️ RISCO MODERADO: Monitorar exposição de perdas.")
            else:
                insights.append("❌ RISCO ELEVADO: Reduzir alavancagem e posições agressivas.")
                
        # Análise de eficiência
        eff_metric = self.metrics.get("efficiency")
        if eff_metric:
            if eff_metric.value >= 95:
                insights.append("✅ EFICIÊNCIA ÓTIMA: Processos funcionando no máximo potencial.")
            elif eff_metric.value >= 90:
                insights.append("⚠️ EFICIÊNCIA BOA: Pequenos ajustes podem melhorar performance.")
            else:
                insights.append("❌ EFICIÊNCIA BAIXA: Identificar gargalos no sistema.")
                
        # Recomendações gerais
        insights.append("\n🎯 RECOMENDAÇÕES:")
        
        # Calcular recomendação baseada em múltiplas métricas
        avg_score = np.mean([
            profit_metric.value if profit_metric else 0,
            100 - risk_metric.value if risk_metric else 0,
            eff_metric.value if eff_metric else 0
        ])
        
        if avg_score >= 85:
            insights.append("• Manter estratégia atual")
            insights.append("• Considerar aumento gradual de capital")
            insights.append("• Explorar novos pares de trading")
        elif avg_score >= 70:
            insights.append("• Otimizar parâmetros atuais")
            insights.append("• Diversificar mais a carteira")
            insights.append("• Implementar stops mais conservadores")
        else:
            insights.append("• Revisar completamente a estratégia")
            insights.append("• Reduzir tamanho das posições")
            insights.append("• Implementar análise de correlação")
            
        # Atualizar widget de texto
        self.insights_text.config(state=tk.NORMAL)
        self.insights_text.delete(1.0, tk.END)
        
        for insight in insights:
            tag = "normal"
            if insight.startswith("✅"):
                tag = "positive"
            elif insight.startswith("⚠️"):
                tag = "warning"
            elif insight.startswith("❌"):
                tag = "negative"
                
            self.insights_text.insert(tk.END, insight + "\n", tag)
            
        # Configurar tags de cor
        self.insights_text.tag_config("positive", foreground=self.colors['accent_green'])
        self.insights_text.tag_config("warning", foreground=self.colors['accent_orange'])
        self.insights_text.tag_config("negative", foreground=self.colors['accent_red'])
        self.insights_text.tag_config("normal", foreground=self.colors['text_primary'])
        
        self.insights_text.config(state=tk.DISABLED)
        
    def set_time_range(self, range_str: str):
        """Define o intervalo de tempo para análise"""
        logger.info(f"Alterando intervalo de tempo para: {range_str}")
        
        # Atualizar dados baseados no intervalo
        # (em implementação real, buscaria dados do período)
        
        # Atualizar label
        self.update_label.config(
            text=f"ATUALIZADO: {datetime.now().strftime('%H:%M:%S')} | PERÍODO: {range_str.upper()}"
        )
        
    def refresh_data(self):
        """Atualiza todos os dados da janela"""
        logger.info("Atualizando dados de análise...")
        
        # Simular atualização de métricas
        for metric in self.metrics.values():
            # Pequena variação aleatória
            variation = np.random.uniform(-0.5, 0.5)
            metric.value = max(0, metric.value + variation)
            metric.change = variation
            metric.timestamp = datetime.now()
            
            # Atualizar tendência
            metric.trend = metric.trend[1:] + [metric.value]
            
        # Atualizar UI
        self.update_metrics_display()
        self.generate_insights()
        
    def export_report(self):
        """Exporta relatório de análise"""
        logger.info("Exportando relatório de análise...")
        # Implementação real viria aqui
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {k: vars(v) for k, v in self.metrics.items()},
            "charts": list(self.charts.keys()),
            "insights": self.get_current_insights()
        }
        
    def get_current_insights(self) -> List[str]:
        """Retorna insights atuais"""
        self.insights_text.config(state=tk.NORMAL)
        insights = self.insights_text.get(1.0, tk.END).strip().split('\n')
        self.insights_text.config(state=tk.DISABLED)
        return insights