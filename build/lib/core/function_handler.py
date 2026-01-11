"""
Function handler for executing system commands and integrations
"""

import importlib
import inspect
import json
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import re

class FunctionCategory(Enum):
    SYSTEM = "system"
    VOICE = "voice"
    TRADING = "trading"
    WEB = "web"
    MEDIA = "media"
    UTILITY = "utility"
    CUSTOM = "custom"

@dataclass
class FunctionDefinition:
    """Definition of an executable function"""
    name: str
    function: Callable
    description: str
    category: FunctionCategory
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    return_type: str = "string"
    requires_auth: bool = False
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'parameters': self.parameters,
            'return_type': self.return_type,
            'requires_auth': self.requires_auth,
            'enabled': self.enabled
        }

class FunctionHandler:
    """
    Handles execution of system functions and integrations
    """
    
    def __init__(self, config):
        self.config = config
        self.functions: Dict[str, FunctionDefinition] = {}
        self.modules: Dict[str, Any] = {}
        
        # Load built-in functions
        self._load_builtin_functions()
        
        # Load external modules
        self._load_external_modules()
        
        # Statistics
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'avg_execution_time': 0.0,
            'last_execution': 0
        }
        
        # Function cache for performance
        self.function_cache = {}
    
    def _load_builtin_functions(self):
        """Load built-in system functions"""
        
        # System functions
        self.register_function(
            name="get_system_info",
            function=self._get_system_info,
            description="Get system information and status",
            category=FunctionCategory.SYSTEM
        )
        
        self.register_function(
            name="get_current_time",
            function=self._get_current_time,
            description="Get current date and time",
            category=FunctionCategory.SYSTEM
        )
        
        self.register_function(
            name="calculate",
            function=self._calculate,
            description="Perform mathematical calculations",
            category=FunctionCategory.UTILITY,
            parameters={
                'expression': {
                    'type': 'string',
                    'description': 'Mathematical expression to calculate',
                    'required': True
                }
            }
        )
        
        self.register_function(
            name="convert_units",
            function=self._convert_units,
            description="Convert between different units",
            category=FunctionCategory.UTILITY,
            parameters={
                'value': {
                    'type': 'number',
                    'description': 'Value to convert',
                    'required': True
                },
                'from_unit': {
                    'type': 'string',
                    'description': 'Source unit',
                    'required': True
                },
                'to_unit': {
                    'type': 'string',
                    'description': 'Target unit',
                    'required': True
                }
            }
        )
        
        # Voice functions
        self.register_function(
            name="toggle_voice",
            function=self._toggle_voice,
            description="Toggle voice recognition on/off",
            category=FunctionCategory.VOICE
        )
        
        self.register_function(
            name="set_voice_activation",
            function=self._set_voice_activation,
            description="Set voice activation phrases",
            category=FunctionCategory.VOICE,
            parameters={
                'phrases': {
                    'type': 'array',
                    'description': 'List of activation phrases',
                    'required': True
                }
            }
        )
        
        print(f"✅ Loaded {len(self.functions)} built-in functions")
    
    def _load_external_modules(self):
        """Load external function modules"""
        try:
            # Try to load trading module
            from modules.trading_module import TradingModule
            trading_module = TradingModule(self.config)
            self.modules['trading'] = trading_module
            
            # Register trading functions
            if hasattr(trading_module, 'get_market_data'):
                self.register_function(
                    name="get_market_data",
                    function=trading_module.get_market_data,
                    description="Get cryptocurrency market data",
                    category=FunctionCategory.TRADING,
                    parameters={
                        'symbol': {
                            'type': 'string',
                            'description': 'Trading pair symbol (e.g., BTCUSDT)',
                            'required': True
                        }
                    },
                    requires_auth=True
                )
            
            print("✅ Loaded external modules")
            
        except ImportError as e:
            print(f"⚠️ Could not load external modules: {e}")
        except Exception as e:
            print(f"⚠️ Error loading external modules: {e}")
    
    def register_function(self, name: str, function: Callable, 
                         description: str, category: FunctionCategory,
                         parameters: Optional[Dict] = None,
                         return_type: str = "string",
                         requires_auth: bool = False):
        """Register a new function"""
        if name in self.functions:
            print(f"⚠️ Function '{name}' already registered, overwriting")
        
        self.functions[name] = FunctionDefinition(
            name=name,
            function=function,
            description=description,
            category=category,
            parameters=parameters or {},
            return_type=return_type,
            requires_auth=requires_auth
        )
        
        print(f"📝 Registered function: {name} ({category.value})")
    
    def unregister_function(self, name: str):
        """Unregister a function"""
        if name in self.functions:
            del self.functions[name]
            print(f"🗑️ Unregistered function: {name}")
    
    def list_functions(self, category: Optional[FunctionCategory] = None) -> List[Dict[str, Any]]:
        """List all available functions"""
        functions_list = []
        
        for func_def in self.functions.values():
            if category and func_def.category != category:
                continue
            
            if func_def.enabled:
                functions_list.append(func_def.to_dict())
        
        return functions_list
    
    def get_function(self, name: str) -> Optional[FunctionDefinition]:
        """Get function definition by name"""
        return self.functions.get(name)
    
    def execute_function(self, name: str, **kwargs) -> Tuple[bool, Any]:
        """
        Execute a registered function
        
        Returns:
            Tuple of (success, result)
        """
        if name not in self.functions:
            return False, f"Function '{name}' not found"
        
        func_def = self.functions[name]
        
        if not func_def.enabled:
            return False, f"Function '{name}' is disabled"
        
        # Check authentication if required
        if func_def.requires_auth and not self._check_authentication():
            return False, "Authentication required for this function"
        
        # Validate parameters
        validation_result = self._validate_parameters(func_def, kwargs)
        if not validation_result[0]:
            return validation_result
        
        # Execute function
        start_time = time.time()
        
        try:
            result = func_def.function(**kwargs)
            execution_time = time.time() - start_time
            
            # Update statistics
            self._update_statistics(True, execution_time)
            
            return True, result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_statistics(False, execution_time)
            
            error_msg = f"Error executing function '{name}': {str(e)}"
            print(f"❌ {error_msg}")
            
            return False, error_msg
    
    def _validate_parameters(self, func_def: FunctionDefinition, 
                           provided_params: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate function parameters"""
        required_params = []
        
        for param_name, param_info in func_def.parameters.items():
            if param_info.get('required', False) and param_name not in provided_params:
                required_params.append(param_name)
        
        if required_params:
            return False, f"Missing required parameters: {', '.join(required_params)}"
        
        # Type validation (simplified)
        for param_name, param_value in provided_params.items():
            if param_name in func_def.parameters:
                param_type = func_def.parameters[param_name].get('type', 'string')
                
                try:
                    if param_type == 'number':
                        float(param_value)
                    elif param_type == 'integer':
                        int(param_value)
                    elif param_type == 'boolean':
                        if isinstance(param_value, str):
                            if param_value.lower() not in ['true', 'false', '1', '0']:
                                raise ValueError(f"Invalid boolean value: {param_value}")
                except ValueError as e:
                    return False, f"Invalid type for parameter '{param_name}': {e}"
        
        return True, "Validation successful"
    
    def process_command(self, command: str) -> Optional[str]:
        """
        Process a natural language command and execute appropriate function
        
        Args:
            command: Natural language command
            
        Returns:
            Function result or None if no function matched
        """
        # Simple command parsing
        command_lower = command.lower()
        
        # Check for function patterns
        for func_def in self.functions.values():
            if not func_def.enabled:
                continue
            
            # Check if command contains function keywords
            func_name_words = func_def.name.split('_')
            func_desc_words = func_def.description.lower().split()
            
            # Check for matches
            matches = []
            for word in func_name_words:
                if word in command_lower:
                    matches.append(word)
            
            for word in func_desc_words[:5]:  # First 5 words of description
                if len(word) > 3 and word in command_lower:
                    matches.append(word)
            
            if len(matches) >= 2:  # At least 2 matching words
                print(f"🎯 Matched command '{command}' to function '{func_def.name}'")
                
                # Try to extract parameters from command
                params = self._extract_parameters(command, func_def)
                
                # Execute function
                success, result = self.execute_function(func_def.name, **params)
                
                if success:
                    return str(result)
                else:
                    return f"Error: {result}"
        
        return None
    
    def _extract_parameters(self, command: str, 
                           func_def: FunctionDefinition) -> Dict[str, Any]:
        """Extract parameters from natural language command"""
        params = {}
        
        # Simple regex-based extraction
        for param_name, param_info in func_def.parameters.items():
            param_type = param_info.get('type', 'string')
            
            # Look for patterns in command
            if param_type == 'number':
                # Extract numbers
                numbers = re.findall(r'\d+\.?\d*', command)
                if numbers:
                    params[param_name] = float(numbers[0]) if '.' in numbers[0] else int(numbers[0])
            
            elif param_type == 'string':
                # Extract quoted strings
                quoted = re.findall(r'"([^"]*)"', command)
                if quoted:
                    params[param_name] = quoted[0]
        
        return params
    
    def _update_statistics(self, success: bool, execution_time: float):
        """Update execution statistics"""
        self.stats['total_executions'] += 1
        self.stats['last_execution'] = time.time()
        
        if success:
            self.stats['successful_executions'] += 1
        else:
            self.stats['failed_executions'] += 1
        
        # Update average execution time
        total_successful = self.stats['successful_executions']
        if total_successful > 0:
            self.stats['avg_execution_time'] = (
                (self.stats['avg_execution_time'] * (total_successful - 1) + execution_time)
                / total_successful
            )
    
    def _check_authentication(self) -> bool:
        """Check if user is authenticated"""
        # Simplified authentication check
        # In production, implement proper authentication
        return True
    
    # Built-in functions implementation
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        import platform
        import psutil
        
        return {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent,
            'boot_time': psutil.boot_time()
        }
    
    def _get_current_time(self) -> str:
        """Get current date and time"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _calculate(self, expression: str) -> float:
        """Perform mathematical calculation"""
        # Safe evaluation
        allowed_chars = '0123456789+-*/(). '
        if any(c not in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        
        try:
            result = eval(expression)
            return float(result)
        except Exception as e:
            raise ValueError(f"Calculation error: {e}")
    
    def _convert_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert between units"""
        # Simplified conversion dictionary
        conversions = {
            'km_mi': 0.621371,  # kilometers to miles
            'mi_km': 1.60934,   # miles to kilometers
            'kg_lb': 2.20462,   # kilograms to pounds
            'lb_kg': 0.453592,  # pounds to kilograms
            'c_f': lambda c: c * 9/5 + 32,  # celsius to fahrenheit
            'f_c': lambda f: (f - 32) * 5/9,  # fahrenheit to celsius
        }
        
        conversion_key = f"{from_unit.lower()}_{to_unit.lower()}"
        
        if conversion_key in conversions:
            conversion = conversions[conversion_key]
            if callable(conversion):
                return conversion(value)
            else:
                return value * conversion
        else:
            raise ValueError(f"Unsupported conversion: {from_unit} to {to_unit}")
    
    def _toggle_voice(self) -> str:
        """Toggle voice recognition"""
        # This would be connected to the voice engine
        return "Voice recognition toggled (placeholder)"
    
    def _set_voice_activation(self, phrases: List[str]) -> str:
        """Set voice activation phrases"""
        # This would be connected to the voice engine
        return f"Voice activation phrases set: {', '.join(phrases)}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get function handler statistics"""
        return {
            **self.stats,
            'total_functions': len(self.functions),
            'enabled_functions': len([f for f in self.functions.values() if f.enabled]),
            'loaded_modules': list(self.modules.keys())
        }
    
    def export_functions(self, filepath: str):
        """Export function definitions to file"""
        functions_data = {
            'functions': [f.to_dict() for f in self.functions.values()],
            'statistics': self.get_statistics(),
            'timestamp': time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(functions_data, f, indent=2)
    
    def import_functions(self, filepath: str):
        """Import function definitions from file"""
        try:
            with open(filepath, 'r') as f:
                functions_data = json.load(f)
            
            # Note: This would need to re-register functions
            # Implementation depends on serialization format
            print(f"📥 Imported functions from {filepath}")
            
        except Exception as e:
            print(f"❌ Error importing functions: {e}")