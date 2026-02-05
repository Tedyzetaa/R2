from .noaa_service import NOAAService

# Só importa o SolarMonitor se houver suporte a interface gráfica
try:
    import tkinter
    from .solar_monitor import SolarMonitor
except (ImportError, ModuleNotFoundError):
    SolarMonitor = None