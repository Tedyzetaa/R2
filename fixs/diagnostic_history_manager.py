# diagnostic_history_manager.py
import sys
import inspect
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core.history_manager import HistoryManager
    
    print("=== INSPECTING HistoryManager ===")
    print(f"Module: {HistoryManager.__module__}")
    
    # Check __init__ signature
    sig = inspect.signature(HistoryManager.__init__)
    print(f"Signature: {sig}")
    print("Parameters:")
    for name, param in sig.parameters.items():
        print(f"  {name}: {param}")
    
except ImportError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()