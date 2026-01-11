"""
Module manager for dynamic loading and management of system modules
"""

import importlib
import inspect
import json
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum
import time
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
            'has_instance': self.instance is not None
        }

class ModuleManager:
    """
    Manages dynamic loading and management of system modules
    """
    
    def __init__(self, config):
        self.config = config
        self.modules: Dict[str, ModuleInfo] = {}
        self.module_classes: Dict[str, Type] = {}
        
        # Module directories
        self.module_dirs = [
            Path(__file__).parent.parent / "modules",
            Path(__file__).parent.parent / "features"
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
            'last_scan_time': 0
        }
        
        # Scan for modules
        self.scan_modules()
    
    def _load_registry(self):
        """Load module registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    registry_data = json.load(f)
                
                for module_data in registry_data.get('modules', []):
                    module_info = ModuleInfo(
                        name=module_data['name'],
                        version=module_data['version'],
                        description=module_data['description'],
                        author=module_data['author'],
                        category=ModuleCategory(module_data['category']),
                        dependencies=module_data.get('dependencies', []),
                        settings=module_data.get('settings', {})
                    )
                    self.modules[module_info.name] = module_info
                
                print(f"📁 Loaded {len(self.modules)} modules from registry")
                
            except Exception as e:
                print(f"⚠️ Error loading module registry: {e}")
    
    def _save_registry(self):
        """Save module registry to file"""
        try:
            registry_data = {
                'modules': [m.to_dict() for m in self.modules.values()],
                'timestamp': time.time()
            }
            
            with open(self.registry_file, 'w') as f:
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
                if item.is_dir() and (item / "__init__.py").exists():
                    module_name = item.name
                    
                    try:
                        # Try to import module
                        spec = importlib.util.spec_from_file_location(
                            f"{module_dir.name}.{module_name}",
                            item / "__init__.py"
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Check for module metadata
                        if hasattr(module, 'MODULE_INFO'):
                            module_info = module.MODULE_INFO
                            
                            # Create ModuleInfo
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
                            if info.name in self.modules:
                                # Update existing module
                                existing = self.modules[info.name]
                                existing.version = info.version
                                existing.description = info.description
                                existing.dependencies = info.dependencies
                                existing.settings = info.settings
                            else:
                                # Add new module
                                self.modules[info.name] = info
                            
                            modules_found += 1
                            
                    except Exception as e:
                        print(f"⚠️ Error scanning module {module_name}: {e}")
        
        self.stats['total_modules'] = len(self.modules)
        self.stats['last_scan_time'] = time.time()
        
        print(f"✅ Found {modules_found} modules, total: {len(self.modules)}")
        
        # Save updated registry
        self._save_registry()
    
    def load_module(self, module_name: str, **kwargs) -> bool:
        """
        Load and initialize a module
        
        Returns:
            True if successful, False otherwise
        """
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
    
    def disable_module(self, module_name: str) -> bool:
        """Disable a module"""
        if module_name not in self.modules:
            print(f"⚠️ Module '{module_name}' not found")
            return False
        
        module_info = self.modules[module_name]
        
        if module_info.status == ModuleStatus.DISABLED:
            print(f"⚠️ Module '{module_name}' is already disabled")
            return True
        
        module_info.status = ModuleStatus.DISABLED
        self.stats['enabled_modules'] = max(0, self.stats['enabled_modules'] - 1)
        
        print(f"🚫 Module '{module_name}' disabled")
        return True
    
    def get_module(self, module_name: str) -> Optional[ModuleInfo]:
        """Get module information"""
        return self.modules.get(module_name)
    
    def list_modules(self, category: Optional[ModuleCategory] = None,
                    status: Optional[ModuleStatus] = None) -> List[Dict[str, Any]]:
        """List modules with optional filtering"""
        modules_list = []
        
        for module_info in self.modules.values():
            if category and module_info.category != category:
                continue
            
            if status and module_info.status != status:
                continue
            
            modules_list.append(module_info.to_dict())
        
        # Sort by name
        modules_list.sort(key=lambda x: x['name'])
        
        return modules_list
    
    def execute_module_command(self, module_name: str, command: str, **kwargs) -> Any:
        """
        Execute a command on a module
        
        Returns:
            Command result
        """
        if module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' not found")
        
        module_info = self.modules[module_name]
        
        if module_info.status not in [ModuleStatus.LOADED, ModuleStatus.ENABLED]:
            raise ValueError(f"Module '{module_name}' is not loaded")
        
        if not module_info.instance:
            raise ValueError(f"Module '{module_name}' has no instance")
        
        try:
            # Check if command exists
            if hasattr(module_info.instance, command):
                method = getattr(module_info.instance, command)
                
                # Execute command
                return method(**kwargs)
            else:
                raise AttributeError(f"Command '{command}' not found in module '{module_name}'")
                
        except Exception as e:
            raise Exception(f"Error executing command '{command}' on module '{module_name}': {e}")
    
    def register_module(self, module_info: Dict[str, Any], module_class: Optional[Type] = None):
        """Register a new module programmatically"""
        info = ModuleInfo(
            name=module_info['name'],
            version=module_info.get('version', '1.0.0'),
            description=module_info.get('description', ''),
            author=module_info.get('author', 'Unknown'),
            category=ModuleCategory(module_info.get('category', 'custom')),
            dependencies=module_info.get('dependencies', []),
            settings=module_info.get('settings', {})
        )
        
        self.modules[info.name] = info
        
        if module_class:
            self.module_classes[info.name] = module_class
        
        print(f"📝 Registered module: {info.name}")
        
        # Save updated registry
        self._save_registry()
    
    def unregister_module(self, module_name: str):
        """Unregister a module"""
        if module_name in self.modules:
            # Unload if loaded
            if self.modules[module_name].status in [ModuleStatus.LOADED, ModuleStatus.ENABLED]:
                self.unload_module(module_name)
            
            # Remove from collections
            del self.modules[module_name]
            
            if module_name in self.module_classes:
                del self.module_classes[module_name]
            
            print(f"🗑️ Unregistered module: {module_name}")
            
            # Save updated registry
            self._save_registry()
    
    def get_module_statistics(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific module"""
        if module_name not in self.modules:
            return None
        
        module_info = self.modules[module_name]
        
        stats = {
            'name': module_info.name,
            'status': module_info.status.value,
            'load_time': module_info.load_time,
            'dependencies_loaded': all(
                dep in self.modules and 
                self.modules[dep].status in [ModuleStatus.LOADED, ModuleStatus.ENABLED]
                for dep in module_info.dependencies
            ),
            'settings': module_info.settings
        }
        
        # Add module-specific statistics if available
        if module_info.instance and hasattr(module_info.instance, 'get_statistics'):
            try:
                module_stats = module_info.instance.get_statistics()
                stats['module_stats'] = module_stats
            except:
                pass
        
        return stats
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get overall module system statistics"""
        # Count modules by category
        modules_by_category = {}
        for module_info in self.modules.values():
            category = module_info.category.value
            if category not in modules_by_category:
                modules_by_category[category] = 0
            modules_by_category[category] += 1
        
        # Count modules by status
        modules_by_status = {}
        for module_info in self.modules.values():
            status = module_info.status.value
            if status not in modules_by_status:
                modules_by_status[status] = 0
            modules_by_status[status] += 1
        
        return {
            **self.stats,
            'modules_by_category': modules_by_category,
            'modules_by_status': modules_by_status,
            'total_dependencies': sum(len(m.dependencies) for m in self.modules.values()),
            'registry_file': str(self.registry_file),
            'module_dirs': [str(d) for d in self.module_dirs]
        }
    
    def export_modules(self, filepath: str, include_settings: bool = True):
        """Export module configuration to file"""
        export_data = {
            'modules': [],
            'statistics': self.get_system_statistics(),
            'timestamp': time.time()
        }
        
        for module_info in self.modules.values():
            module_data = module_info.to_dict()
            
            if not include_settings:
                module_data.pop('settings', None)
            
            export_data['modules'].append(module_data)
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Exported {len(export_data['modules'])} modules to {filepath}")
    
    def import_modules(self, filepath: str, overwrite: bool = False):
        """Import module configuration from file"""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            imported_count = 0
            
            for module_data in import_data.get('modules', []):
                module_name = module_data['name']
                
                if module_name in self.modules and not overwrite:
                    print(f"⚠️ Skipping existing module: {module_name}")
                    continue
                
                # Create module info
                module_info = ModuleInfo(
                    name=module_data['name'],
                    version=module_data['version'],
                    description=module_data['description'],
                    author=module_data['author'],
                    category=ModuleCategory(module_data['category']),
                    dependencies=module_data.get('dependencies', []),
                    settings=module_data.get('settings', {})
                )
                
                self.modules[module_name] = module_info
                imported_count += 1
            
            print(f"📥 Imported {imported_count} modules from {filepath}")
            
            # Save updated registry
            self._save_registry()
            
        except Exception as e:
            print(f"❌ Error importing modules: {e}")
    
    def cleanup(self):
        """Cleanup all loaded modules"""
        print("🧹 Cleaning up modules...")
        
        modules_to_unload = []
        for module_name, module_info in self.modules.items():
            if module_info.status in [ModuleStatus.LOADED, ModuleStatus.ENABLED]:
                modules_to_unload.append(module_name)
        
        for module_name in modules_to_unload:
            self.unload_module(module_name)
        
        print("✅ Modules cleaned up")