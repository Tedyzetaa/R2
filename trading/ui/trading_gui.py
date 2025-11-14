import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use('Agg')  # Usa backend não-interativo para evitar conflitos
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
import logging
import json
import os
import csv

class TradingGUI:
    """Interface gráfica de trading com histórico completo"""
    
    def __init__(self, parent, trading_engine, audio_processor):
        self.parent = parent
        self.trading_engine = trading_engine
        self.audio_processor = audio_processor
        self.logger = logging.getLogger(__name__)
        
        # Arquivos para salvar o histórico
        self.history_file = "trading_history.json"
        self.csv_file = "trading_history.csv"
        self.load_trading_history()
        
        self.setup_ui()
        
    def load_trading_history(self):
        """Carrega o histórico de trades do arquivo"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.saved_history = json.load(f)
                self.logger.info(f"Histórico carregado: {len(self.saved_history)} trades")
            else:
                self.saved_history = []
                self.logger.info("Novo arquivo de histórico criado")
        except Exception as e:
            self.logger.error(f"Erro ao carregar histórico: {e}")
            self.saved_history = []
    
    def save_trade_to_history(self, trade_info):
        """Salva um trade no histórico"""
        try:
            # Adiciona informações adicionais
            trade_with_metrics = trade_info.copy()
            trade_with_metrics['saved_at'] = datetime.now().isoformat()
            
            # Calcula P&L se for uma venda e houver compra correspondente
            if trade_info['side'] == 'SELL':
                # Procura pela compra correspondente
                for saved_trade in reversed(self.saved_history):
                    if (saved_trade['symbol'] == trade_info['symbol'] and 
                        saved_trade['side'] == 'BUY' and
                        'pnl' not in saved_trade):
                        
                        buy_price = saved_trade['price']
                        sell_price = trade_info['price']
                        quantity = trade_info['quantity']
                        
                        # Calcula P&L
                        pnl = (sell_price - buy_price) * quantity
                        pnl_percent = ((sell_price - buy_price) / buy_price) * 100
                        
                        trade_with_metrics['pnl'] = pnl
                        trade_with_metrics['pnl_percent'] = pnl_percent
                        trade_with_metrics['buy_price'] = buy_price
                        break
            
            self.saved_history.append(trade_with_metrics)
            
            # Salva em JSON
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_history, f, indent=2, ensure_ascii=False)
            
            # Salva em CSV
            self.save_to_csv(trade_with_metrics)
            
            self.logger.info(f"Trade salvo no histórico: {trade_info['symbol']} {trade_info['side']}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar trade no histórico: {e}")
    
    def save_to_csv(self, trade_info):
        """Salva trade no arquivo CSV"""
        try:
            file_exists = os.path.exists(self.csv_file)
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    # Cabeçalho
                    writer.writerow([
                        'Data', 'Symbol', 'Side', 'Quantidade', 'Preço', 
                        'Estratégia', 'P&L', 'P&L %', 'Preço Compra'
                    ])
                
                # Dados
                writer.writerow([
                    trade_info['timestamp'],
                    trade_info['symbol'],
                    trade_info['side'],
                    trade_info['quantity'],
                    trade_info['price'],
                    trade_info.get('strategy', 'Manual'),
                    trade_info.get('pnl', 0),
                    trade_info.get('pnl_percent', 0),
                    trade_info.get('buy_price', 0)
                ])
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {e}")
    
    def setup_ui(self):
        """Configura a interface"""
        # Frame principal
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = ttk.Label(
            self.main_frame, 
            text="📈 R2 TRADING DASHBOARD - MODO REAL", 
            font=('Arial', 16, 'bold'),
            foreground='red'
        )
        title_label.pack(pady=10)
        
        # Aviso de modo real
        warning_frame = ttk.Frame(self.main_frame)
        warning_frame.pack(fill=tk.X, pady=5)
        
        warning_label = ttk.Label(
            warning_frame,
            text="⚠️ TRADING COM DINHEIRO REAL - USE COM CUIDADO!",
            font=('Arial', 10, 'bold'),
            foreground='red',
            background='yellow'
        )
        warning_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Painel de status
        self.setup_status_panel()
        
        # Painel de saldos
        self.setup_balance_panel()
        
        # Painel de pares ativos
        self.setup_active_pairs_panel()
        
        # Painel de gráfico
        self.setup_chart_panel()
        
        # Painel de controle
        self.setup_control_panel()
        
        # Painel de histórico recente
        self.setup_recent_history_panel()
        
        # Painel de histórico completo
        self.setup_full_history_panel()
        
        # Inicia atualização em tempo real
        self.update_interval = 5000  # 5 segundos
        self.update_display()
    
    def setup_status_panel(self):
        """Configura painel de status"""
        status_frame = ttk.LabelFrame(self.main_frame, text="📊 Status do Trading", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Grid para status
        self.status_vars = {}
        
        labels = [
            ("Estado:", "trading_ativo"),
            ("Estratégia:", "estrategia"), 
            ("Pares Ativos:", "pares_ativos"),
            ("Preço Atual:", "preco_atual"),
            ("Posições Abertas:", "posicoes_abertas"),
            ("Total Trades:", "total_trades")
        ]
        
        for i, (label, key) in enumerate(labels):
            ttk.Label(status_frame, text=label).grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value="---")
            ttk.Label(status_frame, textvariable=var, font=('Arial', 9)).grid(
                row=i//3, column=(i%3)*2+1, sticky=tk.W, padx=5, pady=2
            )
            self.status_vars[key] = var
    
    def setup_balance_panel(self):
        """Configura painel de saldos"""
        balance_frame = ttk.LabelFrame(self.main_frame, text="💰 Saldos em Tempo Real", padding=10)
        balance_frame.pack(fill=tk.X, pady=5)
        
        # Frame interno para organizar os saldos
        balance_inner_frame = ttk.Frame(balance_frame)
        balance_inner_frame.pack(fill=tk.X)
        
        # Variáveis para os saldos
        self.balance_vars = {}
        
        # Moedas principais para mostrar
        balance_assets = [
            ('USDT', 'USDT:'),
            ('BTC', 'BTC:'),
            ('ETH', 'ETH:'),
            ('BNB', 'BNB:'),
            ('DOGE', 'DOGE:'), 
            ('XNO', 'NANO:'),
            ('ADA', 'ADA:'),
            ('SHIB', 'SHIB:')
        ]
        
        # Cria labels para cada saldo
        for i, (asset, label_text) in enumerate(balance_assets):
            # Label do nome da moeda
            ttk.Label(balance_inner_frame, text=label_text, font=('Arial', 9, 'bold')).grid(
                row=i//4, column=(i%4)*2, sticky=tk.W, padx=10, pady=2
            )
            
            # Label do valor
            var = tk.StringVar(value="Carregando...")
            balance_label = ttk.Label(
                balance_inner_frame, 
                textvariable=var, 
                font=('Arial', 9),
                foreground='green'
            )
            balance_label.grid(
                row=i//4, column=(i%4)*2+1, 
                sticky=tk.W, padx=5, pady=2
            )
            self.balance_vars[asset] = var
        
        # Botão para atualizar saldos manualmente
        refresh_btn = ttk.Button(
            balance_frame, 
            text="🔄 Atualizar Saldos", 
            command=self.update_balances,
            width=15
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def setup_active_pairs_panel(self):
        """Configura painel de pares ativos"""
        self.active_pairs_frame = ttk.LabelFrame(self.main_frame, text="🎯 Pares de Trading Ativos", padding=10)
        self.active_pairs_frame.pack(fill=tk.X, pady=5)
        
        # Treeview para pares ativos
        columns = ('Par', 'Estratégia', 'Quantidade', 'Posição', 'Último Sinal', 'Preço')
        self.pairs_tree = ttk.Treeview(self.active_pairs_frame, columns=columns, show='headings', height=4)
        
        # Configura colunas
        column_widths = {
            'Par': 120,
            'Estratégia': 80,
            'Quantidade': 80,
            'Posição': 80,
            'Último Sinal': 100,
            'Preço': 100
        }
        
        for col in columns:
            self.pairs_tree.heading(col, text=col)
            self.pairs_tree.column(col, width=column_widths.get(col, 100))
        
        # Scrollbar
        pairs_scrollbar = ttk.Scrollbar(self.active_pairs_frame, orient=tk.VERTICAL, command=self.pairs_tree.yview)
        self.pairs_tree.configure(yscrollcommand=pairs_scrollbar.set)
        
        self.pairs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pairs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para botões de controle de pares
        pairs_control_frame = ttk.Frame(self.active_pairs_frame)
        pairs_control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        ttk.Button(
            pairs_control_frame,
            text="⏹️ Parar Par",
            command=self.stop_selected_pair,
            width=12
        ).pack(pady=2)
        
        ttk.Button(
            pairs_control_frame,
            text="🔄 Atualizar",
            command=self.update_active_pairs,
            width=12
        ).pack(pady=2)
        
        ttk.Button(
            pairs_control_frame,
            text="🗑️ Parar Todos",
            command=self.stop_all_pairs,
            width=12
        ).pack(pady=2)
    
    def setup_chart_panel(self):
        """Configura painel do gráfico"""
        chart_frame = ttk.LabelFrame(self.main_frame, text="📈 Gráfico em Tempo Real", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Frame para controles do gráfico
        chart_control_frame = ttk.Frame(chart_frame)
        chart_control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(chart_control_frame, text="Par do Gráfico:").pack(side=tk.LEFT, padx=5)
        
        self.chart_symbol_var = tk.StringVar(value="DOGEUSDT")
        chart_symbol_combo = ttk.Combobox(
            chart_control_frame, 
            textvariable=self.chart_symbol_var,
            values=["DOGEUSDT", "XNOUSDT", "ADAUSDT", "SHIBUSDT", "DOGEBTC", "XNOBTC", "ADABTC", "DOGEETH", "XNOETH"],
            width=12,
            state="readonly"
        )
        chart_symbol_combo.pack(side=tk.LEFT, padx=5)
        chart_symbol_combo.bind('<<ComboboxSelected>>', self.on_chart_symbol_change)
        
        ttk.Button(
            chart_control_frame,
            text="🔄 Atualizar Gráfico",
            command=self.update_chart
        ).pack(side=tk.LEFT, padx=5)
        
        # Figura do matplotlib
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Canvas para Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_control_panel(self):
        """Configura painel de controle"""
        control_frame = ttk.LabelFrame(self.main_frame, text="🎮 Controles de Trading", padding=10)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Frame para seleção de par
        symbol_frame = ttk.Frame(control_frame)
        symbol_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(symbol_frame, text="Par:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.symbol_var = tk.StringVar(value="DOGEUSDT")
        symbol_combo = ttk.Combobox(
            symbol_frame, 
            textvariable=self.symbol_var,
            values=[
                "DOGEUSDT", "XNOUSDT", "ADAUSDT", "SHIBUSDT",
                "DOGEBTC", "XNOBTC", "ADABTC", 
                "DOGEETH", "XNOETH",
                "DOGEBNB", "ADABNB"
            ],
            width=12,
            state="readonly"
        )
        symbol_combo.grid(row=0, column=1, padx=5)
        
        # Frame para estratégia e quantidade
        strategy_frame = ttk.Frame(control_frame)
        strategy_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(strategy_frame, text="Estratégia:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.strategy_var = tk.StringVar(value="sma")
        strategy_combo = ttk.Combobox(
            strategy_frame,
            textvariable=self.strategy_var,
            values=["sma", "rsi"],
            width=12,
            state="readonly"
        )
        strategy_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(strategy_frame, text="Quantidade:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.quantity_var = tk.StringVar(value="0.3")
        quantity_entry = ttk.Entry(strategy_frame, textvariable=self.quantity_var, width=8)
        quantity_entry.grid(row=0, column=3, padx=5)
        
        # Frame para botões principais
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        self.start_button = ttk.Button(
            buttons_frame, 
            text="🟢 Iniciar Trading", 
            command=self.start_trading,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            buttons_frame,
            text="🔴 Parar Trading",
            command=self.stop_trading,
            width=15
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Frame para trades manuais
        manual_frame = ttk.Frame(control_frame)
        manual_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            manual_frame,
            text="🔼 Comprar",
            command=lambda: self.manual_trade("BUY"),
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            manual_frame,
            text="🔽 Vender", 
            command=lambda: self.manual_trade("SELL"),
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            manual_frame,
            text="📊 Ver Saldos",
            command=self.update_balances,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            manual_frame,
            text="ℹ️ Status",
            command=self.show_status,
            width=12
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_recent_history_panel(self):
        """Configura painel de histórico recente"""
        history_frame = ttk.LabelFrame(self.main_frame, text="📋 Histórico de Trades Recentes", padding=10)
        history_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        
        # Treeview para histórico
        columns = ('Data', 'Symbol', 'Side', 'Quantidade', 'Preço', 'Estratégia', 'P&L')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=6)
        
        # Configura colunas
        column_widths = {
            'Data': 120,
            'Symbol': 100,
            'Side': 80,
            'Quantidade': 80,
            'Preço': 100,
            'Estratégia': 100,
            'P&L': 100
        }
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=column_widths.get(col, 100))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para botões do histórico
        history_buttons_frame = ttk.Frame(history_frame)
        history_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        ttk.Button(
            history_buttons_frame,
            text="📊 Estatísticas",
            command=self.show_statistics,
            width=12
        ).pack(pady=2)
        
        ttk.Button(
            history_buttons_frame,
            text="💾 Exportar CSV",
            command=self.export_history_csv,
            width=12
        ).pack(pady=2)
        
        ttk.Button(
            history_buttons_frame,
            text="🗑️ Limpar Histórico",
            command=self.clear_history,
            width=12
        ).pack(pady=2)
    
    def setup_full_history_panel(self):
        """Configura painel de histórico completo"""
        full_history_frame = ttk.LabelFrame(self.main_frame, text="📊 Histórico Completo de Trading", padding=10)
        full_history_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        
        # Treeview para histórico completo
        columns = ('Data', 'Symbol', 'Side', 'Quantidade', 'Preço', 'Estratégia', 'P&L', 'P&L %')
        self.full_history_tree = ttk.Treeview(full_history_frame, columns=columns, show='headings', height=6)
        
        # Configura colunas
        column_widths = {
            'Data': 120,
            'Symbol': 100,
            'Side': 80,
            'Quantidade': 80,
            'Preço': 100,
            'Estratégia': 100,
            'P&L': 100,
            'P&L %': 80
        }
        
        for col in columns:
            self.full_history_tree.heading(col, text=col)
            self.full_history_tree.column(col, width=column_widths.get(col, 100))
        
        # Scrollbar
        full_scrollbar = ttk.Scrollbar(full_history_frame, orient=tk.VERTICAL, command=self.full_history_tree.yview)
        self.full_history_tree.configure(yscrollcommand=full_scrollbar.set)
        
        self.full_history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        full_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Carrega histórico salvo
        self.load_full_history()
    
    def load_full_history(self):
        """Carrega o histórico completo salvo"""
        try:
            # Limpa treeview
            for item in self.full_history_tree.get_children():
                self.full_history_tree.delete(item)
            
            # Adiciona trades do histórico salvo
            for trade in reversed(self.saved_history[-50:]):  # Últimos 50 trades
                # Formata a data
                trade_time = datetime.fromisoformat(trade['timestamp'])
                data_formatada = trade_time.strftime('%d/%m %H:%M:%S')
                
                # Formata o lado (BUY/SELL) com cores
                side = trade['side']
                side_display = f"🟢 {side}" if side == "BUY" else f"🔴 {side}"
                
                # Formata P&L
                pnl = trade.get('pnl', 0)
                pnl_percent = trade.get('pnl_percent', 0)
                
                if pnl > 0:
                    pnl_display = f"🟢 ${pnl:.2f}"
                    pnl_percent_display = f"🟢 {pnl_percent:.2f}%"
                elif pnl < 0:
                    pnl_display = f"🔴 ${pnl:.2f}"
                    pnl_percent_display = f"🔴 {pnl_percent:.2f}%"
                else:
                    pnl_display = f"${pnl:.2f}"
                    pnl_percent_display = f"{pnl_percent:.2f}%"
                
                self.full_history_tree.insert('', 0, values=(
                    data_formatada,
                    trade['symbol'],
                    side_display,
                    trade['quantity'],
                    f"{trade['price']:.6f}",
                    trade.get('strategy', 'Manual'),
                    pnl_display,
                    pnl_percent_display
                ))
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar histórico completo: {e}")
    
    def on_chart_symbol_change(self, event=None):
        """Callback quando o símbolo do gráfico é alterado"""
        self.update_chart()
    
    def start_trading(self):
        """Inicia trading automático"""
        try:
            symbol = self.symbol_var.get()
            strategy = self.strategy_var.get()
            quantity = float(self.quantity_var.get())
            
            # Confirmação para trading real
            if not messagebox.askyesno(
                "Confirmação - DINHEIRO REAL", 
                f"⚠️ ISSO FARÁ TRADING COM DINHEIRO REAL!\n\n"
                f"Par: {symbol}\n"
                f"Estratégia: {strategy}\n"
                f"Quantidade: {quantity}\n\n"
                f"Tem certeza que deseja continuar?"
            ):
                return
            
            success = self.trading_engine.start_auto_trading(strategy, symbol, quantity)
            
            if success:
                messagebox.showinfo("Sucesso", f"Trading REAL iniciado: {strategy} - {symbol}")
                if self.audio_processor:
                    self.audio_processor.text_to_speech(f"Trading automático ativado para {symbol}")
                # Atualiza a lista de pares ativos
                self.update_active_pairs()
            else:
                messagebox.showerror("Erro", "Não foi possível iniciar o trading")
                
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar trading: {e}")
    
    def stop_trading(self):
        """Para todo o trading automático"""
        if messagebox.askyesno("Confirmar", "Parar TODO o trading automático?"):
            self.trading_engine.stop_auto_trading()
            messagebox.showinfo("Info", "Todo o trading automático parado")
            if self.audio_processor:
                self.audio_processor.text_to_speech("Trading automático desativado")
            # Atualiza a lista de pares ativos
            self.update_active_pairs()
    
    def stop_selected_pair(self):
        """Para o par selecionado na treeview"""
        selection = self.pairs_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um par para parar")
            return
        
        item = selection[0]
        symbol = self.pairs_tree.item(item, 'values')[0]
        
        if messagebox.askyesno("Confirmar", f"Parar trading para {symbol}?"):
            self.trading_engine.stop_auto_trading(symbol)
            messagebox.showinfo("Sucesso", f"Trading parado para {symbol}")
            self.update_active_pairs()
    
    def stop_all_pairs(self):
        """Para todos os pares de trading"""
        if messagebox.askyesno("Confirmar", "Parar TODOS os pares de trading?"):
            self.trading_engine.stop_auto_trading()
            messagebox.showinfo("Sucesso", "Todos os pares de trading parados")
            self.update_active_pairs()
    
    def manual_trade(self, side: str):
        """Executa trade manual"""
        try:
            symbol = self.symbol_var.get()
            quantity = float(self.quantity_var.get())
            
            # Confirmação para trading real
            if not messagebox.askyesno(
                "Confirmação - DINHEIRO REAL", 
                f"⚠️ ORDEM MANUAL COM DINHEIRO REAL!\n\n"
                f"Tipo: {side}\n"
                f"Par: {symbol}\n"
                f"Quantidade: {quantity}\n\n"
                f"Executar esta ordem?"
            ):
                return
            
            success = self.trading_engine.manual_trade(symbol, side, quantity)
            
            if success:
                messagebox.showinfo("Sucesso", f"Ordem {side} executada para {symbol}")
                if self.audio_processor:
                    self.audio_processor.text_to_speech(f"Ordem de {side.lower()} executada")
                # Atualiza saldos após o trade
                self.update_balances()
                # Atualiza histórico
                self.update_history()
                # Salva no histórico
                recent_trades = self.trading_engine.trade_history
                if recent_trades:
                    self.save_trade_to_history(recent_trades[-1])
                    self.load_full_history()
            else:
                messagebox.showerror("Erro", f"Falha na ordem {side}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no trade manual: {e}")
    
    def show_status(self):
        """Mostra status detalhado do trading"""
        try:
            status = self.trading_engine.get_status()
            
            status_text = f"📊 Status do Trading - MODO REAL\n\n"
            status_text += f"🔄 Trading Ativo: {'SIM' if status['trading_ativo'] else 'NÃO'}\n"
            status_text += f"📈 Pares Ativos: {len(status['pares_ativos'])}\n"
            status_text += f"💰 Posições Abertas: {status['trades_ativos']}\n"
            status_text += f"📋 Total de Trades: {status['total_historico_trades']}\n\n"
            
            if status['pares_detalhes']:
                status_text += "Pares Ativos:\n"
                for symbol, detalhes in status['pares_detalhes'].items():
                    status_text += f"  • {symbol}: {detalhes['estrategia']} "
                    status_text += f"(Posição: {'ABERTA' if detalhes['posicao_aberta'] else 'FECHADA'})\n"
                    if detalhes['preco_atual']:
                        status_text += f"    Preço: {detalhes['preco_atual']:.6f}\n"
            
            messagebox.showinfo("Status do Trading", status_text)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter status: {e}")
    
    def show_statistics(self):
        """Mostra estatísticas do trading"""
        try:
            if not self.saved_history:
                messagebox.showinfo("Estatísticas", "Nenhum trade no histórico")
                return
            
            total_trades = len(self.saved_history)
            buy_trades = len([t for t in self.saved_history if t['side'] == 'BUY'])
            sell_trades = len([t for t in self.saved_history if t['side'] == 'SELL'])
            
            # Calcula P&L total
            total_pnl = sum(t.get('pnl', 0) for t in self.saved_history)
            profitable_trades = len([t for t in self.saved_history if t.get('pnl', 0) > 0])
            win_rate = (profitable_trades / sell_trades * 100) if sell_trades > 0 else 0
            
            stats_text = f"📈 Estatísticas de Trading\n\n"
            stats_text += f"📊 Total de Trades: {total_trades}\n"
            stats_text += f"🟢 Compras: {buy_trades}\n"
            stats_text += f"🔴 Vendas: {sell_trades}\n"
            stats_text += f"💰 P&L Total: ${total_pnl:.2f}\n"
            stats_text += f"🎯 Win Rate: {win_rate:.1f}%\n"
            stats_text += f"✅ Trades Lucrativos: {profitable_trades}\n"
            
            # Últimos 5 trades
            stats_text += f"\n📋 Últimos 5 Trades:\n"
            for trade in self.saved_history[-5:]:
                side = "🟢 COMPRA" if trade['side'] == 'BUY' else "🔴 VENDA"
                pnl = trade.get('pnl', 0)
                pnl_display = f"+${pnl:.2f}" if pnl > 0 else f"${pnl:.2f}"
                stats_text += f"  {trade['symbol']} {side} {pnl_display}\n"
            
            messagebox.showinfo("Estatísticas", stats_text)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao calcular estatísticas: {e}")
    
    def export_history_csv(self):
        """Exporta histórico para CSV"""
        try:
            if not self.saved_history:
                messagebox.showwarning("Aviso", "Nenhum trade para exportar")
                return
            
            # Usa o arquivo CSV já existente
            if os.path.exists(self.csv_file):
                messagebox.showinfo("Sucesso", f"Histórico exportado para: {self.csv_file}")
            else:
                messagebox.showinfo("Sucesso", f"Arquivo CSV criado: {self.csv_file}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar CSV: {e}")
    
    def clear_history(self):
        """Limpa o histórico de trades"""
        if messagebox.askyesno("Confirmar", "Limpar TODO o histórico de trades?"):
            self.saved_history = []
            try:
                if os.path.exists(self.history_file):
                    os.remove(self.history_file)
                if os.path.exists(self.csv_file):
                    os.remove(self.csv_file)
                messagebox.showinfo("Sucesso", "Histórico limpo")
                self.load_full_history()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao limpar histórico: {e}")
    
    def update_display(self):
        """Atualiza a exibição em tempo real"""
        try:
            # Atualiza status
            status = self.trading_engine.get_status()
            
            # Status geral
            self.status_vars['trading_ativo'].set("🟢 ATIVO" if status['trading_ativo'] else "🔴 PARADO")
            self.status_vars['estrategia'].set("Múltiplas" if status['trading_ativo'] else "Nenhuma")
            self.status_vars['pares_ativos'].set(f"{len(status['pares_ativos'])} pares")
            self.status_vars['posicoes_abertas'].set(f"{status['trades_ativos']} abertas")
            self.status_vars['total_trades'].set(str(status['total_historico_trades']))
            
            # Preço do par selecionado no gráfico
            if self.chart_symbol_var.get():
                preco = self.trading_engine.binance_client.get_ticker_price(self.chart_symbol_var.get())
                self.status_vars['preco_atual'].set(f"{preco:.6f}" if preco else "N/A")
            else:
                self.status_vars['preco_atual'].set("N/A")
            
            # Atualiza histórico recente
            self.update_history()
            
            # Atualiza pares ativos a cada 2 ciclos (10 segundos)
            if hasattr(self, 'update_counter'):
                self.update_counter += 1
            else:
                self.update_counter = 0
                
            if self.update_counter % 2 == 0:
                self.update_active_pairs()
            
            # Atualiza gráfico
            self.update_chart()
            
            # Atualiza saldos a cada 3 ciclos (15 segundos)
            if self.update_counter % 3 == 0:
                self.update_balances()
            
            # Atualiza histórico completo a cada 5 ciclos (25 segundos)
            if self.update_counter % 5 == 0:
                self.load_full_history()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar display: {e}")
        
        # Agenda próxima atualização
        self.parent.after(self.update_interval, self.update_display)
    
    def update_balances(self):
        """Atualiza os saldos em tempo real"""
        try:
            if not self.trading_engine:
                return
                
            # Obtém informações da conta
            balances = self.trading_engine.get_account_balances()
            if not balances:
                return
            
            # Atualiza cada saldo
            for asset, var in self.balance_vars.items():
                if asset in balances:
                    balance_info = balances[asset]
                    total_balance = balance_info['total']
                    
                    # Formata o saldo baseado no tipo de moeda
                    if asset in ['USDT', 'BUSD']:
                        display_text = f"${total_balance:,.2f}"
                    elif asset in ['BTC', 'ETH']:
                        display_text = f"{total_balance:,.6f}"
                    elif asset in ['DOGE', 'XNO', 'ADA']:
                        display_text = f"{total_balance:,.4f}"
                    elif asset == 'SHIB':
                        display_text = f"{total_balance:,.0f}"
                    elif asset == 'BNB':
                        display_text = f"{total_balance:,.4f}"
                    else:
                        display_text = f"{total_balance:,.4f}"
                    
                    # Adiciona indicação se há saldo bloqueado em ordens
                    if balance_info['locked'] > 0:
                        display_text += f" (🔒{balance_info['locked']:.4f})"
                    
                    var.set(display_text)
                else:
                    var.set("0")
                    
        except Exception as e:
            self.logger.error(f"Erro ao atualizar saldos: {e}")
            # Define valores de erro
            for asset in self.balance_vars:
                self.balance_vars[asset].set("Erro")
    
    def update_active_pairs(self):
        """Atualiza a lista de pares ativos"""
        try:
            # Limpa treeview
            for item in self.pairs_tree.get_children():
                self.pairs_tree.delete(item)
            
            # Obtém status atual
            status = self.trading_engine.get_status()
            
            # Adiciona pares ativos
            for symbol, detalhes in status['pares_detalhes'].items():
                # Formata a posição
                posicao = "🟢 ABERTA" if detalhes['posicao_aberta'] else "🔴 FECHADA"
                
                # Formata o último sinal
                ultimo_sinal = detalhes['ultimo_sinal'] or "Nenhum"
                
                # Formata o preço
                preco_text = f"{detalhes['preco_atual']:.6f}" if detalhes['preco_atual'] else "N/A"
                
                self.pairs_tree.insert('', 'end', values=(
                    symbol,
                    detalhes['estrategia'],
                    detalhes['quantidade'],
                    posicao,
                    ultimo_sinal,
                    preco_text
                ))
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar pares ativos: {e}")
    
    def update_history(self):
        """Atualiza histórico de trades recentes"""
        try:
            # Limpa treeview
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # Adiciona trades recentes (últimos 15)
            recent_trades = self.trading_engine.trade_history[-15:]
            
            for trade in reversed(recent_trades):
                # Formata o lado (BUY/SELL) com cores
                side = trade['side']
                side_display = f"🟢 {side}" if side == "BUY" else f"🔴 {side}"
                
                # Formata a data
                trade_time = trade['timestamp']
                if isinstance(trade_time, str):
                    trade_time = datetime.fromisoformat(trade_time)
                data_formatada = trade_time.strftime('%H:%M:%S')
                
                self.history_tree.insert('', 0, values=(
                    data_formatada,
                    trade['symbol'],
                    side_display,
                    trade['quantity'],
                    f"{trade['price']:.6f}",
                    trade.get('strategy', 'Manual'),
                    f"${trade.get('pnl', 0):.2f}" if trade.get('pnl') else "-"
                ))
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar histórico: {e}")
    
    def update_chart(self):
        """Atualiza gráfico de preços"""
        try:
            symbol = self.chart_symbol_var.get()
            if not symbol:
                return
                
            klines = self.trading_engine.binance_client.get_klines(symbol, '1m', 50)
            
            if not klines:
                return
            
            # Extrai dados para o gráfico
            times = [datetime.fromtimestamp(candle[0] / 1000) for candle in klines]
            opens = [float(candle[1]) for candle in klines]
            highs = [float(candle[2]) for candle in klines]
            lows = [float(candle[3]) for candle in klines]
            closes = [float(candle[4]) for candle in klines]
            
            # Limpa e plota novo gráfico
            self.ax.clear()
            
            # Gráfico de linha simplificado
            self.ax.plot(times, closes, color='blue', linewidth=1, label='Preço')
            
            # Adiciona médias móveis se disponível
            if len(closes) >= 21:
                import pandas as pd
                df = pd.DataFrame({'close': closes})
                sma_21 = df['close'].rolling(21).mean()
                sma_13 = df['close'].rolling(13).mean()
                
                self.ax.plot(times[-len(sma_21):], sma_21, color='orange', linewidth=1, label='SMA 21')
                self.ax.plot(times[-len(sma_13):], sma_13, color='red', linewidth=1, label='SMA 13')
            
            self.ax.set_title(f'{symbol} - Preços em Tempo Real (MODO REAL)')
            self.ax.set_ylabel('Preço')
            self.ax.legend()
            self.ax.grid(True, alpha=0.3)
            
            # Formata eixo x
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            self.fig.autofmt_xdate()
            
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar gráfico: {e}")