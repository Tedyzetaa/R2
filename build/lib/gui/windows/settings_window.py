"""
Janela de Configurações - Interface para configuração do sistema
Design inspirado em painéis de controle de naves espaciais
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
import os
import configparser
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)

class SettingType(Enum):
    """Tipos de configurações disponíveis"""
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    SELECT = "select"
    FILE = "file"
    FOLDER = "folder"
    COLOR = "color"

@dataclass
class SettingOption:
    """Opção para configurações do tipo select"""
    label: str
    value: Any
    description: str = ""

@dataclass
class SettingItem:
    """Item de configuração individual"""
    key: str
    name: str
    description: str
    type: SettingType
    value: Any
    default: Any
    options: List[SettingOption] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    category: str = "general"
    advanced: bool = False
    requires_restart: bool = False

class SettingsWindow:
    """Janela de configurações do sistema com estilo Sci-Fi"""
    
    def __init__(self, parent, config: Dict[str, Any]):
        """
        Inicializa a janela de configurações
        
        Args:
            parent: Widget pai
            config: Configuração da aplicação
        """
        self.parent = parent
        self.app_config = config
        self.settings: Dict[str, SettingItem] = {}
        self.original_values: Dict[str, Any] = {}
        
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
            'success': '#00cc66',
            'warning': '#ffcc00',
            'error': '#ff3366'
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
        self.load_settings()
        
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal
        self.main_frame = tk.Frame(
            self.parent,
            bg=self.colors['bg_dark'],
            padx=20,
            pady=20
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho
        self.create_header()
        
        # Corpo principal
        self.create_main_body()
        
        # Rodapé
        self.create_footer()
        
    def create_header(self):
        """Cria o cabeçalho da janela"""
        header_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark']
        )
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Ícone e título
        icon_label = tk.Label(
            header_frame,
            text="⚙️",
            font=('Segoe UI', 32),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_blue']
        )
        icon_label.pack(side=tk.LEFT)
        
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        title_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            title_frame,
            text="CONFIGURAÇÕES DO SISTEMA",
            font=self.fonts['title'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary']
        ).pack(anchor='w')
        
        tk.Label(
            title_frame,
            text="Painel de controle e personalização do R2 Assistant",
            font=self.fonts['small'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_secondary']
        ).pack(anchor='w', pady=(2, 0))
        
        # Separador
        separator = tk.Frame(
            header_frame,
            height=2,
            bg=self.colors['accent_blue']
        )
        separator.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
    def create_main_body(self):
        """Cria o corpo principal da janela"""
        body_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark']
        )
        body_frame.pack(fill=tk.BOTH, expand=True)
        
        # Painel esquerdo - Navegação
        self.create_navigation_panel(body_frame)
        
        # Painel direito - Conteúdo
        self.create_content_panel(body_frame)
        
    def create_navigation_panel(self, parent):
        """Cria o painel de navegação lateral"""
        nav_frame = tk.Frame(
            parent,
            bg=self.colors['bg_medium'],
            width=200,
            relief=tk.RAISED,
            borderwidth=1
        )
        nav_frame.pack(side=tk.LEFT, fill=tk.Y)
        nav_frame.pack_propagate(False)
        
        tk.Label(
            nav_frame,
            text="CATEGORIAS",
            font=self.fonts['heading'],
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_blue'],
            pady=15
        ).pack(fill=tk.X)
        
        # Lista de categorias
        self.categories = {
            "geral": "⚙️ Geral",
            "interface": "🎨 Interface",
            "ia": "🤖 Inteligência Artificial",
            "trading": "📈 Trading",
            "seguranca": "🔒 Segurança",
            "rede": "🌐 Rede",
            "avancado": "⚡ Avançado"
        }
        
        self.category_buttons = {}
        self.current_category = "geral"
        
        for key, label in self.categories.items():
            btn = tk.Button(
                nav_frame,
                text=label,
                font=self.fonts['normal'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_blue'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                anchor='w',
                padx=20,
                pady=10,
                command=lambda k=key: self.switch_category(k)
            )
            btn.pack(fill=tk.X)
            self.category_buttons[key] = btn
            
        # Separador
        separator = tk.Frame(
            nav_frame,
            height=1,
            bg=self.colors['border']
        )
        separator.pack(fill=tk.X, pady=20)
        
        # Ações rápidas
        tk.Label(
            nav_frame,
            text="AÇÕES RÁPIDAS",
            font=self.fonts['small'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary'],
            pady=(0, 10)
        ).pack(fill=tk.X, padx=20)
        
        quick_actions = [
            ("🔄 Restaurar Padrões", self.reset_to_defaults),
            ("💾 Salvar Config", self.save_settings),
            ("📤 Exportar Config", self.export_settings),
            ("📥 Importar Config", self.import_settings)
        ]
        
        for text, command in quick_actions:
            btn = tk.Button(
                nav_frame,
                text=text,
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_purple'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                padx=15,
                pady=8,
                command=command
            )
            btn.pack(fill=tk.X, padx=10, pady=2)
            
    def create_content_panel(self, parent):
        """Cria o painel de conteúdo das configurações"""
        # Frame principal
        content_frame = tk.Frame(
            parent,
            bg=self.colors['bg_dark']
        )
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))
        
        # Canvas para scroll
        self.content_canvas = tk.Canvas(
            content_frame,
            bg=self.colors['bg_dark'],
            highlightthickness=0
        )
        
        scrollbar = ttk.Scrollbar(
            content_frame,
            orient=tk.VERTICAL,
            command=self.content_canvas.yview
        )
        
        self.settings_frame = tk.Frame(
            self.content_canvas,
            bg=self.colors['bg_dark']
        )
        
        self.settings_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        )
        
        self.content_canvas.create_window(
            (0, 0),
            window=self.settings_frame,
            anchor="nw"
        )
        
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar scroll com mouse
        self.content_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Inicializar com categoria geral
        self.show_category("geral")
        
    def _on_mousewheel(self, event):
        """Manipula scroll do mouse"""
        self.content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def create_footer(self):
        """Cria o rodapé da janela"""
        footer_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_light'],
            height=50
        )
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        footer_frame.pack_propagate(False)
        
        # Status
        self.status_label = tk.Label(
            footer_frame,
            text="Configurações carregadas",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Botões de ação
        actions_frame = tk.Frame(footer_frame, bg=self.colors['bg_light'])
        actions_frame.pack(side=tk.RIGHT, padx=20)
        
        action_buttons = [
            ("❌ Cancelar", self.cancel_changes),
            ("💾 Aplicar", self.apply_changes),
            ("✅ Salvar e Sair", self.save_and_close)
        ]
        
        for text, command in action_buttons:
            btn = tk.Button(
                actions_frame,
                text=text,
                font=self.fonts['normal'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_blue'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                padx=15,
                pady=8,
                command=command
            )
            btn.pack(side=tk.LEFT, padx=5)
            
    def load_settings(self):
        """Carrega as configurações do sistema"""
        try:
            # Configurações de exemplo
            settings_list = [
                SettingItem(
                    key="theme",
                    name="Tema da Interface",
                    description="Selecione o tema visual da aplicação",
                    type=SettingType.SELECT,
                    value="dark",
                    default="dark",
                    options=[
                        SettingOption("Escuro (Padrão)", "dark"),
                        SettingOption("Azul Escuro", "blue_dark"),
                        SettingOption("Matrix", "matrix"),
                        SettingOption("Cyberpunk", "cyberpunk")
                    ],
                    category="interface"
                ),
                SettingItem(
                    key="auto_update",
                    name="Atualização Automática",
                    description="Buscar atualizações automaticamente",
                    type=SettingType.BOOLEAN,
                    value=True,
                    default=True,
                    category="geral"
                ),
                SettingItem(
                    key="update_interval",
                    name="Intervalo de Atualização",
                    description="Intervalo para verificar atualizações (minutos)",
                    type=SettingType.INTEGER,
                    value=60,
                    default=60,
                    min_value=5,
                    max_value=1440,
                    step=5,
                    category="geral",
                    requires_restart=True
                ),
                SettingItem(
                    key="ai_model",
                    name="Modelo de IA",
                    description="Modelo de inteligência artificial a ser utilizado",
                    type=SettingType.SELECT,
                    value="gpt-4",
                    default="gpt-4",
                    options=[
                        SettingOption("GPT-4 (Recomendado)", "gpt-4"),
                        SettingOption("GPT-3.5 Turbo", "gpt-3.5-turbo"),
                        SettingOption("Claude 2", "claude-2"),
                        SettingOption("Local Llama", "llama-local")
                    ],
                    category="ia",
                    requires_restart=True
                ),
                SettingItem(
                    key="max_tokens",
                    name="Máximo de Tokens",
                    description="Número máximo de tokens por resposta",
                    type=SettingType.INTEGER,
                    value=2000,
                    default=2000,
                    min_value=100,
                    max_value=8000,
                    step=100,
                    category="ia"
                ),
                SettingItem(
                    key="trading_enabled",
                    name="Trading Automático",
                    description="Habilitar execução automática de trades",
                    type=SettingType.BOOLEAN,
                    value=False,
                    default=False,
                    category="trading"
                ),
                SettingItem(
                    key="risk_per_trade",
                    name="Risco por Trade",
                    description="Porcentagem de risco máximo por operação",
                    type=SettingType.FLOAT,
                    value=2.0,
                    default=2.0,
                    min_value=0.1,
                    max_value=10.0,
                    step=0.1,
                    category="trading"
                ),
                SettingItem(
                    key="api_key",
                    name="Chave API",
                    description="Chave de API para serviços externos",
                    type=SettingType.STRING,
                    value="",
                    default="",
                    category="seguranca"
                ),
                SettingItem(
                    key="log_level",
                    name="Nível de Log",
                    description="Nível de detalhamento dos logs",
                    type=SettingType.SELECT,
                    value="INFO",
                    default="INFO",
                    options=[
                        SettingOption("DEBUG", "DEBUG"),
                        SettingOption("INFO", "INFO"),
                        SettingOption("WARNING", "WARNING"),
                        SettingOption("ERROR", "ERROR")
                    ],
                    category="avancado",
                    requires_restart=True
                ),
                SettingItem(
                    key="cache_size",
                    name="Tamanho do Cache",
                    description="Tamanho máximo do cache em MB",
                    type=SettingType.INTEGER,
                    value=1024,
                    default=1024,
                    min_value=64,
                    max_value=8192,
                    step=64,
                    category="avancado",
                    requires_restart=True
                ),
                SettingItem(
                    key="data_folder",
                    name="Pasta de Dados",
                    description="Localização da pasta de dados do sistema",
                    type=SettingType.FOLDER,
                    value=os.path.expanduser("~/r2_assistant_data"),
                    default=os.path.expanduser("~/r2_assistant_data"),
                    category="geral"
                )
            ]
            
            # Converter para dicionário
            self.settings = {setting.key: setting for setting in settings_list}
            
            # Salvar valores originais
            self.original_values = {key: setting.value for key, setting in self.settings.items()}
            
            logger.info(f"Carregadas {len(self.settings)} configurações")
            self.update_status("Configurações carregadas com sucesso", "success")
            
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            self.update_status(f"Erro ao carregar configurações: {e}", "error")
            
    def show_category(self, category: str):
        """Exibe as configurações de uma categoria específica"""
        # Atualizar botão ativo
        for key, btn in self.category_buttons.items():
            if key == category:
                btn.config(bg=self.colors['accent_blue'], fg=self.colors['text_primary'])
            else:
                btn.config(bg=self.colors['bg_medium'], fg=self.colors['text_primary'])
                
        self.current_category = category
        
        # Limpar frame de configurações
        for widget in self.settings_frame.winfo_children():
            widget.destroy()
            
        # Filtrar configurações por categoria
        category_settings = [
            setting for setting in self.settings.values()
            if setting.category == category
        ]
        
        if not category_settings:
            # Mensagem para categoria vazia
            tk.Label(
                self.settings_frame,
                text="Nenhuma configuração disponível nesta categoria",
                font=self.fonts['normal'],
                bg=self.colors['bg_dark'],
                fg=self.colors['text_secondary']
            ).pack(pady=50)
            return
            
        # Criar widgets para cada configuração
        for i, setting in enumerate(category_settings):
            self.create_setting_widget(self.settings_frame, setting, i)
            
    def create_setting_widget(self, parent, setting: SettingItem, index: int):
        """Cria o widget para uma configuração específica"""
        # Frame da configuração
        setting_frame = tk.Frame(
            parent,
            bg=self.colors['bg_medium'],
            padx=15,
            pady=10
        )
        setting_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Cabeçalho
        header_frame = tk.Frame(setting_frame, bg=self.colors['bg_medium'])
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Nome
        name_label = tk.Label(
            header_frame,
            text=setting.name,
            font=self.fonts['heading'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary'],
            anchor='w'
        )
        name_label.pack(side=tk.LEFT)
        
        # Indicador de reinício necessário
        if setting.requires_restart:
            tk.Label(
                header_frame,
                text="🔄 Reinício necessário",
                font=self.fonts['small'],
                bg=self.colors['bg_medium'],
                fg=self.colors['accent_orange']
            ).pack(side=tk.RIGHT, padx=(10, 0))
            
        # Descrição
        tk.Label(
            setting_frame,
            text=setting.description,
            font=self.fonts['small'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary'],
            wraplength=600,
            justify=tk.LEFT
        ).pack(anchor='w', pady=(0, 10))
        
        # Widget de controle baseado no tipo
        control_frame = tk.Frame(setting_frame, bg=self.colors['bg_medium'])
        control_frame.pack(fill=tk.X)
        
        if setting.type == SettingType.BOOLEAN:
            self.create_boolean_control(control_frame, setting)
        elif setting.type == SettingType.INTEGER or setting.type == SettingType.FLOAT:
            self.create_numeric_control(control_frame, setting)
        elif setting.type == SettingType.STRING:
            self.create_string_control(control_frame, setting)
        elif setting.type == SettingType.SELECT:
            self.create_select_control(control_frame, setting)
        elif setting.type == SettingType.FILE:
            self.create_file_control(control_frame, setting)
        elif setting.type == SettingType.FOLDER:
            self.create_folder_control(control_frame, setting)
            
    def create_boolean_control(self, parent, setting: SettingItem):
        """Cria controle para valores booleanos"""
        var = tk.BooleanVar(value=setting.value)
        var.trace('w', lambda *args, s=setting: self.on_setting_changed(s.key, var.get()))
        
        checkbox = tk.Checkbutton(
            parent,
            text="Habilitado" if setting.value else "Desabilitado",
            variable=var,
            font=self.fonts['normal'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_medium'],
            activeforeground=self.colors['text_primary'],
            command=lambda s=setting, v=var: self.update_checkbox_label(s, v)
        )
        checkbox.pack(anchor='w')
        
        setting.control_var = var
        
    def update_checkbox_label(self, setting: SettingItem, var: tk.BooleanVar):
        """Atualiza o label do checkbox"""
        for widget in var._root.winfo_children():
            if isinstance(widget, tk.Checkbutton) and widget.cget("variable") == str(var):
                widget.config(text="Habilitado" if var.get() else "Desabilitado")
                
    def create_numeric_control(self, parent, setting: SettingItem):
        """Cria controle para valores numéricos"""
        control_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        control_frame.pack(fill=tk.X)
        
        # Spinbox ou Scale baseado no tipo
        if setting.type == SettingType.INTEGER:
            var = tk.IntVar(value=setting.value)
        else:
            var = tk.DoubleVar(value=setting.value)
            
        var.trace('w', lambda *args, s=setting: self.on_setting_changed(s.key, var.get()))
        
        # Spinbox
        spinbox = tk.Spinbox(
            control_frame,
            from_=setting.min_value or 0,
            to=setting.max_value or 100,
            increment=setting.step or 1,
            textvariable=var,
            font=self.fonts['normal'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            width=15
        )
        spinbox.pack(side=tk.LEFT)
        
        # Label com valor atual
        value_label = tk.Label(
            control_frame,
            text=str(setting.value),
            font=self.fonts['normal'],
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_blue'],
            width=10
        )
        value_label.pack(side=tk.LEFT, padx=10)
        
        setting.control_var = var
        setting.value_label = value_label
        
        # Atualizar label quando valor mudar
        var.trace('w', lambda *args, v=var, l=value_label: l.config(text=str(v.get())))
        
    def create_string_control(self, parent, setting: SettingItem):
        """Cria controle para strings"""
        var = tk.StringVar(value=setting.value)
        var.trace('w', lambda *args, s=setting: self.on_setting_changed(s.key, var.get()))
        
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=self.fonts['normal'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            width=40
        )
        entry.pack(anchor='w')
        
        setting.control_var = var
        
    def create_select_control(self, parent, setting: SettingItem):
        """Cria controle para seleção"""
        var = tk.StringVar(value=setting.value)
        var.trace('w', lambda *args, s=setting: self.on_setting_changed(s.key, var.get()))
        
        # Combobox
        combobox = ttk.Combobox(
            parent,
            textvariable=var,
            values=[opt.label for opt in setting.options],
            state="readonly",
            width=40
        )
        
        # Configurar estilo
        style = ttk.Style()
        style.configure(
            "TCombobox",
            fieldbackground=self.colors['bg_light'],
            background=self.colors['bg_light'],
            foreground=self.colors['text_primary']
        )
        
        combobox.pack(anchor='w')
        
        # Mapear labels para valores
        label_to_value = {opt.label: opt.value for opt in setting.options}
        value_to_label = {opt.value: opt.label for opt in setting.options}
        
        # Configurar bind para converter label para valor
        def on_select(event):
            label = var.get()
            if label in label_to_value:
                setting.value = label_to_value[label]
                
        combobox.bind("<<ComboboxSelected>>", on_select)
        
        # Configurar valor inicial
        if setting.value in value_to_label:
            var.set(value_to_label[setting.value])
            
        setting.control_var = var
        setting.combobox = combobox
        
    def create_file_control(self, parent, setting: SettingItem):
        """Cria controle para seleção de arquivo"""
        control_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        control_frame.pack(fill=tk.X)
        
        var = tk.StringVar(value=setting.value)
        
        # Entry para caminho
        entry = tk.Entry(
            control_frame,
            textvariable=var,
            font=self.fonts['normal'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            width=35
        )
        entry.pack(side=tk.LEFT)
        
        # Botão de busca
        btn = tk.Button(
            control_frame,
            text="📁 Buscar",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['accent_blue'],
            activeforeground=self.colors['text_primary'],
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=lambda v=var: self.browse_file(v)
        )
        btn.pack(side=tk.LEFT, padx=10)
        
        setting.control_var = var
        
    def create_folder_control(self, parent, setting: SettingItem):
        """Cria controle para seleção de pasta"""
        control_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        control_frame.pack(fill=tk.X)
        
        var = tk.StringVar(value=setting.value)
        
        # Entry para caminho
        entry = tk.Entry(
            control_frame,
            textvariable=var,
            font=self.fonts['normal'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            width=35
        )
        entry.pack(side=tk.LEFT)
        
        # Botão de busca
        btn = tk.Button(
            control_frame,
            text="📂 Pasta",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['accent_blue'],
            activeforeground=self.colors['text_primary'],
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=lambda v=var: self.browse_folder(v)
        )
        btn.pack(side=tk.LEFT, padx=10)
        
        setting.control_var = var
        
    def browse_file(self, var: tk.StringVar):
        """Abre diálogo para selecionar arquivo"""
        filename = filedialog.askopenfilename(
            title="Selecionar arquivo",
            filetypes=[("Todos os arquivos", "*.*")]
        )
        if filename:
            var.set(filename)
            self.on_setting_changed(None, None)  # Trigger change
            
    def browse_folder(self, var: tk.StringVar):
        """Abre diálogo para selecionar pasta"""
        folder = filedialog.askdirectory(title="Selecionar pasta")
        if folder:
            var.set(folder)
            self.on_setting_changed(None, None)  # Trigger change
            
    def on_setting_changed(self, key: str, value: Any):
        """Chamado quando uma configuração é alterada"""
        if key and key in self.settings:
            self.settings[key].value = value
            
        # Verificar se há mudanças não salvas
        self.check_unsaved_changes()
        
    def check_unsaved_changes(self):
        """Verifica se há mudanças não salvas"""
        unsaved = False
        for key, setting in self.settings.items():
            if key in self.original_values and setting.value != self.original_values[key]:
                unsaved = True
                break
                
        if unsaved:
            self.update_status("Alterações não salvas", "warning")
        else:
            self.update_status("Todas as alterações foram salvas", "success")
            
    def switch_category(self, category: str):
        """Alterna para uma categoria diferente"""
        self.show_category(category)
        
    def reset_to_defaults(self):
        """Restaura todas as configurações para os valores padrão"""
        response = messagebox.askyesno(
            "Restaurar Padrões",
            "Tem certeza que deseja restaurar todas as configurações para os valores padrão?"
        )
        
        if response:
            for setting in self.settings.values():
                setting.value = setting.default
                
                # Atualizar controles
                if hasattr(setting, 'control_var'):
                    if isinstance(setting.control_var, tk.BooleanVar):
                        setting.control_var.set(setting.default)
                    elif isinstance(setting.control_var, (tk.IntVar, tk.DoubleVar)):
                        setting.control_var.set(setting.default)
                    elif isinstance(setting.control_var, tk.StringVar):
                        setting.control_var.set(setting.default)
                        
            self.update_status("Configurações restauradas para padrões", "success")
            self.check_unsaved_changes()
            
    def save_settings(self):
        """Salva as configurações atuais"""
        try:
            # Em implementação real, salvaria em arquivo de configuração
            config = configparser.ConfigParser()
            
            # Agrupar por categoria
            for category in set(s.category for s in self.settings.values()):
                config[category] = {}
                
            # Adicionar valores
            for key, setting in self.settings.items():
                config[setting.category][key] = str(setting.value)
                
            # Salvar em arquivo (exemplo)
            config_path = os.path.join(os.path.expanduser("~"), ".r2_assistant", "config.ini")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                config.write(f)
                
            # Atualizar valores originais
            self.original_values = {key: setting.value for key, setting in self.settings.items()}
            
            logger.info("Configurações salvas com sucesso")
            self.update_status("Configurações salvas com sucesso", "success")
            
            # Notificar outros componentes
            self.notify_config_change()
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            self.update_status(f"Erro ao salvar: {e}", "error")
            
    def export_settings(self):
        """Exporta configurações para arquivo"""
        filename = filedialog.asksaveasfilename(
            title="Exportar Configurações",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                data = {
                    "export_date": datetime.now().isoformat(),
                    "settings": {key: asdict(setting) for key, setting in self.settings.items()}
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                    
                logger.info(f"Configurações exportadas para {filename}")
                self.update_status(f"Configurações exportadas com sucesso", "success")
                
            except Exception as e:
                logger.error(f"Erro ao exportar configurações: {e}")
                self.update_status(f"Erro ao exportar: {e}", "error")
                
    def import_settings(self):
        """Importa configurações de arquivo"""
        filename = filedialog.askopenfilename(
            title="Importar Configurações",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    
                # Aplicar configurações importadas
                imported_settings = data.get("settings", {})
                
                for key, setting_data in imported_settings.items():
                    if key in self.settings:
                        self.settings[key].value = setting_data.get("value", self.settings[key].default)
                        
                        # Atualizar controle se existir
                        if hasattr(self.settings[key], 'control_var'):
                            control_var = self.settings[key].control_var
                            if isinstance(control_var, tk.BooleanVar):
                                control_var.set(self.settings[key].value)
                            elif isinstance(control_var, (tk.IntVar, tk.DoubleVar)):
                                control_var.set(self.settings[key].value)
                            elif isinstance(control_var, tk.StringVar):
                                control_var.set(self.settings[key].value)
                                
                logger.info(f"Configurações importadas de {filename}")
                self.update_status("Configurações importadas com sucesso", "success")
                self.check_unsaved_changes()
                
            except Exception as e:
                logger.error(f"Erro ao importar configurações: {e}")
                self.update_status(f"Erro ao importar: {e}", "error")
                
    def cancel_changes(self):
        """Cancela todas as alterações não salvas"""
        response = messagebox.askyesno(
            "Cancelar Alterações",
            "Tem certeza que deseja descartar todas as alterações não salvas?"
        )
        
        if response:
            # Restaurar valores originais
            for key, setting in self.settings.items():
                if key in self.original_values:
                    setting.value = self.original_values[key]
                    
                    # Atualizar controles
                    if hasattr(setting, 'control_var'):
                        if isinstance(setting.control_var, tk.BooleanVar):
                            setting.control_var.set(setting.value)
                        elif isinstance(setting.control_var, (tk.IntVar, tk.DoubleVar)):
                            setting.control_var.set(setting.value)
                        elif isinstance(setting.control_var, tk.StringVar):
                            setting.control_var.set(setting.value)
                            
            self.update_status("Alterações descartadas", "success")
            
    def apply_changes(self):
        """Aplica as alterações atuais"""
        self.save_settings()
        
    def save_and_close(self):
        """Salva as alterações e fecha a janela"""
        self.save_settings()
        self.parent.destroy()  # Em implementação real, fecharia a janela
        
    def update_status(self, message: str, status_type: str = "normal"):
        """Atualiza a mensagem de status"""
        colors = {
            "normal": self.colors['text_secondary'],
            "success": self.colors['success'],
            "warning": self.colors['warning'],
            "error": self.colors['error']
        }
        
        self.status_label.config(
            text=message,
            fg=colors.get(status_type, self.colors['text_secondary'])
        )
        
    def notify_config_change(self):
        """Notifica outros componentes sobre mudanças de configuração"""
        # Em implementação real, usaria um sistema de eventos
        logger.info("Notificando componentes sobre mudanças de configuração")
        
    def get_current_config(self) -> Dict[str, Any]:
        """Retorna a configuração atual como dicionário"""
        return {key: setting.value for key, setting in self.settings.items()}