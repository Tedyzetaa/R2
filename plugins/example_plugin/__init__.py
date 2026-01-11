"""
Example Plugin for R2 Assistant V2.1
"""

import json
from typing import Dict, Any

PLUGIN_INFO = {
    'name': 'Example Plugin',
    'version': '1.0.0',
    'description': 'An example plugin for R2 Assistant',
    'author': 'R2 Team',
    'category': 'utility',
    'dependencies': [],
    'settings': {
        'enabled': True,
        'auto_start': False
    }
}

class ExamplePlugin:
    """Example plugin implementation"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = False
    
    def initialize(self):
        """Initialize plugin"""
        self.enabled = True
        print("✅ Example Plugin initialized")
    
    def handle_command(self, command: str, **kwargs) -> str:
        """Handle plugin command"""
        if command == "hello":
            return "Hello from Example Plugin!"
        elif command == "status":
            return f"Plugin status: {'Enabled' if self.enabled else 'Disabled'}"
        else:
            return f"Unknown command: {command}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get plugin statistics"""
        return {
            'enabled': self.enabled,
            'commands_handled': 0
        }
    
    def cleanup(self):
        """Cleanup plugin resources"""
        self.enabled = False
        print("🧹 Example Plugin cleaned up")

# Required export
PluginClass = ExamplePlugin