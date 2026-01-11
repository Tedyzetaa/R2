"""
Janela de Trading - Interface para operações e monitoramento de trading
Dashboard profissional com visualização em tempo real
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
import time
import random

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Tipos de ordens de trading"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    """Lados da ordem"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """Status das ordens"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    """Representa uma ordem de trading"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    filled_quantity: float = 0.0
    average_price: Optional[float] = None
    
@dataclass
class Position:
    """Representa uma posição aberta"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.now)
    
@dataclass
class MarketData:
    """Dados de mercado em tempo real"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    change: float
    change_percent: float
    timestamp: datetime
    high_24h: float
    low_24h: float

class TradingWindow:
    """Janela de trading com interface profissional"""
    
    def __init__(self, parent, config: Dict[str, Any]):
        """
        Inicializa a janela de trading
        
        Args:
            parent: Widget pai
            config: Configuração da aplicação
        """
        self.parent = parent
        self.config = config
        self.orders: List[Order] = []
        self.positions: Dict[str, Position] = {}
        self.market_data: Dict[str, MarketData] = {}
        self.watchlist: List[str] = ["BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD", "DOT/USD"]
        
        # Simulação de dados
        self.simulation_running = False
        self.simulation_thread: Optional[threading.Thread] = None
        
        # Cores e temas
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
            'profit': '#00cc66',
            'loss': '#ff3366'
        }
        
        # Fontes
        self.fonts = {
            'title': ('Segoe UI', 16, 'bold'),
            'heading': ('Segoe UI', 12, 'bold'),
            'normal': ('Segoe UI', 10),
            'small': ('Segoe UI', 9),
            'mono': ('Consolas', 9)
        }
        
        self.setup_ui()
        self.start_simulation()
        
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal
        self.main_frame = tk.Frame(
            self.parent,
            bg=self.colors['bg_dark']
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Layout em grid
        self.main_frame.grid_columnconfigure(0, weight=2)  # Gráfico
        self.main_frame.grid_columnconfigure(1, weight=1)  # Painel direito
        self.main_frame.grid_rowconfigure(0, weight=2)     # Cabeçalho + gráfico
        self.main_frame.grid_rowconfigure(1, weight=1)     # Ordens + posições
        
        # Cabeçalho
        self.create_header()
        
        # Área do gráfico
        self.create_chart_area()
        
        # Painel direito
        self.create_right_panel()
        
        # Área inferior
        self.create_bottom_panel()
        
    def create_header(self):
        """Cria o cabeçalho da janela"""
        header_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark'],
            padx=20,
            pady=15
        )
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew')
        
        # Título
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        title_frame.pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="💎",
            font=('Segoe UI', 32),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_blue']
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="PAINEL DE TRADING - R2 ASSISTANT",
            font=self.fonts['title'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=10)
        
        # Status do trading
        self.trading_status = tk.Label(
            header_frame,
            text="🟢 TRADING ATIVO",
            font=self.fonts['heading'],
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_green']
        )
        self.trading_status.pack(side=tk.RIGHT, padx=20)
        
        # Controles rápidos
        controls_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        controls_frame.pack(side=tk.RIGHT)
        
        control_buttons = [
            ("⏸️ PAUSAR", self.toggle_trading),
            ("🔄 ATUALIZAR", self.refresh_data),
            ("📊 RELATÓRIO", self.generate_report)
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
                padx=10,
                pady=5,
                command=command
            )
            btn.pack(side=tk.LEFT, padx=2)
            
    def create_chart_area(self):
        """Cria a área do gráfico de preços"""
        chart_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_medium'],
            relief=tk.SUNKEN,
            borderwidth=2
        )
        chart_frame.grid(row=0, column=0, sticky='nsew', padx=(20, 10), pady=(0, 10))
        
        # Controles do gráfico
        chart_controls = tk.Frame(chart_frame, bg=self.colors['bg_medium'])
        chart_controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Seletor de símbolo
        tk.Label(
            chart_controls,
            text="Símbolo:",
            font=self.fonts['normal'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT)
        
        self.symbol_var = tk.StringVar(value="BTC/USD")
        symbol_combo = ttk.Combobox(
            chart_controls,
            textvariable=self.symbol_var,
            values=self.watchlist,
            state="readonly",
            width=15
        )
        symbol_combo.pack(side=tk.LEFT, padx=5)
        symbol_combo.bind("<<ComboboxSelected>>", self.on_symbol_changed)
        
        # Intervalos de tempo
        intervals = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        for interval in intervals:
            btn = tk.Button(
                chart_controls,
                text=interval,
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_blue'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                width=4,
                command=lambda i=interval: self.set_chart_interval(i)
            )
            btn.pack(side=tk.LEFT, padx=2)
            
        # Indicadores
        indicators_frame = tk.Frame(chart_controls, bg=self.colors['bg_medium'])
        indicators_frame.pack(side=tk.RIGHT)
        
        indicators = ["MA", "RSI", "MACD", "BB"]
        for indicator in indicators:
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(
                indicators_frame,
                text=indicator,
                variable=var,
                font=self.fonts['small'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary'],
                selectcolor=self.colors['bg_dark']
            )
            cb.pack(side=tk.LEFT, padx=5)
            
        # Canvas do gráfico
        self.chart_canvas = tk.Canvas(
            chart_frame,
            bg=self.colors['bg_dark'],
            highlightthickness=0
        )
        self.chart_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Inicializar gráfico
        self.create_price_chart()
        
    def create_right_panel(self):
        """Cria o painel direito com dados de mercado e ordens"""
        right_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark']
        )
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 20), pady=(0, 10))
        
        # Notebook para abas
        self.right_notebook = ttk.Notebook(right_frame)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba de ordens
        self.orders_tab = tk.Frame(self.right_notebook, bg=self.colors['bg_medium'])
        self.right_notebook.add(self.orders_tab, text="📝 ORDENS")
        self.create_orders_tab()
        
        # Aba de mercado
        self.market_tab = tk.Frame(self.right_notebook, bg=self.colors['bg_medium'])
        self.right_notebook.add(self.market_tab, text="📊 MERCADO")
        self.create_market_tab()
        
        # Aba de nova ordem
        self.new_order_tab = tk.Frame(self.right_notebook, bg=self.colors['bg_medium'])
        self.right_notebook.add(self.new_order_tab, text="➕ NOVA ORDEM")
        self.create_new_order_tab()
        
    def create_bottom_panel(self):
        """Cria o painel inferior com posições e histórico"""
        bottom_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark']
        )
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=20, pady=(0, 20))
        
        # Notebook inferior
        self.bottom_notebook = ttk.Notebook(bottom_frame)
        self.bottom_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba de posições
        self.positions_tab = tk.Frame(self.bottom_notebook, bg=self.colors['bg_medium'])
        self.bottom_notebook.add(self.positions_tab, text="💰 POSIÇÕES")
        self.create_positions_tab()
        
        # Aba de histórico
        self.history_tab = tk.Frame(self.bottom_notebook, bg=self.colors['bg_medium'])
        self.bottom_notebook.add(self.history_tab, text="📜 HISTÓRICO")
        self.create_history_tab()
        
    def create_orders_tab(self):
        """Cria a aba de ordens ativas"""
        # Treeview para ordens
        columns = ('id', 'symbol', 'side', 'type', 'quantity', 'price', 'status')
        
        self.orders_tree = ttk.Treeview(
            self.orders_tab,
            columns=columns,
            show='headings',
            height=8
        )
        
        # Configurar colunas
        headers = [
            ('ID', 80),
            ('Símbolo', 100),
            ('Lado', 80),
            ('Tipo', 100),
            ('Quantidade', 100),
            ('Preço', 100),
            ('Status', 120)
        ]
        
        for col, (text, width) in zip(columns, headers):
            self.orders_tree.heading(col, text=text)
            self.orders_tree.column(col, width=width)
            
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.orders_tab,
            orient=tk.VERTICAL,
            command=self.orders_tree.yview
        )
        self.orders_tree.configure(yscrollcommand=scrollbar.set)
        
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botões de ação
        actions_frame = tk.Frame(self.orders_tab, bg=self.colors['bg_medium'])
        actions_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        action_buttons = [
            ("↻ Atualizar", self.refresh_orders),
            ("✏️ Editar", self.edit_order),
            ("❌ Cancelar", self.cancel_order),
            ("🗑️ Limpar", self.clear_orders)
        ]
        
        for text, command in action_buttons:
            btn = tk.Button(
                actions_frame,
                text=text,
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_blue'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                padx=10,
                pady=3,
                command=command
            )
            btn.pack(side=tk.LEFT, padx=2)
            
    def create_market_tab(self):
        """Cria a aba de dados de mercado"""
        # Treeview para dados de mercado
        columns = ('symbol', 'last', 'change', 'volume', 'high', 'low')
        
        self.market_tree = ttk.Treeview(
            self.market_tab,
            columns=columns,
            show='headings',
            height=8
        )
        
        # Configurar colunas
        headers = [
            ('Símbolo', 100),
            ('Último', 100),
            ('Variação', 100),
            ('Volume', 120),
            ('Máxima', 100),
            ('Mínima', 100)
        ]
        
        for col, (text, width) in zip(columns, headers):
            self.market_tree.heading(col, text=text)
            self.market_tree.column(col, width=width)
            
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.market_tab,
            orient=tk.VERTICAL,
            command=self.market_tree.yview
        )
        self.market_tree.configure(yscrollcommand=scrollbar.set)
        
        self.market_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Atualizar dados periodicamente
        self.update_market_data()
        
    def create_new_order_tab(self):
        """Cria a aba para nova ordem"""
        form_frame = tk.Frame(self.new_order_tab, bg=self.colors['bg_medium'], padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formulário de nova ordem
        fields = [
            ("Símbolo:", "symbol", tk.StringVar(value="BTC/USD")),
            ("Lado:", "side", tk.StringVar(value="buy")),
            ("Tipo:", "type", tk.StringVar(value="market")),
            ("Quantidade:", "quantity", tk.DoubleVar(value=0.01)),
            ("Preço:", "price", tk.DoubleVar(value=0.0)),
            ("Stop Price:", "stop_price", tk.DoubleVar(value=0.0))
        ]
        
        self.order_vars = {}
        
        for i, (label, key, var) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=self.fonts['normal'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary'],
                anchor='w'
            ).grid(row=i, column=0, sticky='w', pady=5)
            
            if key == "side":
                combo = ttk.Combobox(
                    form_frame,
                    textvariable=var,
                    values=["buy", "sell"],
                    state="readonly",
                    width=20
                )
                combo.grid(row=i, column=1, sticky='w', pady=5)
            elif key == "type":
                combo = ttk.Combobox(
                    form_frame,
                    textvariable=var,
                    values=["market", "limit", "stop", "stop_limit"],
                    state="readonly",
                    width=20
                )
                combo.grid(row=i, column=1, sticky='w', pady=5)
            else:
                entry = tk.Entry(
                    form_frame,
                    textvariable=var,
                    font=self.fonts['normal'],
                    bg=self.colors['bg_light'],
                    fg=self.colors['text_primary'],
                    width=25
                )
                entry.grid(row=i, column=1, sticky='w', pady=5)
                
            self.order_vars[key] = var
            
        # Botões
        buttons_frame = tk.Frame(form_frame, bg=self.colors['bg_medium'])
        buttons_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        tk.Button(
            buttons_frame,
            text="📋 Pré-visualizar",
            font=self.fonts['normal'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['accent_blue'],
            activeforeground=self.colors['text_primary'],
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.preview_order
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            buttons_frame,
            text="✅ Enviar Ordem",
            font=self.fonts['normal'],
            bg=self.colors['accent_green'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['accent_blue'],
            activeforeground=self.colors['text_primary'],
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.submit_order
        ).pack(side=tk.LEFT, padx=5)
        
    def create_positions_tab(self):
        """Cria a aba de posições abertas"""
        # Treeview para posições
        columns = ('symbol', 'quantity', 'entry', 'current', 'pnl', 'pnl_percent')
        
        self.positions_tree = ttk.Treeview(
            self.positions_tab,
            columns=columns,
            show='headings',
            height=5
        )
        
        # Configurar colunas
        headers = [
            ('Símbolo', 100),
            ('Quantidade', 100),
            ('Preço Entrada', 100),
            ('Preço Atual', 100),
            ('P&L', 100),
            ('P&L %', 100)
        ]
        
        for col, (text, width) in zip(columns, headers):
            self.positions_tree.heading(col, text=text)
            self.positions_tree.column(col, width=width)
            
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.positions_tab,
            orient=tk.VERTICAL,
            command=self.positions_tree.yview
        )
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Resumo
        summary_frame = tk.Frame(self.positions_tab, bg=self.colors['bg_medium'])
        summary_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.total_pnl_label = tk.Label(
            summary_frame,
            text="P&L Total: $0.00 (0.00%)",
            font=self.fonts['heading'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        )
        self.total_pnl_label.pack(side=tk.LEFT, padx=10)
        
    def create_history_tab(self):
        """Cria a aba de histórico de trades"""
        # Treeview para histórico
        columns = ('time', 'symbol', 'side', 'quantity', 'price', 'total')
        
        self.history_tree = ttk.Treeview(
            self.history_tab,
            columns=columns,
            show='headings',
            height=5
        )
        
        # Configurar colunas
        headers = [
            ('Hora', 120),
            ('Símbolo', 100),
            ('Lado', 80),
            ('Quantidade', 100),
            ('Preço', 100),
            ('Total', 120)
        ]
        
        for col, (text, width) in zip(columns, headers):
            self.history_tree.heading(col, text=text)
            self.history_tree.column(col, width=width)
            
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.history_tab,
            orient=tk.VERTICAL,
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_price_chart(self):
        """Cria o gráfico de preços"""
        # Criar figura matplotlib
        self.chart_fig = Figure(figsize=(10, 6), dpi=100, facecolor=self.colors['bg_dark'])
        self.chart_ax = self.chart_fig.add_subplot(111)
        
        # Configurar estilo
        self.chart_ax.set_facecolor(self.colors['bg_medium'])
        self.chart_ax.tick_params(colors=self.colors['text_secondary'])
        self.chart_ax.spines['bottom'].set_color(self.colors['border'])
        self.chart_ax.spines['top'].set_color(self.colors['border'])
        self.chart_ax.spines['left'].set_color(self.colors['border'])
        self.chart_ax.spines['right'].set_color(self.colors['border'])
        
        # Dados de exemplo
        self.generate_sample_chart_data()
        
        # Embed no canvas
        self.chart_canvas_widget = FigureCanvasTkAgg(self.chart_fig, self.chart_canvas)
        self.chart_canvas_widget.draw()
        self.chart_canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def generate_sample_chart_data(self):
        """Gera dados de exemplo para o gráfico"""
        # Gerar dados de candlestick aleatórios
        np.random.seed(42)
        n_points = 100
        
        # Preços base
        base_price = 45000
        prices = [base_price]
        
        for i in range(1, n_points):
            change = np.random.normal(0, 0.02)  # 2% de variação
            prices.append(prices[-1] * (1 + change))
            
        # Converter para OHLC
        self.ohlc_data = []
        for i in range(0, n_points, 5):
            if i + 5 <= n_points:
                chunk = prices[i:i+5]
                open_price = chunk[0]
                close_price = chunk[-1]
                high_price = max(chunk)
                low_price = min(chunk)
                self.ohlc_data.append((open_price, high_price, low_price, close_price))
                
        # Plotar
        self.chart_ax.clear()
        
        # Plotar candlesticks
        for i, (open_price, high_price, low_price, close_price) in enumerate(self.ohlc_data):
            color = self.colors['accent_green'] if close_price >= open_price else self.colors['accent_red']
            
            # Corpo do candle
            self.chart_ax.plot([i, i], [low_price, high_price], color=color, linewidth=1)
            
            # Wick
            if close_price >= open_price:
                self.chart_ax.fill_between([i-0.3, i+0.3], open_price, close_price, color=color)
            else:
                self.chart_ax.fill_between([i-0.3, i+0.3], close_price, open_price, color=color)
                
        self.chart_ax.set_title(
            f"{self.symbol_var.get()} - Gráfico de Preços",
            color=self.colors['text_primary'],
            fontsize=12,
            pad=10
        )
        self.chart_ax.set_xlabel('Período', color=self.colors['text_secondary'])
        self.chart_ax.set_ylabel('Preço (USD)', color=self.colors['text_secondary'])
        self.chart_ax.grid(True, alpha=0.3, linestyle='--', color=self.colors['border'])
        
        self.chart_fig.tight_layout()
        self.chart_canvas_widget.draw()
        
    def on_symbol_changed(self, event):
        """Chamado quando o símbolo é alterado"""
        symbol = self.symbol_var.get()
        self.generate_sample_chart_data()
        logger.info(f"Símbolo alterado para: {symbol}")
        
    def set_chart_interval(self, interval: str):
        """Define o intervalo do gráfico"""
        logger.info(f"Intervalo do gráfico alterado para: {interval}")
        self.generate_sample_chart_data()
        
    def start_simulation(self):
        """Inicia a simulação de dados de mercado"""
        self.simulation_running = True
        self.simulation_thread = threading.Thread(target=self.market_simulation, daemon=True)
        self.simulation_thread.start()
        
    def market_simulation(self):
        """Simula dados de mercado em tempo real"""
        # Preços iniciais
        base_prices = {
            "BTC/USD": 45000,
            "ETH/USD": 2500,
            "SOL/USD": 100,
            "ADA/USD": 0.5,
            "DOT/USD": 7.5
        }
        
        current_prices = base_prices.copy()
        
        while self.simulation_running:
            try:
                # Atualizar preços aleatoriamente
                for symbol in self.watchlist:
                    if symbol in current_prices:
                        # Pequena variação aleatória
                        change = np.random.normal(0, 0.001)  # 0.1% de variação
                        current_prices[symbol] *= (1 + change)
                        
                        # Criar dados de mercado
                        price = current_prices[symbol]
                        market_data = MarketData(
                            symbol=symbol,
                            bid=price * 0.999,
                            ask=price * 1.001,
                            last=price,
                            volume=np.random.uniform(1000, 10000),
                            change=price - base_prices[symbol],
                            change_percent=(price - base_prices[symbol]) / base_prices[symbol] * 100,
                            timestamp=datetime.now(),
                            high_24h=price * 1.02,
                            low_24h=price * 0.98
                        )
                        
                        self.market_data[symbol] = market_data
                        
                # Atualizar UI na thread principal
                self.parent.after(0, self.update_market_display)
                
                # Esperar antes da próxima atualização
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Erro na simulação de mercado: {e}")
                time.sleep(5)
                
    def update_market_display(self):
        """Atualiza a exibição dos dados de mercado"""
        # Atualizar treeview de mercado
        for item in self.market_tree.get_children():
            self.market_tree.delete(item)
            
        for symbol, data in self.market_data.items():
            # Determinar cor da variação
            change_color = self.colors['accent_green'] if data.change >= 0 else self.colors['accent_red']
            change_sign = "+" if data.change >= 0 else ""
            
            self.market_tree.insert(
                '',
                tk.END,
                values=(
                    symbol,
                    f"${data.last:,.2f}",
                    f"{change_sign}{data.change_percent:.2f}%",
                    f"${data.volume:,.0f}",
                    f"${data.high_24h:,.2f}",
                    f"${data.low_24h:,.2f}"
                ),
                tags=(symbol,)
            )
            
            # Aplicar cor à coluna de variação
            self.market_tree.tag_configure(symbol, foreground=change_color)
            
        # Atualizar posições se existirem
        self.update_positions_display()
        
    def update_market_data(self):
        """Atualiza dados de mercado (chamado periodicamente)"""
        self.update_market_display()
        # Agendar próxima atualização
        self.parent.after(5000, self.update_market_data)
        
    def update_positions_display(self):
        """Atualiza a exibição das posições"""
        # Limpar treeview
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
            
        total_pnl = 0
        total_pnl_percent = 0
        
        for symbol, position in self.positions.items():
            # Atualizar preço atual
            if symbol in self.market_data:
                position.current_price = self.market_data[symbol].last
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
                position.unrealized_pnl_percent = (position.current_price / position.entry_price - 1) * 100
                position.updated_at = datetime.now()
                
            # Determinar cor do P&L
            pnl_color = self.colors['profit'] if position.unrealized_pnl >= 0 else self.colors['loss']
            pnl_sign = "+" if position.unrealized_pnl >= 0 else ""
            
            self.positions_tree.insert(
                '',
                tk.END,
                values=(
                    symbol,
                    f"{position.quantity:.4f}",
                    f"${position.entry_price:,.2f}",
                    f"${position.current_price:,.2f}",
                    f"{pnl_sign}${position.unrealized_pnl:,.2f}",
                    f"{pnl_sign}{position.unrealized_pnl_percent:.2f}%"
                ),
                tags=(symbol,)
            )
            
            # Aplicar cor ao P&L
            self.positions_tree.tag_configure(symbol, foreground=pnl_color)
            
            # Acumular totais
            total_pnl += position.unrealized_pnl
            total_pnl_percent = (total_pnl_percent + position.unrealized_pnl_percent) / 2
            
        # Atualizar resumo
        total_color = self.colors['profit'] if total_pnl >= 0 else self.colors['loss']
        total_sign = "+" if total_pnl >= 0 else ""
        
        self.total_pnl_label.config(
            text=f"P&L Total: {total_sign}${total_pnl:,.2f} ({total_sign}{total_pnl_percent:.2f}%)",
            fg=total_color
        )
        
    def preview_order(self):
        """Pré-visualiza uma ordem antes de enviar"""
        try:
            # Coletar dados do formulário
            symbol = self.order_vars['symbol'].get()
            side = self.order_vars['side'].get()
            order_type = self.order_vars['type'].get()
            quantity = self.order_vars['quantity'].get()
            price = self.order_vars['price'].get()
            
            # Validar
            if quantity <= 0:
                messagebox.showerror("Erro", "Quantidade deve ser maior que zero")
                return
                
            if order_type != "market" and price <= 0:
                messagebox.showerror("Erro", "Preço deve ser especificado para ordens limit/stop")
                return
                
            # Mostrar pré-visualização
            preview_text = f"""
            📋 PRÉ-VISUALIZAÇÃO DA ORDEM
            
            Símbolo: {symbol}
            Lado: {side.upper()}
            Tipo: {order_type.upper()}
            Quantidade: {quantity:.4f}
            Preço: ${price:,.2f if price > 0 else 'MARKET'}
            
            Deseja prosseguir com o envio?
            """
            
            response = messagebox.askyesno("Pré-visualização", preview_text)
            
            if response:
                self.submit_order()
                
        except Exception as e:
            logger.error(f"Erro ao pré-visualizar ordem: {e}")
            messagebox.showerror("Erro", f"Falha na pré-visualização: {e}")
            
    def submit_order(self):
        """Envia uma nova ordem"""
        try:
            # Coletar dados do formulário
            symbol = self.order_vars['symbol'].get()
            side = OrderSide(self.order_vars['side'].get())
            order_type = OrderType(self.order_vars['type'].get())
            quantity = self.order_vars['quantity'].get()
            price = self.order_vars['price'].get() if self.order_vars['price'].get() > 0 else None
            stop_price = self.order_vars['stop_price'].get() if self.order_vars['stop_price'].get() > 0 else None
            
            # Criar ordem
            order_id = f"ORD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"
            
            order = Order(
                id=order_id,
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                status=OrderStatus.PENDING
            )
            
            # Adicionar à lista
            self.orders.append(order)
            
            # Atualizar display
            self.refresh_orders()
            
            # Simular processamento
            self.parent.after(1000, lambda: self.process_order(order))
            
            logger.info(f"Ordem enviada: {order_id}")
            messagebox.showinfo("Sucesso", f"Ordem {order_id} enviada com sucesso!")
            
            # Limpar formulário
            self.order_vars['quantity'].set(0.01)
            self.order_vars['price'].set(0.0)
            self.order_vars['stop_price'].set(0.0)
            
        except Exception as e:
            logger.error(f"Erro ao enviar ordem: {e}")
            messagebox.showerror("Erro", f"Falha ao enviar ordem: {e}")
            
    def process_order(self, order: Order):
        """Processa uma ordem (simulação)"""
        # Simular execução
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.OPEN
            
        # Simular preenchimento
        if random.random() > 0.3:  # 70% de chance de preenchimento
            if order.type == OrderType.MARKET:
                # Preço de mercado atual
                if order.symbol in self.market_data:
                    order.average_price = self.market_data[order.symbol].last
                else:
                    order.average_price = 45000  # Fallback
                    
            elif order.type == OrderType.LIMIT and order.price:
                # Verificar se o preço foi atingido
                if order.symbol in self.market_data:
                    current_price = self.market_data[order.symbol].last
                    if (order.side == OrderSide.BUY and current_price <= order.price) or \
                       (order.side == OrderSide.SELL and current_price >= order.price):
                        order.average_price = order.price
                        
            # Atualizar status
            if order.average_price:
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.updated_at = datetime.now()
                
                # Criar posição se for compra
                if order.side == OrderSide.BUY and order.status == OrderStatus.FILLED:
                    position = Position(
                        symbol=order.symbol,
                        quantity=order.quantity,
                        entry_price=order.average_price,
                        current_price=order.average_price,
                        unrealized_pnl=0.0,
                        unrealized_pnl_percent=0.0,
                        created_at=datetime.now()
                    )
                    self.positions[order.symbol] = position
                    
                # Atualizar histórico
                self.add_to_history(order)
                
        else:
            # Simular rejeição
            order.status = OrderStatus.REJECTED
            
        # Atualizar display
        self.refresh_orders()
        self.update_positions_display()
        
    def add_to_history(self, order: Order):
        """Adiciona ordem ao histórico"""
        # Adicionar à treeview de histórico
        if order.status == OrderStatus.FILLED:
            self.history_tree.insert(
                '',
                0,  # Inserir no topo
                values=(
                    order.updated_at.strftime("%H:%M:%S"),
                    order.symbol,
                    order.side.value.upper(),
                    f"{order.quantity:.4f}",
                    f"${order.average_price:,.2f}" if order.average_price else "N/A",
                    f"${order.quantity * (order.average_price or 0):,.2f}"
                )
            )
            
    def refresh_orders(self):
        """Atualiza a exibição das ordens"""
        # Limpar treeview
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
            
        # Adicionar ordens
        for order in self.orders:
            # Determinar cor baseada no status
            status_color = self.colors['text_secondary']
            if order.status == OrderStatus.FILLED:
                status_color = self.colors['accent_green']
            elif order.status == OrderStatus.REJECTED:
                status_color = self.colors['accent_red']
            elif order.status == OrderStatus.PENDING:
                status_color = self.colors['accent_orange']
                
            # Adicionar à treeview
            self.orders_tree.insert(
                '',
                tk.END,
                values=(
                    order.id[-8:],  # Mostrar apenas últimos 8 caracteres
                    order.symbol,
                    order.side.value.upper(),
                    order.type.value.upper(),
                    f"{order.quantity:.4f}",
                    f"${order.price:,.2f}" if order.price else "MARKET",
                    order.status.value.upper()
                ),
                tags=(order.id,)
            )
            
            # Aplicar cor ao status
            self.orders_tree.tag_configure(order.id, foreground=status_color)
            
    def edit_order(self):
        """Edita uma ordem selecionada"""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma ordem para editar")
            return
            
        # Implementar edição de ordem
        messagebox.showinfo("Editar", "Funcionalidade de edição em desenvolvimento")
        
    def cancel_order(self):
        """Cancela uma ordem selecionada"""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma ordem para cancelar")
            return
            
        item = selection[0]
        order_id = self.orders_tree.item(item, "tags")[0]
        
        # Encontrar e cancelar ordem
        for order in self.orders:
            if order.id == order_id and order.status in [OrderStatus.PENDING, OrderStatus.OPEN]:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
                logger.info(f"Ordem cancelada: {order_id}")
                self.refresh_orders()
                messagebox.showinfo("Sucesso", f"Ordem {order_id} cancelada")
                return
                
        messagebox.showwarning("Aviso", "Ordem não pode ser cancelada")
        
    def clear_orders(self):
        """Limpa todas as ordens concluídas"""
        # Manter apenas ordens pendentes/abertas
        self.orders = [o for o in self.orders if o.status in [OrderStatus.PENDING, OrderStatus.OPEN]]
        self.refresh_orders()
        logger.info("Ordens concluídas limpas")
        
    def toggle_trading(self):
        """Alterna o estado do trading"""
        if self.simulation_running:
            self.simulation_running = False
            self.trading_status.config(
                text="⏸️ TRADING PAUSADO",
                fg=self.colors['accent_orange']
            )
        else:
            self.simulation_running = True
            self.trading_status.config(
                text="🟢 TRADING ATIVO",
                fg=self.colors['accent_green']
            )
            self.start_simulation()
            
    def refresh_data(self):
        """Atualiza todos os dados"""
        self.refresh_orders()
        self.update_market_display()
        self.update_positions_display()
        logger.info("Dados atualizados")
        
    def generate_report(self):
        """Gera relatório de trading"""
        try:
            # Calcular métricas
            total_trades = len([o for o in self.orders if o.status == OrderStatus.FILLED])
            winning_trades = len([o for o in self.orders if o.status == OrderStatus.FILLED and 
                                 ((o.side == OrderSide.BUY and o.average_price) or 
                                  (o.side == OrderSide.SELL and o.average_price))])
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calcular P&L total das posições
            total_pnl = sum(p.unrealized_pnl for p in self.positions.values())
            
            # Criar relatório
            report = {
                "generated_at": datetime.now().isoformat(),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "win_rate": win_rate,
                "open_positions": len(self.positions),
                "total_pnl": total_pnl,
                "positions": [
                    {
                        "symbol": p.symbol,
                        "quantity": p.quantity,
                        "entry_price": p.entry_price,
                        "current_price": p.current_price,
                        "pnl": p.unrealized_pnl,
                        "pnl_percent": p.unrealized_pnl_percent
                    }
                    for p in self.positions.values()
                ]
            }
            
            # Mostrar resumo
            summary = f"""
            📊 RELATÓRIO DE TRADING
            
            Total de Trades: {total_trades}
            Trades Lucrativos: {winning_trades}
            Taxa de Acerto: {win_rate:.1f}%
            
            Posições Abertas: {len(self.positions)}
            P&L Total: ${total_pnl:,.2f}
            
            Deseja exportar o relatório completo?
            """
            
            response = messagebox.askyesno("Relatório", summary)
            
            if response:
                # Exportar para arquivo
                filename = f"trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                    
                messagebox.showinfo("Exportado", f"Relatório exportado para: {filename}")
                
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Falha ao gerar relatório: {e}")
            
    def on_close(self):
        """Limpeza ao fechar a janela"""
        self.simulation_running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2)