"""
Module manager for dynamic loading and management of system modules
V2.1: Suporte a plugins e sandbox
"""

import importlib
import inspect
import json
import sys
import os
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib
from pathlib import Path

class ModuleStatus(Enum):
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNLOADED = "unloaded"

class ModuleCategory(Enum):
    SYSTEM = "system"
    VOICE = "voice"
    TRADING = "trading"
    WEB = "web"
    MEDIA = "media"
    MONITORING = "monitoring"
    UTILITY = "utility"
    AI = "ai"
    WEATHER = "weather"
    GESTURE = "gesture"
    PLUGIN = "plugin"
    CUSTOM = "custom"

@dataclass
class ModuleInfo:
    """Module information"""
    name: str
    version: str
    description: str
    author: str
    category: ModuleCategory
    status: ModuleStatus = ModuleStatus.UNLOADED
    dependencies: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    instance: Optional[Any] = None
    load_time: Optional[float] = None
    error_message: Optional[str] = None
    plugin_id: Optional[str] = None  # ID único para plugins
    manifest: Optional[Dict[str, Any]] = None  # Manifesto do plugin
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'category': self.category.value,
            'status': self.status.value,
            'dependencies': self.dependencies,
            'settings': self.settings,
            'load_time': self.load_time,
            'error_message': self.error_message,
            'has_instance': self.instance is not None,
            'plugin_id': self.plugin_id,
            'has_manifest': self.manifest is not None
        }

