"""
Module panel component for displaying and controlling system modules
"""

import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable

class ModulePanel(ctk.CTkFrame):
    """Panel for displaying and controlling system modules"""
    
    def __init__(self, parent, module_manager=None, theme=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.module_manager = module_manager
        self.modules: Dict[str, Dict[str, Any]] = {}
        
        # Colors
        if theme:
            self.colors = theme.colors
        else:
            self.colors = {
                'primary': '#00ffff',
                'secondary': '#0099ff',
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff0066',
                'bg_dark': '#0a0a12',
                'text': '#ffffff',
                'text_dim': '#8888aa'
            }
        
        # Module status colors
        self.status_colors = {
            'loaded': self.colors['success'],
            'enabled': self.colors['primary'],
            'disabled': self.colors['text_dim'],
            'error': self.colors['danger'],
            'unloaded': self.colors['warning']
        }
        
        # Setup UI
        self._setup_ui()
        
        # Load modules if manager is provided
        if module_manager:
            self.load_modules()
    
    def _setup_ui(self):
        """Setup module panel UI"""
        self.configure(
            fg_color=self.colors['bg_dark'],
            corner_radius=6,
            border_width=1,
            border_color=self.colors['primary']
        )
        
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="⚙️ SYSTEM MODULES",
            font=("Consolas", 10, "bold"),
            text_color=self.colors['primary']
        )
        self.title_label.pack(pady=(5, 5))
        
        # Module container
        self.module_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=200
        )
        self.module_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Statistics
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        self._update_stats()
        
    def load_modules(self):
        """Load modules from module manager"""
        if not self.module_manager:
            return
        
        # Clear existing modules
        for widget in self.module_container.winfo_children():
            widget.destroy()
        
        # Get modules from manager
        modules_list = self.module_manager.list_modules()
        self.modules = {}
        
        for module_info in modules_list:
            module_name = module_info['name']
            self.modules[module_name] = module_info
            
            # Create module widget
            self._create_module_widget(module_info)
        
        # Update statistics
        self._update_stats()
    
    def _create_module_widget(self, module_info: Dict[str, Any]):
        """Create widget for a single module"""
        module_frame = ctk.CTkFrame(
            self.module_container,
            fg_color=self.colors['bg_dark'],
            corner_radius=4,
            border_width=1,
            border_color=self.status_colors.get(
                module_info.get('status', 'unloaded').lower(),
                self.colors['text_dim']
            )
        )
        module_frame.pack(fill="x", pady=2, padx=2)
        
        # Module header
        header_frame = ctk.CTkFrame(module_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=3)
        
        # Module name and version
        name_text = f"{module_info['name']} v{module_info.get('version', '1.0')}"
        name_label = ctk.CTkLabel(
            header_frame,
            text=name_text,
            font=("Consolas", 9, "bold"),
            text_color=self.colors['text'],
            justify="left",
            width=150
        )
        name_label.pack(side="left")
        
        # Status indicator
        status = module_info.get('status', 'unloaded').lower()
        status_color = self.status_colors.get(status, self.colors['text_dim'])
        
        status_label = ctk.CTkLabel(
            header_frame,
            text=status.upper(),
            font=("Consolas", 8, "bold"),
            text_color=status_color,
            justify="right"
        )
        status_label.pack(side="right", padx=(0, 10))
        
        # Module description
        description = module_info.get('description', '')
        if description:
            desc_frame = ctk.CTkFrame(module_frame, fg_color="transparent")
            desc_frame.pack(fill="x", padx=5, pady=(0, 3))
            
            desc_label = ctk.CTkLabel(
                desc_frame,
                text=description[:60] + ("..." if len(description) > 60 else ""),
                font=("Consolas", 8),
                text_color=self.colors['text_dim'],
                justify="left",
                wraplength=250
            )
            desc_label.pack(anchor="w")
        
        # Control buttons
        if self.module_manager:
            control_frame = ctk.CTkFrame(module_frame, fg_color="transparent")
            control_frame.pack(fill="x", padx=5, pady=(0, 3))
            
            module_name = module_info['name']
            
            # Load/Unload button
            if status in ['loaded', 'enabled']:
                unload_btn = ctk.CTkButton(
                    control_frame,
                    text="UNLOAD",
                    width=60,
                    height=20,
                    font=("Consolas", 8),
                    fg_color=self.colors['warning'],
                    hover_color=self.colors['danger'],
                    text_color=self.colors['text'],
                    command=lambda m=module_name: self._unload_module(m)
                )
                unload_btn.pack(side="left", padx=(0, 5))
            else:
                load_btn = ctk.CTkButton(
                    control_frame,
                    text="LOAD",
                    width=60,
                    height=20,
                    font=("Consolas", 8),
                    fg_color=self.colors['success'],
                    hover_color=self.colors['primary'],
                    text_color=self.colors['text'],
                    command=lambda m=module_name: self._load_module(m)
                )
                load_btn.pack(side="left", padx=(0, 5))
            
            # Enable/Disable button
            if status == 'loaded':
                enable_btn = ctk.CTkButton(
                    control_frame,
                    text="ENABLE",
                    width=60,
                    height=20,
                    font=("Consolas", 8),
                    fg_color=self.colors['primary'],
                    hover_color=self.colors['secondary'],
                    text_color=self.colors['text'],
                    command=lambda m=module_name: self._enable_module(m)
                )
                enable_btn.pack(side="left")
            elif status == 'enabled':
                disable_btn = ctk.CTkButton(
                    control_frame,
                    text="DISABLE",
                    width=60,
                    height=20,
                    font=("Consolas", 8),
                    fg_color=self.colors['warning'],
                    hover_color=self.colors['danger'],
                    text_color=self.colors['text'],
                    command=lambda m=module_name: self._disable_module(m)
                )
                disable_btn.pack(side="left")
    
    def _load_module(self, module_name: str):
        """Load a module"""
        if self.module_manager:
            success = self.module_manager.load_module(module_name)
            if success:
                self.load_modules()
    
    def _unload_module(self, module_name: str):
        """Unload a module"""
        if self.module_manager:
            success = self.module_manager.unload_module(module_name)
            if success:
                self.load_modules()
    
    def _enable_module(self, module_name: str):
        """Enable a module"""
        if self.module_manager:
            success = self.module_manager.enable_module(module_name)
            if success:
                self.load_modules()
    
    def _disable_module(self, module_name: str):
        """Disable a module"""
        if self.module_manager:
            success = self.module_manager.disable_module(module_name)
            if success:
                self.load_modules()
    
    def _update_stats(self):
        """Update module statistics"""
        # Clear stats frame
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Calculate statistics
        total = len(self.modules)
        if total == 0:
            stats_text = "No modules loaded"
        else:
            loaded = sum(1 for m in self.modules.values() 
                        if m.get('status') in ['loaded', 'enabled'])
            enabled = sum(1 for m in self.modules.values() 
                         if m.get('status') == 'enabled')
            
            stats_text = f"Modules: {total} | Loaded: {loaded} | Active: {enabled}"
        
        # Create stats label
        stats_label = ctk.CTkLabel(
            self.stats_frame,
            text=stats_text,
            font=("Consolas", 9),
            text_color=self.colors['text_dim']
        )
        stats_label.pack()
    
    def add_module(self, module_info: Dict[str, Any]):
        """Add a module manually"""
        module_name = module_info['name']
        self.modules[module_name] = module_info
        self._create_module_widget(module_info)
        self._update_stats()
    
    def remove_module(self, module_name: str):
        """Remove a module"""
        if module_name in self.modules:
            del self.modules[module_name]
            self.load_modules()
    
    def get_module_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a module"""
        return self.modules.get(module_name)
    
    def refresh(self):
        """Refresh module display"""
        self.load_modules()
    
    def set_module_manager(self, module_manager):
        """Set module manager and load modules"""
        self.module_manager = module_manager
        self.load_modules()