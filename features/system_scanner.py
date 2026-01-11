import psutil
import platform

class SystemScanner:
    def get_stats(self):
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        stats = {
            "cpu": cpu_usage,
            "ram": ram.percent,
            "disk": disk.percent,
            "os": platform.system(),
            "status": "NOMINAL" if cpu_usage < 80 else "CRÍTICO"
        }
        return stats