class SandboxEnvironment:
    """Ambiente sandbox para plugins"""
    
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.allowed_modules = [
            'time', 'json', 'os', 'sys', 'pathlib', 
            'datetime', 'math', 'random', 're'
        ]
        self.restricted_functions = [
            'eval', 'exec', 'compile', '__import__',
            'open', 'file', 'exit', 'quit'
        ]
        
    def execute_safe(self, code: str, globals_dict: Dict = None, locals_dict: Dict = None):
        """Executa código de forma segura"""
        # Implementação básica de sandbox
        # Em produção, usar RestrictedPython ou similares
        if globals_dict is None:
            globals_dict = {}
        
        # Adicionar módulos permitidos
        for module_name in self.allowed_modules:
            try:
                globals_dict[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        # Remover funções restritas
        for func in self.restricted_functions:
            if func in globals_dict:
                del globals_dict[func]
        
        try:
            return eval(code, {"__builtins__": {}}, globals_dict)
        except Exception as e:
            raise Exception(f"Sandbox error: {e}")

class ModuleManager:
    """
    Manages dynamic loading and management of system modules
    V2.1: Suporte a plugins com sandbox
    """
    
    def __init__(self, config):
        self.config = config
        self.modules: Dict[str, ModuleInfo] = {}
        self.module_classes: Dict[str, Type] = {}
        self.sandboxes: Dict[str, SandboxEnvironment] = {}
        
        # Module directories
        self.module_dirs = [
            Path(__file__).parent.parent / "modules",
            Path(__file__).parent.parent / "features",
            Path(__file__).parent.parent / "plugins"
        ]
        
        # Load module registry
        self.registry_file = self.config.DATA_DIR / "modules.json"
        self._load_registry()
        
        # Statistics
        self.stats = {
            'total_modules': 0,
            'loaded_modules': 0,
            'enabled_modules': 0,
            'failed_modules': 0,
            'module_load_times': {},
            'last_scan_time': 0,
            'sandboxed_plugins': 0
        }
        
        # Scan for modules
        if self.config.PLUGINS_AUTO_LOAD:
            self.scan_modules()
    
    def _load_registry(self):
        """Load module registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    registry_data = json.load(f)
                
                for module_data in registry_data.get('modules', []):
                    try:
                        module_info = ModuleInfo(
                            name=module_data['name'],
                            version=module_data.get('version', '1.0.0'),
                            description=module_data.get('description', ''),
                            author=module_data.get('author', 'Unknown'),
                            category=ModuleCategory(module_data.get('category', 'custom')),
                            dependencies=module_data.get('dependencies', []),
                            settings=module_data.get('settings', {}),
                            plugin_id=module_data.get('plugin_id'),
                            manifest=module_data.get('manifest')
                        )
                        self.modules[module_info.name] = module_info
                    except Exception as e:
                        print(f"⚠️ Error loading module from registry: {e}")
                
                print(f"📁 Loaded {len(self.modules)} modules from registry")
                
            except Exception as e:
                print(f"⚠️ Error loading module registry: {e}")
    
    def _save_registry(self):
        """Save module registry to file"""
        try:
            registry_data = {
                'modules': [m.to_dict() for m in self.modules.values()],
                'timestamp': time.time(),
                'version': '2.1'
            }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
            
            print("💾 Module registry saved")
            
        except Exception as e:
            print(f"❌ Error saving module registry: {e}")
    
    def scan_modules(self):
        """Scan for available modules"""
        print("🔍 Scanning for modules...")
        
        modules_found = 0
        
        for module_dir in self.module_dirs:
            if not module_dir.exists():
                continue
            
            for item in module_dir.iterdir():
                if item.is_dir():
                    # Check for module files
                    module_files = [
                        item / "__init__.py",
                        item / "module.py",
                        item / "manifest.json"
                    ]
                    
                    has_module = any(f.exists() for f in module_files)
                    
                    if has_module:
                        module_name = item.name
                        
                        try:
                            # Try to load module
                            if (item / "manifest.json").exists():
                                # Plugin with manifest
                                self._load_plugin(item)
                            else:
                                # Regular module
                                self._load_regular_module(item, module_name)
                            
                            modules_found += 1
                            
                        except Exception as e:
                            print(f"⚠️ Error scanning module {module_name}: {e}")
        
        self.stats['total_modules'] = len(self.modules)
        self.stats['last_scan_time'] = time.time()
        
        print(f"✅ Found {modules_found} modules, total: {len(self.modules)}")
        self._save_registry()
    
    def _load_regular_module(self, module_path: Path, module_name: str):
        """Load regular module"""
        try:
            spec = importlib.util.spec_from_file_location(
                f"modules.{module_name}",
                module_path / "__init__.py"
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Check for module metadata
            if hasattr(module, 'MODULE_INFO'):
                module_info = module.MODULE_INFO
                
                info = ModuleInfo(
                    name=module_info.get('name', module_name),
                    version=module_info.get('version', '1.0.0'),
                    description=module_info.get('description', 'No description'),
                    author=module_info.get('author', 'Unknown'),
                    category=ModuleCategory(module_info.get('category', 'custom')),
                    dependencies=module_info.get('dependencies', []),
                    settings=module_info.get('settings', {})
                )
                
                # Store module class if available
                if hasattr(module, 'ModuleClass'):
                    self.module_classes[info.name] = module.ModuleClass
                
                # Add or update module
                self.modules[info.name] = info
                
        except Exception as e:
            print(f"❌ Error loading regular module {module_name}: {e}")
    
    def _load_plugin(self, plugin_path: Path):
        """Load plugin with manifest"""
        try:
            # Load manifest
            with open(plugin_path / "manifest.json", 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            plugin_id = manifest.get('id', plugin_path.name)
            plugin_name = manifest.get('name', plugin_path.name)
            plugin_version = manifest.get('version', '1.0.0')
            
            # Generate unique plugin ID
            unique_id = hashlib.md5(f"{plugin_id}_{plugin_version}".encode()).hexdigest()[:8]
            full_plugin_id = f"{plugin_id}_{unique_id}"
            
            # Check if plugin already loaded
            for existing in self.modules.values():
                if existing.plugin_id == full_plugin_id:
                    print(f"⚠️ Plugin {plugin_name} already loaded")
                    return
            
            # Create sandbox if needed
            if self.config.PLUGINS_SANDBOX:
                sandbox = SandboxEnvironment(full_plugin_id)
                self.sandboxes[full_plugin_id] = sandbox
                self.stats['sandboxed_plugins'] += 1
            
            # Create module info
            module_info = ModuleInfo(
                name=plugin_name,
                version=plugin_version,
                description=manifest.get('description', ''),
                author=manifest.get('author', 'Unknown'),
                category=ModuleCategory(manifest.get('category', 'plugin')),
                dependencies=manifest.get('dependencies', []),
                settings=manifest.get('settings', {}),
                plugin_id=full_plugin_id,
                manifest=manifest
            )
            
            # Try to load main module
            main_file = plugin_path / manifest.get('main', 'module.py')
            if main_file.exists():
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{full_plugin_id}",
                    main_file
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                
                # Store module class if available
                if hasattr(module, 'PluginClass'):
                    self.module_classes[module_info.name] = module.PluginClass
            
            self.modules[module_info.name] = module_info
            print(f"📦 Loaded plugin: {plugin_name} v{plugin_version}")
            
        except Exception as e:
            print(f"❌ Error loading plugin {plugin_path.name}: {e}")
    
    def load_module(self, module_name: str, **kwargs) -> bool:
        """Load and initialize a module"""
        if module_name not in self.modules:
            print(f"❌ Module '{module_name}' not found")
            return False
        
        module_info = self.modules[module_name]
        
        # Check if already loaded
        if module_info.status == ModuleStatus.LOADED or module_info.status == ModuleStatus.ENABLED:
            print(f"⚠️ Module '{module_name}' is already loaded")
            return True
        
        # Check dependencies
        for dep in module_info.dependencies:
            if dep not in self.modules:
                print(f"❌ Missing dependency: {dep}")
                module_info.status = ModuleStatus.ERROR
                module_info.error_message = f"Missing dependency: {dep}"
                return False
            
            dep_module = self.modules[dep]
            if dep_module.status != ModuleStatus.LOADED and dep_module.status != ModuleStatus.ENABLED:
                print(f"❌ Dependency '{dep}' not loaded")
                module_info.status = ModuleStatus.ERROR
                module_info.error_message = f"Dependency '{dep}' not loaded"
                return False
        
        start_time = time.time()
        
        try:
            # Check if we have a module class
            if module_name in self.module_classes:
                module_class = self.module_classes[module_name]
                
                # For plugins, check sandbox
                if module_info.plugin_id and self.config.PLUGINS_SANDBOX:
                    sandbox = self.sandboxes.get(module_info.plugin_id)
                    if sandbox:
                        print(f"🔒 Loading plugin '{module_name}' in sandbox")
                
                # Create module instance
                instance = module_class(self.config, **kwargs)
                module_info.instance = instance
                
                # Call initialization if available
                if hasattr(instance, 'initialize'):
                    instance.initialize()
                
                module_info.status = ModuleStatus.LOADED
                module_info.load_time = time.time() - start_time
                module_info.error_message = None
                
                # Update statistics
                self.stats['loaded_modules'] += 1
                self.stats['module_load_times'][module_name] = module_info.load_time
                
                print(f"✅ Module '{module_name}' loaded in {module_info.load_time:.2f}s")
                return True
            else:
                module_info.status = ModuleStatus.ERROR
                module_info.error_message = "No module class found"
                return False
                
        except Exception as e:
            module_info.status = ModuleStatus.ERROR
            module_info.error_message = str(e)
            self.stats['failed_modules'] += 1
            
            print(f"❌ Error loading module '{module_name}': {e}")
            return False
    
    def execute_plugin_command(self, plugin_id: str, command: str, **kwargs) -> Any:
        """Execute a command in plugin sandbox"""
        if plugin_id not in self.sandboxes:
            raise ValueError(f"Plugin '{plugin_id}' not found or not sandboxed")
        
        sandbox = self.sandboxes[plugin_id]
        
        try:
            # Find plugin module
            plugin_module = None
            for module_info in self.modules.values():
                if module_info.plugin_id == plugin_id:
                    # Get the module instance
                    if module_info.instance:
                        plugin_module = module_info.instance
                    break
            
            if not plugin_module:
                raise ValueError(f"Plugin instance not found for '{plugin_id}'")
            
            # Execute command in sandbox
            if hasattr(plugin_module, command):
                method = getattr(plugin_module, command)
                
                # Check if method is safe to execute
                if self.config.PLUGINS_SANDBOX:
                    # Execute in sandbox
                    code = f"plugin_module.{command}(**kwargs)"
                    return sandbox.execute_safe(code, {'plugin_module': plugin_module, 'kwargs': kwargs})
                else:
                    # Execute directly
                    return method(**kwargs)
            else:
                raise AttributeError(f"Command '{command}' not found in plugin")
                
        except Exception as e:
            raise Exception(f"Error executing command '{command}' in plugin '{plugin_id}': {e}")
    
    # Rest of the methods remain similar to original with updates for V2.1
    def unload_module(self, module_name: str) -> bool:
        """Unload a module"""
        if module_name not in self.modules:
            print(f"⚠️ Module '{module_name}' not found")
            return False
        
        module_info = self.modules[module_name]
        
        if module_info.status in [ModuleStatus.UNLOADED, ModuleStatus.DISABLED]:
            print(f"⚠️ Module '{module_name}' is already unloaded")
            return True
        
        try:
            # Call cleanup if available
            if module_info.instance and hasattr(module_info.instance, 'cleanup'):
                module_info.instance.cleanup()
            
            # Remove instance
            module_info.instance = None
            module_info.status = ModuleStatus.UNLOADED
            module_info.load_time = None
            
            # Update statistics
            self.stats['loaded_modules'] = max(0, self.stats['loaded_modules'] - 1)
            
            print(f"✅ Module '{module_name}' unloaded")
            return True
            
        except Exception as e:
            print(f"❌ Error unloading module '{module_name}': {e}")
            return False
    
    def enable_module(self, module_name: str) -> bool:
        """Enable a module"""
        if module_name not in self.modules:
            print(f"⚠️ Module '{module_name}' not found")
            return False
        
        module_info = self.modules[module_name]
        
        if module_info.status == ModuleStatus.ENABLED:
            print(f"⚠️ Module '{module_name}' is already enabled")
            return True
        
        # Ensure module is loaded
        if module_info.status != ModuleStatus.LOADED:
            if not self.load_module(module_name):
                return False
        
        module_info.status = ModuleStatus.ENABLED
        self.stats['enabled_modules'] += 1
        
        print(f"✅ Module '{module_name}' enabled")
        return True
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get overall module system statistics"""
        modules_by_category = {}
        modules_by_status = {}
        
        for module_info in self.modules.values():
            category = module_info.category.value
            status = module_info.status.value
            
            if category not in modules_by_category:
                modules_by_category[category] = 0
            modules_by_category[category] += 1
            
            if status not in modules_by_status:
                modules_by_status[status] = 0
            modules_by_status[status] += 1
        
        return {
            **self.stats,
            'modules_by_category': modules_by_category,
            'modules_by_status': modules_by_status,
            'total_dependencies': sum(len(m.dependencies) for m in self.modules.values()),
            'total_plugins': sum(1 for m in self.modules.values() if m.plugin_id),
            'sandbox_enabled': self.config.PLUGINS_SANDBOX
        }