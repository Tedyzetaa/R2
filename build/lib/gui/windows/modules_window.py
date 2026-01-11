"""
Janela de Módulos - Interface para gerenciamento de módulos do sistema
Design inspirado em painéis de controle de naves espaciais
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ModuleStatus(Enum):
    """Status dos módulos do sistema"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UPDATING = "updating"
    ERROR = "error"
    STANDBY = "standby"

@dataclass
class ModuleInfo:
    """Estrutura de dados para informações do módulo"""
    name: str
    description: str
    version: str
    status: ModuleStatus
    category: str
    dependencies: List[str]
    memory_usage: float  # MB
    cpu_usage: float    # %
    last_updated: str
    author: str

class ModulesWindow:
    """Janela de gerenciamento de módulos com interface Sci-Fi/HUD"""
    
    def __init__(self, parent, config: Dict[str, Any]):
        """
        Inicializa a janela de módulos
        
        Args:
            parent: Widget pai
            config: Configuração da aplicação
        """
        self.parent = parent
        self.config = config
        self.modules: Dict[str, ModuleInfo] = {}
        self.current_filter = "all"
        
        # Cores e temas Sci-Fi
        self.colors = {
            'bg_dark': '#0a0a12',
            'bg_medium': '#121225',
            'bg_light': '#1a1a35',
            'accent_blue': '#00ccff',
            'accent_purple': '#9d00ff',
            'accent_green': '#00ffaa',
            'accent_red': '#ff3366',
            'text_primary': '#ffffff',
            'text_secondary': '#a0a0c0',
            'border': '#2a2a4a'
        }
        
        # Configuração da fonte HUD
        self.fonts = {
            'title': ('Segoe UI', 14, 'bold'),
            'heading': ('Segoe UI', 12, 'bold'),
            'normal': ('Segoe UI', 10),
            'small': ('Segoe UI', 9),
            'mono': ('Consolas', 9)
        }
        
        self.setup_ui()
        self.load_modules()
        
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
        
        # Título da janela
        self.create_title_section()
        
        # Barra de ferramentas
        self.create_toolbar()
        
        # Área de conteúdo
        self.create_content_area()
        
        # Barra de status
        self.create_status_bar()
        
    def create_title_section(self):
        """Cria a seção de título com estilo Sci-Fi"""
        title_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark']
        )
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Ícone e título
        icon_label = tk.Label(
            title_frame,
            text="⚙️",
            font=('Segoe UI', 24),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_blue']
        )
        icon_label.pack(side=tk.LEFT)
        
        title_label = tk.Label(
            title_frame,
            text="SISTEMA DE MÓDULOS - R2 ASSISTANT",
            font=self.fonts['title'],
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary']
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Linha decorativa
        separator = tk.Frame(
            title_frame,
            height=2,
            bg=self.colors['accent_blue']
        )
        separator.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
    def create_toolbar(self):
        """Cria a barra de ferramentas com filtros e ações"""
        toolbar_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_medium'],
            relief=tk.RAISED,
            borderwidth=1
        )
        toolbar_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Filtros
        filters_frame = tk.Frame(toolbar_frame, bg=self.colors['bg_medium'])
        filters_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(
            filters_frame,
            text="FILTRAR:",
            font=self.fonts['small'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT)
        
        filter_options = [
            ("TODOS", "all"),
            ("ATIVOS", "active"),
            ("INATIVOS", "inactive"),
            ("IA", "ai"),
            ("DADOS", "data"),
            ("TRADING", "trading"),
            ("SEGURANÇA", "security")
        ]
        
        for text, value in filter_options:
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
                padx=10,
                pady=3,
                command=lambda v=value: self.filter_modules(v)
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Botões de ação
        actions_frame = tk.Frame(toolbar_frame, bg=self.colors['bg_medium'])
        actions_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        action_buttons = [
            ("🔄 ATUALIZAR", self.update_modules),
            ("➕ INSTALAR", self.install_module),
            ("⚙️ CONFIGURAR", self.configure_system),
            ("📊 RELATÓRIO", self.generate_report)
        ]
        
        for text, command in action_buttons:
            btn = tk.Button(
                actions_frame,
                text=text,
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_purple'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                borderwidth=1,
                padx=12,
                pady=3,
                command=command
            )
            btn.pack(side=tk.LEFT, padx=2)
            
    def create_content_area(self):
        """Cria a área de conteúdo para exibição dos módulos"""
        # Frame de conteúdo com duas colunas
        content_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_dark']
        )
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Painel esquerdo - Lista de módulos
        self.create_modules_panel(content_frame)
        
        # Painel direito - Detalhes do módulo
        self.create_details_panel(content_frame)
        
    def create_modules_panel(self, parent):
        """Cria o painel de lista de módulos"""
        modules_frame = tk.Frame(
            parent,
            bg=self.colors['bg_medium'],
            relief=tk.SUNKEN,
            borderwidth=2
        )
        modules_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Cabeçalho do painel
        header_frame = tk.Frame(
            modules_frame,
            bg=self.colors['bg_light'],
            height=30
        )
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        headers = ["STATUS", "MÓDULO", "VERSÃO", "CATEGORIA", "CPU", "MEM"]
        for i, header in enumerate(headers):
            tk.Label(
                header_frame,
                text=header,
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['accent_blue'],
                padx=10
            ).grid(row=0, column=i, sticky='w')
        
        # Treeview para lista de módulos
        self.modules_tree = ttk.Treeview(
            modules_frame,
            columns=('status', 'module', 'version', 'category', 'cpu', 'mem'),
            show='tree headings',
            height=15
        )
        
        # Configurar estilo
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=self.colors['bg_dark'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['bg_dark'],
            borderwidth=0
        )
        
        # Configurar colunas
        self.modules_tree.heading('#0', text='')
        self.modules_tree.column('#0', width=0, stretch=False)
        
        for col in self.modules_tree['columns']:
            self.modules_tree.heading(col, text=col.upper())
            self.modules_tree.column(col, width=100)
        
        self.modules_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            modules_frame,
            orient=tk.VERTICAL,
            command=self.modules_tree.yview
        )
        self.modules_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind de seleção
        self.modules_tree.bind('<<TreeviewSelect>>', self.on_module_select)
        
    def create_details_panel(self, parent):
        """Cria o painel de detalhes do módulo"""
        details_frame = tk.Frame(
            parent,
            bg=self.colors['bg_medium'],
            width=400,
            relief=tk.SUNKEN,
            borderwidth=2
        )
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        details_frame.pack_propagate(False)
        
        # Cabeçalho
        tk.Label(
            details_frame,
            text="DETALHES DO MÓDULO",
            font=self.fonts['heading'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary'],
            pady=10
        ).pack(fill=tk.X)
        
        # Frame de conteúdo dos detalhes
        self.details_content = tk.Frame(
            details_frame,
            bg=self.colors['bg_medium']
        )
        self.details_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Inicializar com mensagem padrão
        tk.Label(
            self.details_content,
            text="Selecione um módulo para ver os detalhes",
            font=self.fonts['normal'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary'],
            wraplength=350
        ).pack(expand=True)
        
    def create_status_bar(self):
        """Cria a barra de status"""
        status_frame = tk.Frame(
            self.main_frame,
            bg=self.colors['bg_light'],
            height=25
        )
        status_frame.pack(fill=tk.X, pady=(15, 0))
        status_frame.pack_propagate(False)
        
        # Status do sistema
        self.system_status = tk.Label(
            status_frame,
            text="SISTEMA: OPERACIONAL",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['accent_green']
        )
        self.system_status.pack(side=tk.LEFT, padx=10)
        
        # Contador de módulos
        self.module_count = tk.Label(
            status_frame,
            text="MÓDULOS: 0/0 ATIVOS",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary']
        )
        self.module_count.pack(side=tk.LEFT, padx=20)
        
        # Última atualização
        self.last_update = tk.Label(
            status_frame,
            text="ÚLTIMA ATUALIZAÇÃO: --:--:--",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary']
        )
        self.last_update.pack(side=tk.RIGHT, padx=10)
        
    def load_modules(self):
        """Carrega a lista de módulos do sistema"""
        try:
            # Exemplo de dados - em produção, viria de um banco de dados ou API
            sample_modules = [
                ModuleInfo(
                    name="Núcleo de IA",
                    description="Núcleo principal de inteligência artificial",
                    version="2.1.0",
                    status=ModuleStatus.ACTIVE,
                    category="ai",
                    dependencies=["python>=3.8", "torch", "transformers"],
                    memory_usage=512.5,
                    cpu_usage=23.4,
                    last_updated="2024-01-15",
                    author="R2 Team"
                ),
                ModuleInfo(
                    name="Análise Quantitativa",
                    description="Sistema de análise de dados financeiros",
                    version="1.8.2",
                    status=ModuleStatus.ACTIVE,
                    category="data",
                    dependencies=["pandas", "numpy", "scipy"],
                    memory_usage=256.3,
                    cpu_usage=12.7,
                    last_updated="2024-01-14",
                    author="Quant Team"
                ),
                ModuleInfo(
                    name="Motor de Trading",
                    description="Execução automática de trades",
                    version="1.5.3",
                    status=ModuleStatus.STANDBY,
                    category="trading",
                    dependencies=["ccxt", "websockets", "cryptography"],
                    memory_usage=128.9,
                    cpu_usage=5.2,
                    last_updated="2024-01-13",
                    author="Trading Team"
                ),
                ModuleInfo(
                    name="Monitor de Segurança",
                    description="Monitoramento de segurança em tempo real",
                    version="1.2.1",
                    status=ModuleStatus.ACTIVE,
                    category="security",
                    dependencies=["psutil", "cryptography", "requests"],
                    memory_usage=89.6,
                    cpu_usage=3.1,
                    last_updated="2024-01-15",
                    author="Security Team"
                )
            ]
            
            self.modules = {module.name: module for module in sample_modules}
            self.update_modules_list()
            self.update_status_bar()
            
        except Exception as e:
            logger.error(f"Erro ao carregar módulos: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar módulos: {e}")
            
    def update_modules_list(self):
        """Atualiza a lista de módulos na treeview"""
        # Limpar treeview
        for item in self.modules_tree.get_children():
            self.modules_tree.delete(item)
        
        # Adicionar módulos filtrados
        for name, module in self.modules.items():
            if self.current_filter == "all" or self.current_filter == module.category:
                # Determinar ícone de status
                status_icon = self.get_status_icon(module.status)
                
                # Adicionar à treeview
                self.modules_tree.insert(
                    '',
                    tk.END,
                    values=(
                        status_icon,
                        name,
                        module.version,
                        module.category.upper(),
                        f"{module.cpu_usage:.1f}%",
                        f"{module.memory_usage:.1f}MB"
                    ),
                    tags=(name,)
                )
                
    def get_status_icon(self, status: ModuleStatus) -> str:
        """Retorna o ícone correspondente ao status"""
        icons = {
            ModuleStatus.ACTIVE: "🟢",
            ModuleStatus.INACTIVE: "⚫",
            ModuleStatus.UPDATING: "🟡",
            ModuleStatus.ERROR: "🔴",
            ModuleStatus.STANDBY: "🟣"
        }
        return icons.get(status, "⚫")
    
    def on_module_select(self, event):
        """Evento de seleção de módulo na treeview"""
        selection = self.modules_tree.selection()
        if not selection:
            return
            
        # Obter nome do módulo selecionado
        item = selection[0]
        module_name = self.modules_tree.item(item, "tags")[0]
        
        if module_name in self.modules:
            self.show_module_details(self.modules[module_name])
            
    def show_module_details(self, module: ModuleInfo):
        """Exibe os detalhes do módulo selecionado"""
        # Limpar frame de detalhes
        for widget in self.details_content.winfo_children():
            widget.destroy()
        
        # Criar layout de detalhes
        details_grid = tk.Frame(self.details_content, bg=self.colors['bg_medium'])
        details_grid.pack(fill=tk.BOTH, expand=True)
        
        # Informações básicas
        info_labels = [
            ("Nome:", module.name),
            ("Descrição:", module.description),
            ("Versão:", module.version),
            ("Status:", module.status.value.upper()),
            ("Categoria:", module.category.upper()),
            ("Autor:", module.author),
            ("Última Atualização:", module.last_updated)
        ]
        
        for i, (label, value) in enumerate(info_labels):
            # Label
            tk.Label(
                details_grid,
                text=label,
                font=self.fonts['small'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_secondary'],
                anchor='w'
            ).grid(row=i, column=0, sticky='w', pady=2)
            
            # Valor
            tk.Label(
                details_grid,
                text=value,
                font=self.fonts['small'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary'],
                anchor='w'
            ).grid(row=i, column=1, sticky='w', pady=2, padx=(10, 0))
        
        # Métricas de desempenho
        metrics_frame = tk.Frame(details_grid, bg=self.colors['bg_light'])
        metrics_frame.grid(row=len(info_labels), column=0, columnspan=2, 
                          pady=(15, 0), sticky='ew')
        
        tk.Label(
            metrics_frame,
            text="DESEMPENHO",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['accent_blue']
        ).pack(anchor='w', padx=5, pady=5)
        
        # Barras de progresso
        progress_frame = tk.Frame(metrics_frame, bg=self.colors['bg_light'])
        progress_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # CPU
        tk.Label(
            progress_frame,
            text=f"CPU: {module.cpu_usage:.1f}%",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary'],
            width=15
        ).pack(side=tk.LEFT)
        
        cpu_bar = tk.Canvas(
            progress_frame,
            width=200,
            height=15,
            bg=self.colors['bg_dark'],
            highlightthickness=0
        )
        cpu_bar.pack(side=tk.LEFT, padx=5)
        self.draw_progress_bar(cpu_bar, module.cpu_usage / 100)
        
        # Memória
        tk.Label(
            progress_frame,
            text=f"MEM: {module.memory_usage:.1f}MB",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary'],
            width=15
        ).pack(side=tk.LEFT)
        
        mem_bar = tk.Canvas(
            progress_frame,
            width=200,
            height=15,
            bg=self.colors['bg_dark'],
            highlightthickness=0
        )
        mem_bar.pack(side=tk.LEFT, padx=5)
        self.draw_progress_bar(mem_bar, module.memory_usage / 1024)
        
        # Dependências
        deps_frame = tk.Frame(details_grid, bg=self.colors['bg_light'])
        deps_frame.grid(row=len(info_labels) + 1, column=0, columnspan=2,
                       pady=(10, 0), sticky='ew')
        
        tk.Label(
            deps_frame,
            text="DEPENDÊNCIAS",
            font=self.fonts['small'],
            bg=self.colors['bg_light'],
            fg=self.colors['accent_blue']
        ).pack(anchor='w', padx=5, pady=5)
        
        for dep in module.dependencies:
            tk.Label(
                deps_frame,
                text=f"• {dep}",
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                anchor='w'
            ).pack(anchor='w', padx=10)
            
        # Botões de ação para o módulo
        actions_frame = tk.Frame(details_grid, bg=self.colors['bg_medium'])
        actions_frame.grid(row=len(info_labels) + 2, column=0, columnspan=2,
                          pady=(15, 0), sticky='ew')
        
        actions = [
            ("▶️ ATIVAR", self.activate_module),
            ("⏸️ PAUSAR", self.pause_module),
            ("🔄 REINICIAR", self.restart_module),
            ("🗑️ REMOVER", self.remove_module)
        ]
        
        for text, command in actions:
            btn = tk.Button(
                actions_frame,
                text=text,
                font=self.fonts['small'],
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary'],
                activebackground=self.colors['accent_blue'],
                activeforeground=self.colors['text_primary'],
                relief=tk.FLAT,
                borderwidth=1,
                padx=10,
                pady=3,
                command=lambda cmd=command, m=module: cmd(m)
            )
            btn.pack(side=tk.LEFT, padx=5)
            
    def draw_progress_bar(self, canvas: tk.Canvas, percentage: float):
        """Desenha uma barra de progresso no canvas"""
        width = canvas.winfo_reqwidth()
        height = canvas.winfo_reqheight()
        
        # Limpar canvas
        canvas.delete("all")
        
        # Fundo
        canvas.create_rectangle(0, 0, width, height, 
                               fill=self.colors['bg_dark'], outline="")
        
        # Determinar cor baseada na porcentagem
        if percentage < 0.5:
            color = self.colors['accent_green']
        elif percentage < 0.8:
            color = self.colors['accent_blue']
        else:
            color = self.colors['accent_red']
        
        # Barra de progresso
        bar_width = int(width * percentage)
        canvas.create_rectangle(0, 0, bar_width, height, 
                               fill=color, outline="")
        
        # Efeito de gradiente (simples)
        canvas.create_rectangle(0, 0, bar_width, height//2, 
                               fill=color, outline="", stipple="gray50")
        
    def filter_modules(self, category: str):
        """Filtra módulos por categoria"""
        self.current_filter = category
        self.update_modules_list()
        
    def update_modules(self):
        """Atualiza todos os módulos"""
        logger.info("Iniciando atualização de módulos...")
        # Implementação real viria aqui
        messagebox.showinfo("Atualização", "Verificando atualizações de módulos...")
        
    def install_module(self):
        """Instala um novo módulo"""
        logger.info("Iniciando instalação de novo módulo...")
        # Implementação real viria aqui
        messagebox.showinfo("Instalação", "Abrir gerenciador de módulos...")
        
    def configure_system(self):
        """Abre configurações do sistema"""
        logger.info("Abrindo configurações do sistema...")
        # Implementação real viria aqui
        messagebox.showinfo("Configuração", "Abrindo configurações do sistema...")
        
    def generate_report(self):
        """Gera relatório do sistema"""
        logger.info("Gerando relatório de módulos...")
        # Implementação real viria aqui
        messagebox.showinfo("Relatório", "Gerando relatório do sistema...")
        
    def activate_module(self, module: ModuleInfo):
        """Ativa um módulo"""
        logger.info(f"Ativando módulo: {module.name}")
        module.status = ModuleStatus.ACTIVE
        self.update_modules_list()
        
    def pause_module(self, module: ModuleInfo):
        """Pausa um módulo"""
        logger.info(f"Pausando módulo: {module.name}")
        module.status = ModuleStatus.STANDBY
        self.update_modules_list()
        
    def restart_module(self, module: ModuleInfo):
        """Reinicia um módulo"""
        logger.info(f"Reiniciando módulo: {module.name}")
        module.status = ModuleStatus.UPDATING
        self.update_modules_list()
        # Simulação de tempo de reinicialização
        self.parent.after(2000, lambda: self.complete_restart(module))
        
    def complete_restart(self, module: ModuleInfo):
        """Completa o reinício do módulo"""
        module.status = ModuleStatus.ACTIVE
        self.update_modules_list()
        
    def remove_module(self, module: ModuleInfo):
        """Remove um módulo"""
        response = messagebox.askyesno(
            "Confirmar Remoção",
            f"Tem certeza que deseja remover o módulo '{module.name}'?"
        )
        
        if response:
            logger.info(f"Removendo módulo: {module.name}")
            if module.name in self.modules:
                del self.modules[module.name]
                self.update_modules_list()
                self.update_status_bar()
                
    def update_status_bar(self):
        """Atualiza a barra de status"""
        total = len(self.modules)
        active = sum(1 for m in self.modules.values() 
                    if m.status == ModuleStatus.ACTIVE)
        
        self.module_count.config(text=f"MÓDULOS: {active}/{total} ATIVOS")
        
    def refresh(self):
        """Atualiza a janela"""
        self.load_modules()
        
    def get_window_info(self) -> Dict[str, Any]:
        """Retorna informações sobre a janela"""
        return {
            "name": "Modules Window",
            "version": "1.0.0",
            "modules_count": len(self.modules),
            "active_modules": sum(1 for m in self.modules.values() 
                                if m.status == ModuleStatus.ACTIVE)
        }