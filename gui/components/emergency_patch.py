"""
emergency_patch.py
Patch de emergência para numpy/matplotlib corrompidos
Executar antes de qualquer import problemático
"""

import sys
import importlib

class EmergencyMathPatch:
    """Patch de emergência para funções matemáticas"""
    
    @staticmethod
    def apply():
        """Aplica patches de emergência"""
        
        # Patch para numpy
        if 'numpy' in sys.modules:
            print("⚠️ Numpy detectado, aplicando patches...")
            try:
                # Tentar corrigir atributos faltando
                import math
                numpy_module = sys.modules['numpy']
                
                # Adicionar atributos básicos se faltarem
                if not hasattr(numpy_module, 'pi'):
                    numpy_module.pi = math.pi
                    print("  ✅ Patch: numpy.pi adicionado")
                
                if not hasattr(numpy_module, 'sin'):
                    numpy_module.sin = math.sin
                    print("  ✅ Patch: numpy.sin adicionado")
                
                if not hasattr(numpy_module, 'cos'):
                    numpy_module.cos = math.cos
                    print("  ✅ Patch: numpy.cos adicionado")
                    
            except Exception as e:
                print(f"  ❌ Falha no patch numpy: {e}")
        
        # Patch para matplotlib
        if 'matplotlib' in sys.modules:
            print("⚠️ Matplotlib detectado, aplicando patches...")
            try:
                matplotlib_module = sys.modules['matplotlib']
                
                # Patch para matplotlib.use
                if not hasattr(matplotlib_module, 'use'):
                    def dummy_use(*args, **kwargs):
                        print("⚠️ matplotlib.use() ignorado (modo patch)")
                    
                    matplotlib_module.use = dummy_use
                    print("  ✅ Patch: matplotlib.use adicionado")
                    
            except Exception as e:
                print(f"  ❌ Falha no patch matplotlib: {e}")
        
        # Criar módulo fallback se necessário
        if 'numpy' not in sys.modules:
            print("🔧 Criando módulo numpy fallback...")
            
            class FakeNumpy:
                """Módulo numpy fake para emergência"""
                def __init__(self):
                    import math
                    self.pi = math.pi
                    self.e = math.e
                    self.sin = math.sin
                    self.cos = math.cos
                    self.tan = math.tan
                    self.sqrt = math.sqrt
                    self.exp = math.exp
                    self.log = math.log
                    self.array = lambda x: x
                    self.linspace = lambda start, stop, num: [
                        start + i * (stop - start) / (num - 1) 
                        for i in range(num)
                    ]
                    
                def __getattr__(self, name):
                    # Retorna função dummy para qualquer atributo
                    def dummy(*args, **kwargs):
                        print(f"⚠️ numpy.{name}() chamado em modo fallback")
                        return 0
                    return dummy
            
            sys.modules['numpy'] = FakeNumpy()
            print("  ✅ Módulo numpy fallback criado")

# Aplicar patch automaticamente quando importado
EmergencyMathPatch.apply()