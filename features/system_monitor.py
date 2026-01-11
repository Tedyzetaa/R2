import os
import platform
import asyncio

class SystemMonitor:
    def __init__(self, core):
        self.core = core

    def check_all(self):
        report = ["🛰️ [R2 DIAGNÓSTICO DE SISTEMA]\n"]
        
        # 1. Identificação do Host
        host = "Nuvem (Render)" if "render" in platform.node() or os.environ.get('RENDER') else "Local (PC)"
        report.append(f"📍 NÓ ATUAL: {host}")
        report.append(f"💻 OS: {platform.system()} {platform.release()}\n")

        # 2. Teste: Radar
        try:
            # Apenas verifica se a classe existe e inicializa
            if hasattr(self.core, 'radar_ops'):
                report.append("✅ [RADAR]: Operacional")
            else:
                report.append("❌ [RADAR]: Não carregado")
        except Exception as e:
            report.append(f"⚠️ [RADAR]: Erro - {str(e)[:20]}")

        # 3. Teste: Clima
        try:
            if hasattr(self.core, 'weather_ops'):
                report.append("✅ [CLIMA]: Operacional")
            else:
                report.append("❌ [CLIMA]: Não carregado")
        except Exception as e:
            report.append(f"⚠️ [CLIMA]: Erro - {str(e)[:20]}")

        # 4. Teste: Intel (LiveUAMap)
        try:
            from features.liveuamap_intel import FrontlineIntel
            test_intel = FrontlineIntel()
            report.append("✅ [INTEL]: Módulo integrado")
        except ImportError:
            report.append("❌ [INTEL]: Dependências ausentes")
        except Exception:
            report.append("⚠️ [INTEL]: Falha de conexão")

        # 5. Teste: Solar (NOAA)
        try:
            from features.noaa import NOAAService
            report.append("✅ [SOLAR]: Módulo pronto")
        except Exception:
            report.append("❌ [SOLAR]: Falha no serviço NOAA")

        # 6. Teste: Hardware/GUI (Tkinter/PyAutoGUI)
        try:
            import tkinter
            report.append("✅ [GUI]: Interface disponível (Local)")
        except:
            report.append("ℹ️ [GUI]: Desativado (Headless Mode)")

        report.append(f"\n⏱️ TIMESTAMP: {asyncio.run(self._get_time())}")
        return "\n".join(report)

    async def _get_time(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")