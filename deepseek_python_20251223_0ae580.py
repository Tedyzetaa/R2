#!/usr/bin/env python3
"""
Script de correção para instalação do módulo NOAA - R2 Assistant
Corrige o erro de diretório vazio e instala os arquivos necessários
"""

import os
import sys
import shutil
import json
import subprocess
from pathlib import Path

def criar_estrutura_diretorios():
    """Cria a estrutura completa de diretórios necessária"""
    
    diretorios = [
        "noaa_updates",
        "features/noaa",
        "commands",
        "gui/components",
        "data/noaa/cache",
        "data/noaa/reports",
        "data/noaa/historical",
        "data/noaa/alerts",
        "logs/noaa",
        "gui",
        "core"
    ]
    
    for dir_path in diretorios:
        os.makedirs(dir_path, exist_ok=True)
        print(f"[OK] Diretório criado: {dir_path}")
    
    return True

def criar_noaa_service():
    """Cria o arquivo noaa_service.py básico"""
    
    conteudo = '''#!/usr/bin/env python3
"""
NOAA Service - Monitoramento de Clima Espacial
Versão: 2.1.0
Autor: R2 Assistant Team
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    ALERT = "ALERT"
    SEVERE = "SEVERE"

class SolarFlareClass(Enum):
    A = "A"
    B = "B"
    C = "C"
    M = "M"
    X = "X"
    X_PLUS = "X+"

@dataclass
class SolarFlare:
    class_value: SolarFlareClass
    peak_time: datetime
    intensity: float
    active_region: str = ""
    duration_minutes: float = 0.0
    noaa_scale: AlertLevel = AlertLevel.NORMAL
    effects: List[str] = field(default_factory=list)

@dataclass
class SolarWind:
    speed: float  # km/s
    density: float  # p/cm³
    temperature: float  # K
    bz: float  # nT (componente Bz)
    bt: float  # nT (magnitude total)
    timestamp: datetime

@dataclass
class GeomagneticStorm:
    level: str  # G1-G5
    kp_index: float
    dst_index: float
    start_time: datetime
    expected_end: Optional[datetime] = None
    noaa_scale: AlertLevel = AlertLevel.NORMAL

@dataclass
class SpaceWeatherData:
    timestamp: datetime
    solar_flares: List[SolarFlare] = field(default_factory=list)
    geomagnetic_storms: List[GeomagneticStorm] = field(default_factory=list)
    solar_wind: Optional[SolarWind] = None
    coronal_mass_ejections: List[Dict] = field(default_factory=list)
    proton_events: List[Dict] = field(default_factory=list)
    kp_index: float = 0.0
    dst_index: float = 0.0
    aurora_probability: Dict[str, float] = field(default_factory=dict)
    sunspot_number: int = 0
    solar_flux: float = 0.0
    alerts: List[Dict] = field(default_factory=list)
    overall_alert: AlertLevel = AlertLevel.NORMAL

class NOAAService:
    """Serviço principal para monitoramento NOAA"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self.current_data: Optional[SpaceWeatherData] = None
        self.is_running = False
        
        # Endpoints NOAA
        self.endpoints = {
            "solar_wind": "https://services.swpc.noaa.gov/json/ace/swepam.json",
            "geomagnetic_indices": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
            "solar_flares": "https://services.swpc.noaa.gov/json/goes/primary/xray-flares.json",
            "cme_data": "https://services.swpc.noaa.gov/json/llsdat.json",
            "proton_flux": "https://services.swpc.noaa.gov/json/goes/proton-flux.json",
            "aurora_forecast": "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json",
            "sunspot_regions": "https://services.swpc.noaa.gov/json/solar-cycle/sunspots.json"
        }
        
        logger.info("NOAA Service inicializado")
    
    def _load_config(self, config_path: str) -> Dict:
        """Carrega configuração do arquivo"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {
                "noaa_update_interval": 300,
                "cache_ttl": 300,
                "alert_thresholds": {
                    "solar_flare": ["M", "X", "X+"],
                    "kp_index": 6.0,
                    "solar_wind_speed": 600
                }
            }
    
    async def start(self):
        """Inicia o serviço NOAA"""
        if self.is_running:
            return
        
        self.session = aiohttp.ClientSession()
        self.is_running = True
        
        # Primeira atualização
        await self.update_all_data()
        
        logger.info("NOAA Service iniciado")
    
    async def stop(self):
        """Para o serviço NOAA"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.session:
            await self.session.close()
        
        logger.info("NOAA Service parado")
    
    async def fetch_data(self, endpoint: str) -> Optional[Dict]:
        """Busca dados de um endpoint NOAA"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(endpoint, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Erro {response.status} ao buscar {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Erro ao buscar {endpoint}: {e}")
            return None
    
    async def update_solar_wind(self):
        """Atualiza dados do vento solar"""
        data = await self.fetch_data(self.endpoints["solar_wind"])
        if data and len(data) > 0:
            latest = data[-1]
            try:
                solar_wind = SolarWind(
                    speed=float(latest.get("speed", 0)),
                    density=float(latest.get("density", 0)),
                    temperature=float(latest.get("temperature", 0)),
                    bz=float(latest.get("bz", 0)),
                    bt=float(latest.get("bt", 0)),
                    timestamp=datetime.strptime(latest.get("time_tag", ""), "%Y-%m-%d %H:%M:%S.%f")
                )
                return solar_wind
            except (ValueError, KeyError) as e:
                logger.error(f"Erro ao processar vento solar: {e}")
        
        return None
    
    async def update_kp_index(self):
        """Atualiza índice Kp"""
        data = await self.fetch_data(self.endpoints["geomagnetic_indices"])
        if data and len(data) > 0:
            # Pega o último valor válido
            for item in reversed(data):
                try:
                    if len(item) >= 2:
                        kp_value = float(item[1])
                        if kp_value >= 0:
                            return kp_value
                except (ValueError, IndexError):
                    continue
        
        return 0.0
    
    async def update_all_data(self):
        """Atualiza todos os dados NOAA"""
        logger.info("Atualizando dados NOAA...")
        
        # Atualiza dados em paralelo
        tasks = [
            self.update_solar_wind(),
            self.update_kp_index(),
            # Outras atualizações aqui
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        solar_wind = results[0] if not isinstance(results[0], Exception) else None
        kp_index = results[1] if not isinstance(results[1], Exception) else 0.0
        
        # Cria objeto de dados
        self.current_data = SpaceWeatherData(
            timestamp=datetime.now(),
            solar_wind=solar_wind,
            kp_index=kp_index,
            overall_alert=self._calculate_alert_level(kp_index, solar_wind)
        )
        
        self.last_update = datetime.now()
        logger.info(f"Dados NOAA atualizados: Kp={kp_index}, Vento Solar={'OK' if solar_wind else 'N/A'}")
        
        return self.current_data
    
    def _calculate_alert_level(self, kp_index: float, solar_wind: Optional[SolarWind]) -> AlertLevel:
        """Calcula nível de alerta baseado nos dados"""
        if kp_index >= 8.0:
            return AlertLevel.SEVERE
        elif kp_index >= 6.0:
            return AlertLevel.ALERT
        elif kp_index >= 5.0:
            return AlertLevel.WARNING
        elif kp_index >= 4.0:
            return AlertLevel.WATCH
        else:
            return AlertLevel.NORMAL
    
    def get_summary(self) -> Dict:
        """Retorna resumo dos dados atuais"""
        if not self.current_data:
            return {"status": "no_data", "message": "Nenhum dado disponível"}
        
        summary = {
            "status": "ok",
            "timestamp": self.current_data.timestamp.isoformat(),
            "kp_index": self.current_data.kp_index,
            "overall_alert": self.current_data.overall_alert.value,
            "solar_wind": {
                "speed": self.current_data.solar_wind.speed if self.current_data.solar_wind else 0,
                "density": self.current_data.solar_wind.density if self.current_data.solar_wind else 0,
                "bz": self.current_data.solar_wind.bz if self.current_data.solar_wind else 0
            } if self.current_data.solar_wind else None,
            "alerts": self.current_data.alerts
        }
        
        return summary

# Instância global do serviço
_noaa_service = None

def get_noaa_service() -> NOAAService:
    """Retorna instância global do serviço NOAA"""
    global _noaa_service
    if _noaa_service is None:
        _noaa_service = NOAAService()
    return _noaa_service

async def main_test():
    """Função de teste principal"""
    service = get_noaa_service()
    await service.start()
    
    try:
        # Aguarda um pouco para dados serem carregados
        await asyncio.sleep(2)
        
        # Obtém resumo
        summary = service.get_summary()
        print("Resumo NOAA:", json.dumps(summary, indent=2))
        
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main_test())
'''
    
    caminho = "noaa_updates/noaa_service.py"
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"[OK] Arquivo criado: {caminho}")
    return True

def criar_solar_monitor():
    """Cria o arquivo solar_monitor.py"""
    
    conteudo = '''#!/usr/bin/env python3
"""
Solar Monitor - Interface gráfica para monitoramento solar
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
import asyncio
import threading

class SolarMonitor(ctk.CTkToplevel):
    """Janela de monitoramento solar"""
    
    def __init__(self, parent, noaa_service):
        super().__init__(parent)
        
        self.noaa_service = noaa_service
        self.parent = parent
        
        # Configuração da janela
        self.title("R2 Assistant - Solar Monitor")
        self.geometry("900x600")
        
        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Cores do tema Sci-Fi
        self.colors = {
            "bg": "#0a0a12",
            "primary": "#00ffff",
            "secondary": "#0099ff",
            "accent": "#ff00ff",
            "success": "#00ff88",
            "warning": "#ffaa00",
            "danger": "#ff0066",
            "text": "#ffffff",
            "text_dim": "#8888aa"
        }
        
        self.configure(fg_color=self.colors["bg"])
        
        # Criar interface
        self._create_widgets()
        
        # Iniciar atualização periódica
        self.update_interval = 60000  # 1 minuto
        self._schedule_update()
    
    def _create_widgets(self):
        """Cria os widgets da interface"""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color=self.colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🌌 SOLAR MONITOR",
            font=("Courier", 24, "bold"),
            text_color=self.colors["primary"]
        )
        title_label.pack(pady=(0, 20))
        
        # Frame de status
        status_frame = ctk.CTkFrame(main_frame, fg_color="#111122")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # Labels de status
        self.kp_label = ctk.CTkLabel(
            status_frame,
            text="Kp Index: --",
            font=("Courier", 14),
            text_color=self.colors["text"]
        )
        self.kp_label.pack(side="left", padx=20, pady=10)
        
        self.wind_label = ctk.CTkLabel(
            status_frame,
            text="Solar Wind: -- km/s",
            font=("Courier", 14),
            text_color=self.colors["text"]
        )
        self.wind_label.pack(side="left", padx=20, pady=10)
        
        self.alert_label = ctk.CTkLabel(
            status_frame,
            text="Status: NORMAL",
            font=("Courier", 14, "bold"),
            text_color=self.colors["success"]
        )
        self.alert_label.pack(side="right", padx=20, pady=10)
        
        # Frame de gráficos
        graph_frame = ctk.CTkFrame(main_frame, fg_color="#111122")
        graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Criar gráfico placeholder
        fig, ax = plt.subplots(figsize=(8, 4), facecolor='#0a0a12')
        ax.set_facecolor('#0a0a12')
        
        # Dados de exemplo
        hours = np.arange(24)
        kp_values = 2 + np.sin(hours / 3) + np.random.normal(0, 0.5, 24)
        
        ax.plot(hours, kp_values, color='#00ffff', linewidth=2)
        ax.fill_between(hours, kp_values, alpha=0.3, color='#00ffff')
        
        ax.set_xlabel('Hours', color='#8888aa')
        ax.set_ylabel('Kp Index', color='#8888aa')
        ax.set_title('Geomagnetic Activity (Last 24h)', color='#ffffff')
        ax.grid(True, alpha=0.2, color='#444466')
        ax.tick_params(colors='#8888aa')
        
        for spine in ax.spines.values():
            spine.set_color('#444466')
        
        # Embed no tkinter
        canvas = FigureCanvasTkAgg(fig, graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de controles
        control_frame = ctk.CTkFrame(main_frame, fg_color="#111122")
        control_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Botões
        self.refresh_btn = ctk.CTkButton(
            control_frame,
            text="🔄 Refresh",
            command=self.refresh_data,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["primary"]
        )
        self.refresh_btn.pack(side="left", padx=5)
        
        self.alert_btn = ctk.CTkButton(
            control_frame,
            text="⚠️ Alerts",
            command=self.show_alerts,
            fg_color=self.colors["warning"],
            hover_color="#ff8800"
        )
        self.alert_btn.pack(side="left", padx=5)
        
        self.close_btn = ctk.CTkButton(
            control_frame,
            text="✕ Close",
            command=self.destroy,
            fg_color="#444466",
            hover_color="#666688"
        )
        self.close_btn.pack(side="right", padx=5)
        
        # Label de atualização
        self.update_label = ctk.CTkLabel(
            control_frame,
            text="Last update: --:--",
            font=("Courier", 10),
            text_color=self.colors["text_dim"]
        )
        self.update_label.pack(side="right", padx=20)
    
    def refresh_data(self):
        """Atualiza dados manualmente"""
        threading.Thread(target=self._update_data_thread, daemon=True).start()
    
    def _update_data_thread(self):
        """Thread para atualizar dados"""
        try:
            # Em um ambiente real, aqui você chamaria o NOAA Service
            # Por enquanto, apenas simula dados
            self.after(0, self._update_display, {
                "kp_index": 2.3,
                "solar_wind_speed": 420,
                "status": "NORMAL"
            })
        except Exception as e:
            print(f"Erro ao atualizar dados: {e}")
    
    def _update_display(self, data):
        """Atualiza a exibição com novos dados"""
        self.kp_label.configure(text=f"Kp Index: {data.get('kp_index', '--'):.1f}")
        self.wind_label.configure(text=f"Solar Wind: {data.get('solar_wind_speed', '--'):.0f} km/s")
        
        status = data.get('status', 'NORMAL')
        status_colors = {
            'NORMAL': self.colors["success"],
            'WATCH': self.colors["secondary"],
            'WARNING': self.colors["warning"],
            'ALERT': self.colors["danger"],
            'SEVERE': self.colors["danger"]
        }
        
        self.alert_label.configure(
            text=f"Status: {status}",
            text_color=status_colors.get(status, self.colors["text"])
        )
        
        current_time = datetime.now().strftime("%H:%M:%S")
        self.update_label.configure(text=f"Last update: {current_time}")
    
    def _schedule_update(self):
        """Agenda próxima atualização automática"""
        self.after(self.update_interval, self._auto_update)
    
    def _auto_update(self):
        """Atualização automática"""
        self.refresh_data()
        self._schedule_update()
    
    def show_alerts(self):
        """Mostra janela de alertas"""
        alert_window = ctk.CTkToplevel(self)
        alert_window.title("Solar Alerts")
        alert_window.geometry("400x300")
        alert_window.configure(fg_color=self.colors["bg"])
        
        title = ctk.CTkLabel(
            alert_window,
            text="🚨 ACTIVE ALERTS",
            font=("Courier", 18, "bold"),
            text_color=self.colors["warning"]
        )
        title.pack(pady=20)
        
        # Lista de alertas
        alerts_text = ctk.CTkTextbox(alert_window, height=150)
        alerts_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        alerts_text.insert("1.0", "No active alerts at this time.")
        alerts_text.configure(state="disabled")

def test_monitor():
    """Testa o monitor solar"""
    root = ctk.CTk()
    root.withdraw()  # Esconde a janela principal
    
    monitor = SolarMonitor(root, None)
    monitor.mainloop()

if __name__ == "__main__":
    test_monitor()
'''
    
    caminho = "noaa_updates/solar_monitor.py"
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"[OK] Arquivo criado: {caminho}")
    return True

def criar_noaa_commands():
    """Cria o arquivo noaa_commands.py"""
    
    conteudo = '''#!/usr/bin/env python3
"""
NOAA Commands - Comandos de voz/texto para funcionalidades NOAA
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

class NOAACommands:
    """Manipulador de comandos NOAA"""
    
    def __init__(self, noaa_service):
        self.noaa_service = noaa_service
        self.commands = self._register_commands()
    
    def _register_commands(self) -> Dict:
        """Registra todos os comandos NOAA"""
        
        commands = {
            "clima espacial": {
                "func": self.cmd_space_weather,
                "description": "Relatório completo de clima espacial",
                "aliases": ["climaespacial", "space weather", "weather space"]
            },
            "vento solar": {
                "func": self.cmd_solar_wind,
                "description": "Dados do vento solar em tempo real",
                "aliases": ["solar wind", "ventosolar", "vento"]
            },
            "alerta solar": {
                "func": self.cmd_solar_alerts,
                "description": "Verificar alertas solares ativos",
                "aliases": ["alertas solares", "solar alert", "alerta"]
            },
            "tempestade geomagnética": {
                "func": self.cmd_geomagnetic_storm,
                "description": "Status de tempestades geomagnéticas",
                "aliases": ["tempestade", "geomagnetic storm", "storm"]
            },
            "aurora boreal": {
                "func": self.cmd_aurora,
                "description": "Previsão de aurora boreal/austral",
                "aliases": ["aurora", "aurora forecast", "aurora boreal"]
            },
            "flares solares": {
                "func": self.cmd_solar_flares,
                "description": "Atividade de flares solares recentes",
                "aliases": ["flares", "solar flares", "erupções solares"]
            },
            "manchas solares": {
                "func": self.cmd_sunspots,
                "description": "Regiões ativas no Sol",
                "aliases": ["sunspots", "manchas", "regiões ativas"]
            },
            "status noaa": {
                "func": self.cmd_noaa_status,
                "description": "Status do serviço NOAA",
                "aliases": ["noaa", "status noaa", "noaa status"]
            },
            "relatório noaa": {
                "func": self.cmd_noaa_report,
                "description": "Relatório detalhado NOAA",
                "aliases": ["relatório", "report", "noaa report"]
            }
        }
        
        return commands
    
    async def cmd_space_weather(self, args: List[str] = None) -> Dict:
        """Comando: clima espacial - Relatório completo"""
        
        if not self.noaa_service or not self.noaa_service.current_data:
            return {
                "success": False,
                "message": "Serviço NOAA não disponível",
                "voice_response": "O serviço de clima espacial não está disponível no momento."
            }
        
        data = self.noaa_service.current_data
        
        # Criar relatório
        report = {
            "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "kp_index": f"{data.kp_index:.1f}",
            "solar_wind": {
                "speed": f"{data.solar_wind.speed:.0f}" if data.solar_wind else "N/A",
                "density": f"{data.solar_wind.density:.1f}" if data.solar_wind else "N/A",
                "bz": f"{data.solar_wind.bz:.1f}" if data.solar_wind else "N/A"
            },
            "alerts": len(data.alerts),
            "overall_alert": data.overall_alert.value,
            "solar_flares": len(data.solar_flares)
        }
        
        # Resposta de voz
        alert_level = data.overall_alert.value
        if alert_level == "NORMAL":
            voice_msg = f"Status geral: NORMAL. Índice Kp: {data.kp_index:.1f}. "
        elif alert_level == "WARNING":
            voice_msg = f"ALERTA: Nível {alert_level}. Índice Kp: {data.kp_index:.1f}. "
        else:
            voice_msg = f"Status: {alert_level}. Índice Kp: {data.kp_index:.1f}. "
        
        if data.solar_wind:
            voice_msg += f"Vento solar: {data.solar_wind.speed:.0f} quilômetros por segundo. "
        
        voice_msg += f"{len(data.alerts)} alertas ativos. "
        
        if len(data.solar_flares) > 0:
            voice_msg += f"{len(data.solar_flares)} flares solares detectados recentemente."
        else:
            voice_msg += "Nenhum flare solar significativo nas últimas 24 horas."
        
        return {
            "success": True,
            "data": report,
            "message": "Relatório de clima espacial gerado",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_solar_wind(self, args: List[str] = None) -> Dict:
        """Comando: vento solar - Dados do vento solar"""
        
        if not self.noaa_service or not self.noaa_service.current_data:
            return {
                "success": False,
                "message": "Dados não disponíveis",
                "voice_response": "Dados do vento solar não disponíveis."
            }
        
        data = self.noaa_service.current_data
        
        if not data.solar_wind:
            return {
                "success": False,
                "message": "Dados do vento solar não disponíveis",
                "voice_response": "Não há dados do vento solar disponíveis no momento."
            }
        
        wind = data.solar_wind
        
        # Analisar direção do Bz
        if wind.bz < -5:
            bz_status = "Sul (Favorável a tempestades)"
            bz_icon = "↓"
        elif wind.bz > 5:
            bz_status = "Norte (Estável)"
            bz_icon = "↑"
        else:
            bz_status = "Neutro"
            bz_icon = "→"
        
        report = {
            "speed_km_s": f"{wind.speed:.0f}",
            "density_p_cm3": f"{wind.density:.1f}",
            "temperature_k": f"{wind.temperature:.0f}",
            "bz_nT": f"{wind.bz:.1f}",
            "bz_direction": bz_status,
            "bz_icon": bz_icon,
            "timestamp": wind.timestamp.strftime("%H:%M:%S")
        }
        
        voice_msg = f"Vento solar: {wind.speed:.0f} quilômetros por segundo. "
        voice_msg += f"Densidade: {wind.density:.1f} partículas por centímetro cúbico. "
        voice_msg += f"Campo magnético Bz: {wind.bz:.1f} nano Tesla, direção {bz_status}."
        
        return {
            "success": True,
            "data": report,
            "message": "Dados do vento solar",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_solar_alerts(self, args: List[str] = None) -> Dict:
        """Comando: alerta solar - Alertas ativos"""
        
        # Simular dados de alerta
        alerts = [
            {
                "id": 1,
                "type": "SOLAR_FLARE",
                "level": "WATCH",
                "message": "Aumento na atividade de flares classe C",
                "time": "2024-01-15 14:30:00"
            },
            {
                "id": 2,
                "type": "GEOMAGNETIC",
                "level": "NORMAL",
                "message": "Condições geomagnéticas estáveis",
                "time": "2024-01-15 13:45:00"
            }
        ]
        
        active_alerts = [a for a in alerts if a["level"] != "NORMAL"]
        
        if active_alerts:
            alert_text = "\\n".join([f"{a['type']}: {a['message']}" for a in active_alerts])
            voice_msg = f"{len(active_alerts)} alertas ativos. {active_alerts[0]['message']}"
        else:
            alert_text = "Nenhum alerta ativo no momento"
            voice_msg = "Nenhum alerta solar ativo. Todas as condições estão normais."
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "active_count": len(active_alerts),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            },
            "message": alert_text,
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_geomagnetic_storm(self, args: List[str] = None) -> Dict:
        """Comando: tempestade geomagnética"""
        
        if not self.noaa_service or not self.noaa_service.current_data:
            kp = 2.3
        else:
            kp = self.noaa_service.current_data.kp_index
        
        # Determinar nível da tempestade
        if kp >= 8.0:
            level = "G5 (Extreme)"
            voice_level = "G5 Extrema"
        elif kp >= 7.0:
            level = "G4 (Severe)"
            voice_level = "G4 Severa"
        elif kp >= 6.0:
            level = "G3 (Strong)"
            voice_level = "G3 Forte"
        elif kp >= 5.0:
            level = "G2 (Moderate)"
            voice_level = "G2 Moderada"
        elif kp >= 4.0:
            level = "G1 (Minor)"
            voice_level = "G1 Menor"
        else:
            level = "None"
            voice_level = "Nenhuma"
        
        report = {
            "kp_index": f"{kp:.1f}",
            "storm_level": level,
            "activity": "Quiet" if kp < 4 else "Active",
            "aurora_chance": "High" if kp >= 6 else "Moderate" if kp >= 4 else "Low"
        }
        
        voice_msg = f"Índice Kp atual: {kp:.1f}. "
        if kp < 4:
            voice_msg += "Nenhuma tempestade geomagnética ativa. Condições calmas."
        else:
            voice_msg += f"Tempestade nível {voice_level} ativa. "
            voice_msg += f"Probabilidade de aurora: {report['aurora_chance']}."
        
        return {
            "success": True,
            "data": report,
            "message": f"Status tempestade geomagnética: {level}",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_aurora(self, args: List[str] = None) -> Dict:
        """Comando: aurora boreal - Previsão de aurora"""
        
        # Dados simulados de aurora
        regions = {
            "Alaska": 65,
            "Canada": 70,
            "Scandinavia": 75,
            "Russia": 60,
            "Antarctica": 80,
            "New Zealand": 30,
            "Scotland": 40
        }
        
        max_region = max(regions, key=regions.get)
        max_prob = regions[max_region]
        
        report = {
            "regions": regions,
            "max_region": max_region,
            "max_probability": max_prob,
            "visibility": "Good" if max_prob > 50 else "Fair" if max_prob > 30 else "Poor",
            "next_24h": "Increasing" if max_prob > 60 else "Stable" if max_prob > 40 else "Decreasing"
        }
        
        voice_msg = f"Previsão de aurora: Probabilidade máxima de {max_prob}% em {max_region}. "
        voice_msg += f"Visibilidade: {report['visibility']}. Tendência para as próximas 24 horas: {report['next_24h']}."
        
        return {
            "success": True,
            "data": report,
            "message": f"Previsão de aurora: {max_prob}% em {max_region}",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_solar_flares(self, args: List[str] = None) -> Dict:
        """Comando: flares solares"""
        
        # Dados simulados de flares
        flares = [
            {"class": "C2.4", "region": "AR13452", "peak": "14:30", "duration": "18min"},
            {"class": "B8.7", "region": "AR13451", "peak": "12:15", "duration": "42min"},
            {"class": "C1.2", "region": "AR13449", "peak": "09:45", "duration": "25min"}
        ]
        
        x_class = any(f["class"].startswith("X") for f in flares)
        m_class = any(f["class"].startswith("M") for f in flares)
        
        if x_class:
            activity = "HIGH (X-class detected)"
        elif m_class:
            activity = "MODERATE (M-class detected)"
        elif any(f["class"].startswith("C") for f in flares):
            activity = "LOW (C-class only)"
        else:
            activity = "VERY LOW"
        
        report = {
            "flares_24h": len(flares),
            "largest_flare": flares[0]["class"] if flares else "None",
            "activity_level": activity,
            "recent_flares": flares[:3],
            "x_ray_background": "C1.2"
        }
        
        voice_msg = f"{len(flares)} flares solares nas últimas 24 horas. "
        if flares:
            voice_msg += f"Maior flare: classe {flares[0]['class']} na região {flares[0]['region']}. "
        voice_msg += f"Nível de atividade: {activity}."
        
        return {
            "success": True,
            "data": report,
            "message": f"Atividade de flares: {activity}",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_sunspots(self, args: List[str] = None) -> Dict:
        """Comando: manchas solares"""
        
        report = {
            "sunspot_number": 87,
            "regions": 6,
            "largest_region": "AR13452",
            "magnetic_complexity": "Beta-Gamma",
            "flare_potential": "Medium",
            "location": "NE Quadrant"
        }
        
        voice_msg = f"{report['regions']} regiões ativas no Sol. "
        voice_msg += f"Número de manchas solares: {report['sunspot_number']}. "
        voice_msg += f"Região mais ativa: {report['largest_region']} com complexidade magnética {report['magnetic_complexity']}. "
        voice_msg += f"Potencial para flares: {report['flare_potential']}."
        
        return {
            "success": True,
            "data": report,
            "message": f"Manchas solares: {report['regions']} regiões ativas",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_noaa_status(self, args: List[str] = None) -> Dict:
        """Comando: status noaa"""
        
        if self.noaa_service and self.noaa_service.is_running:
            status = "RUNNING"
            last_update = self.noaa_service.last_update.strftime("%H:%M:%S") if self.noaa_service.last_update else "Never"
            voice_msg = "Serviço NOAA está rodando. "
        else:
            status = "STOPPED"
            last_update = "N/A"
            voice_msg = "Serviço NOAA não está rodando. "
        
        report = {
            "service_status": status,
            "last_update": last_update,
            "endpoints": len(self.noaa_service.endpoints) if self.noaa_service else 0,
            "data_available": self.noaa_service.current_data is not None if self.noaa_service else False
        }
        
        voice_msg += f"Última atualização: {last_update}. "
        
        if self.noaa_service and self.noaa_service.current_data:
            voice_msg += "Dados atuais disponíveis."
        else:
            voice_msg += "Nenhum dado disponível."
        
        return {
            "success": True,
            "data": report,
            "message": f"Status NOAA: {status}",
            "voice_response": voice_msg,
            "show_panel": False
        }
    
    async def cmd_noaa_report(self, args: List[str] = None) -> Dict:
        """Comando: relatório noaa"""
        
        # Gerar relatório completo
        report_data = {
            "generated": datetime.now().isoformat(),
            "sections": [
                "Space Weather Overview",
                "Solar Activity",
                "Geomagnetic Conditions",
                "Solar Wind Parameters",
                "Aurora Forecast",
                "Alert Summary"
            ],
            "summary": "Space weather conditions are currently quiet with no significant activity expected in the next 24 hours.",
            "recommendations": [
                "No impacts to satellite operations expected",
                "No impacts to power grid operations expected",
                "Aurora visible at high latitudes only"
            ]
        }
        
        voice_msg = "Relatório NOAA gerado. "
        voice_msg += "Condições de clima espacial atualmente calmas. "
        voice_msg += "Nenhuma atividade significativa esperada nas próximas 24 horas."
        
        return {
            "success": True,
            "data": report_data,
            "message": "Relatório NOAA gerado com sucesso",
            "voice_response": voice_msg,
            "show_panel": True,
            "export_formats": ["json", "txt"]
        }

# Teste dos comandos
async def test_commands():
    """Testa os comandos NOAA"""
    
    # Criar serviço simulado
    class MockNOAAService:
        def __init__(self):
            self.current_data = None
            self.is_running = True
            self.last_update = datetime.now()
            self.endpoints = {}
    
    service = MockNOAAService()
    commands = NOAACommands(service)
    
    # Testar comando específico
    result = await commands.cmd_space_weather()
    print("Teste comando 'clima espacial':")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_commands())
'''
    
    caminho = "noaa_updates/noaa_commands.py"
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"[OK] Arquivo criado: {caminho}")
    return True

def criar_noaa_panel():
    """Cria o arquivo noaa_panel.py para interface"""
    
    conteudo = '''#!/usr/bin/env python3
"""
NOAA Panel - Painel principal NOAA para interface Sci-Fi
"""

import customtkinter as ctk
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
import json

class NOAAPanel(ctk.CTkFrame):
    """Painel principal NOAA para interface HUD"""
    
    def __init__(self, parent, noaa_service=None):
        super().__init__(parent)
        
        self.noaa_service = noaa_service
        self.parent = parent
        
        # Cores do tema Sci-Fi
        self.theme = {
            "bg": "#0a0a12",
            "bg_dark": "#05050a",
            "primary": "#00ffff",
            "secondary": "#0099ff",
            "accent": "#ff00ff",
            "success": "#00ff88",
            "warning": "#ffaa00",
            "danger": "#ff0066",
            "text": "#ffffff",
            "text_dim": "#8888aa",
            "border": "#444466"
        }
        
        self.configure(
            fg_color=self.theme["bg"],
            corner_radius=10,
            border_width=1,
            border_color=self.theme["border"]
        )
        
        # Dados atuais
        self.current_data = None
        self.update_interval = 30000  # 30 segundos
        
        # Criar interface
        self._create_widgets()
        
        # Iniciar com dados iniciais
        self._load_initial_data()
    
    def _create_widgets(self):
        """Cria todos os widgets do painel"""
        
        # Frame de cabeçalho
        header_frame = ctk.CTkFrame(self, fg_color=self.theme["bg_dark"], height=40)
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        header_frame.pack_propagate(False)
        
        # Título
        title = ctk.CTkLabel(
            header_frame,
            text="🌌 NOAA SPACE WEATHER",
            font=("Courier", 16, "bold"),
            text_color=self.theme["primary"]
        )
        title.pack(side="left", padx=10, pady=5)
        
        # Status indicator
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="●",
            font=("Arial", 20),
            text_color=self.theme["success"]
        )
        self.status_indicator.pack(side="right", padx=10, pady=5)
        
        # Frame principal com grid
        main_frame = ctk.CTkFrame(self, fg_color=self.theme["bg"])
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Grid 2x2 para widgets
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Widget 1: Kp Index Gauge
        self.kp_frame = self._create_kp_gauge(main_frame)
        self.kp_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Widget 2: Solar Wind
        self.wind_frame = self._create_solar_wind_gauge(main_frame)
        self.wind_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Widget 3: Alert Panel
        self.alert_frame = self._create_alert_panel(main_frame)
        self.alert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Widget 4: Aurora Forecast
        self.aurora_frame = self._create_aurora_panel(main_frame)
        self.aurora_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        # Frame de rodapé
        footer_frame = ctk.CTkFrame(self, fg_color=self.theme["bg_dark"], height=30)
        footer_frame.pack(fill="x", padx=5, pady=(0, 5))
        footer_frame.pack_propagate(False)
        
        # Timestamp
        self.timestamp_label = ctk.CTkLabel(
            footer_frame,
            text="Last update: --:--:--",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        self.timestamp_label.pack(side="left", padx=10)
        
        # Botão de atualização
        refresh_btn = ctk.CTkButton(
            footer_frame,
            text="⟳",
            width=30,
            height=20,
            command=self.refresh_data,
            fg_color=self.theme["secondary"],
            hover_color=self.theme["primary"]
        )
        refresh_btn.pack(side="right", padx=5)
    
    def _create_kp_gauge(self, parent):
        """Cria medidor de índice Kp"""
        frame = ctk.CTkFrame(parent, fg_color=self.theme["bg_dark"], corner_radius=8)
        
        # Título
        title = ctk.CTkLabel(
            frame,
            text="KP INDEX",
            font=("Courier", 12, "bold"),
            text_color=self.theme["text"]
        )
        title.pack(pady=(10, 5))
        
        # Valor do Kp
        self.kp_value_label = ctk.CTkLabel(
            frame,
            text="--",
            font=("Digital-7", 48, "bold"),
            text_color=self.theme["primary"]
        )
        self.kp_value_label.pack()
        
        # Nível
        self.kp_level_label = ctk.CTkLabel(
            frame,
            text="QUIET",
            font=("Courier", 10),
            text_color=self.theme["success"]
        )
        self.kp_level_label.pack()
        
        # Barra de progresso
        self.kp_progress = ctk.CTkProgressBar(frame, width=150, height=10)
        self.kp_progress.pack(pady=10)
        self.kp_progress.set(0.2)
        
        # Escala
        scale_frame = ctk.CTkFrame(frame, fg_color="transparent")
        scale_frame.pack(pady=(0, 10))
        
        for i in range(0, 10, 2):
            label = ctk.CTkLabel(
                scale_frame,
                text=str(i),
                font=("Courier", 8),
                text_color=self.theme["text_dim"]
            )
            label.pack(side="left", padx=14)
        
        return frame
    
    def _create_solar_wind_gauge(self, parent):
        """Cria medidor de vento solar"""
        frame = ctk.CTkFrame(parent, fg_color=self.theme["bg_dark"], corner_radius=8)
        
        # Título
        title = ctk.CTkLabel(
            frame,
            text="SOLAR WIND",
            font=("Courier", 12, "bold"),
            text_color=self.theme["text"]
        )
        title.pack(pady=(10, 5))
        
        # Velocidade
        speed_frame = ctk.CTkFrame(frame, fg_color="transparent")
        speed_frame.pack(pady=5)
        
        speed_label = ctk.CTkLabel(
            speed_frame,
            text="SPEED:",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        speed_label.pack(side="left", padx=(10, 5))
        
        self.wind_speed_label = ctk.CTkLabel(
            speed_frame,
            text="---",
            font=("Digital-7", 24),
            text_color=self.theme["secondary"]
        )
        self.wind_speed_label.pack(side="left")
        
        unit_label = ctk.CTkLabel(
            speed_frame,
            text="km/s",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        unit_label.pack(side="left", padx=(2, 10))
        
        # Densidade
        density_frame = ctk.CTkFrame(frame, fg_color="transparent")
        density_frame.pack(pady=5)
        
        density_label = ctk.CTkLabel(
            density_frame,
            text="DENSITY:",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        density_label.pack(side="left", padx=(10, 5))
        
        self.wind_density_label = ctk.CTkLabel(
            density_frame,
            text="---",
            font=("Digital-7", 20),
            text_color=self.theme["accent"]
        )
        self.wind_density_label.pack(side="left")
        
        unit_label2 = ctk.CTkLabel(
            density_frame,
            text="p/cm³",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        unit_label2.pack(side="left", padx=(2, 10))
        
        # Componente Bz
        bz_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bz_frame.pack(pady=10)
        
        bz_label = ctk.CTkLabel(
            bz_frame,
            text="Bz:",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        bz_label.pack(side="left", padx=(10, 5))
        
        self.bz_value_label = ctk.CTkLabel(
            bz_frame,
            text="+--.-",
            font=("Digital-7", 18),
            text_color=self.theme["text"]
        )
        self.bz_value_label.pack(side="left")
        
        unit_label3 = ctk.CTkLabel(
            bz_frame,
            text="nT",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        unit_label3.pack(side="left", padx=(2, 10))
        
        # Direção do Bz
        self.bz_direction_label = ctk.CTkLabel(
            frame,
            text="North",
            font=("Courier", 9),
            text_color=self.theme["text_dim"]
        )
        self.bz_direction_label.pack()
        
        return frame
    
    def _create_alert_panel(self, parent):
        """Cria painel de alertas"""
        frame = ctk.CTkFrame(parent, fg_color=self.theme["bg_dark"], corner_radius=8)
        
        # Título
        title = ctk.CTkLabel(
            frame,
            text="🚨 ACTIVE ALERTS",
            font=("Courier", 12, "bold"),
            text_color=self.theme["warning"]
        )
        title.pack(pady=(10, 5))
        
        # Lista de alertas
        self.alerts_text = ctk.CTkTextbox(
            frame,
            height=100,
            font=("Courier", 10),
            text_color=self.theme["text"],
            fg_color="#111122",
            border_width=0
        )
        self.alerts_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.alerts_text.insert("1.0", "No active alerts")
        self.alerts_text.configure(state="disabled")
        
        return frame
    
    def _create_aurora_panel(self, parent):
        """Cria painel de previsão de aurora"""
        frame = ctk.CTkFrame(parent, fg_color=self.theme["bg_dark"], corner_radius=8)
        
        # Título
        title = ctk.CTkLabel(
            frame,
            text="AURORA FORECAST",
            font=("Courier", 12, "bold"),
            text_color=self.theme["accent"]
        )
        title.pack(pady=(10, 5))
        
        # Probabilidade
        prob_frame = ctk.CTkFrame(frame, fg_color="transparent")
        prob_frame.pack(pady=5)
        
        prob_label = ctk.CTkLabel(
            prob_frame,
            text="Probability:",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        prob_label.pack(side="left")
        
        self.aurora_prob_label = ctk.CTkLabel(
            prob_frame,
            text="--%",
            font=("Digital-7", 24),
            text_color=self.theme["accent"]
        )
        self.aurora_prob_label.pack(side="left", padx=10)
        
        # Região
        region_frame = ctk.CTkFrame(frame, fg_color="transparent")
        region_frame.pack(pady=5)
        
        region_label = ctk.CTkLabel(
            region_frame,
            text="Best Region:",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        region_label.pack(side="left")
        
        self.aurora_region_label = ctk.CTkLabel(
            region_frame,
            text="---",
            font=("Courier", 10, "bold"),
            text_color=self.theme["text"]
        )
        self.aurora_region_label.pack(side="left", padx=10)
        
        # Visibilidade
        vis_frame = ctk.CTkFrame(frame, fg_color="transparent")
        vis_frame.pack(pady=10)
        
        vis_label = ctk.CTkLabel(
            vis_frame,
            text="Visibility:",
            font=("Courier", 10),
            text_color=self.theme["text_dim"]
        )
        vis_label.pack(side="left")
        
        self.aurora_vis_label = ctk.CTkLabel(
            vis_frame,
            text="---",
            font=("Courier", 10),
            text_color=self.theme["text"]
        )
        self.aurora_vis_label.pack(side="left", padx=10)
        
        # Mapa simples (placeholder)
        map_frame = ctk.CTkFrame(frame, fg_color="#111133", height=40)
        map_frame.pack(fill="x", padx=10, pady=(0, 10))
        map_frame.pack_propagate(False)
        
        map_label = ctk.CTkLabel(
            map_frame,
            text="[Aurora Map]",
            font=("Courier", 8),
            text_color=self.theme["text_dim"]
        )
        map_label.pack(expand=True)
        
        return frame
    
    def _load_initial_data(self):
        """Carrega dados iniciais"""
        self.current_data = {
            "kp_index": 2.3,
            "solar_wind": {
                "speed": 420,
                "density": 8.5,
                "bz": -2.3
            },
            "alerts": [],
            "aurora": {
                "probability": 65,
                "region": "Scandinavia",
                "visibility": "Good"
            }
        }
        
        self._update_display()
    
    def _update_display(self):
        """Atualiza a exibição com dados atuais"""
        if not self.current_data:
            return
        
        # Atualizar Kp
        kp = self.current_data.get("kp_index", 0)
        self.kp_value_label.configure(text=f"{kp:.1f}")
        self.kp_progress.set(kp / 9.0)  # Normalizar para 0-1
        
        # Determinar nível do Kp
        if kp >= 6:
            level = "STORM"
            color = self.theme["danger"]
        elif kp >= 4:
            level = "ACTIVE"
            color = self.theme["warning"]
        elif kp >= 2:
            level = "UNSETTLED"
            color = self.theme["success"]
        else:
            level = "QUIET"
            color = self.theme["text_dim"]
        
        self.kp_level_label.configure(text=level, text_color=color)
        
        # Atualizar vento solar
        wind = self.current_data.get("solar_wind", {})
        self.wind_speed_label.configure(text=f"{wind.get('speed', 0):.0f}")
        self.wind_density_label.configure(text=f"{wind.get('density', 0):.1f}")
        
        # Atualizar Bz
        bz = wind.get('bz', 0)
        self.bz_value_label.configure(text=f"{bz:+.1f}")
        
        # Cor do Bz baseada na direção
        if bz < -5:
            direction = "SOUTH"
            color = self.theme["danger"]
        elif bz > 5:
            direction = "NORTH"
            color = self.theme["success"]
        else:
            direction = "NEUTRAL"
            color = self.theme["text_dim"]
        
        self.bz_direction_label.configure(text=direction, text_color=color)
        
        # Atualizar alertas
        alerts = self.current_data.get("alerts", [])
        self.alerts_text.configure(state="normal")
        self.alerts_text.delete("1.0", "end")
        
        if alerts:
            for alert in alerts[:3]:  # Mostrar até 3 alertas
                self.alerts_text.insert("end", f"• {alert}\\n")
        else:
            self.alerts_text.insert("end", "No active alerts")
        
        self.alerts_text.configure(state="disabled")
        
        # Atualizar aurora
        aurora = self.current_data.get("aurora", {})
        self.aurora_prob_label.configure(text=f"{aurora.get('probability', 0)}%")
        self.aurora_region_label.configure(text=aurora.get('region', '--'))
        self.aurora_vis_label.configure(text=aurora.get('visibility', '--'))
        
        # Atualizar timestamp
        current_time = datetime.now().strftime("%H:%M:%S")
        self.timestamp_label.configure(text=f"Last update: {current_time}")
        
        # Atualizar status indicator
        if alerts:
            self.status_indicator.configure(text_color=self.theme["warning"])
        else:
            self.status_indicator.configure(text_color=self.theme["success"])
    
    def refresh_data(self):
        """Atualiza dados manualmente"""
        # Simular novos dados
        import random
        
        if self.current_data:
            # Atualizar Kp (ligeira variação)
            current_kp = self.current_data["kp_index"]
            new_kp = current_kp + random.uniform(-0.5, 0.5)
            new_kp = max(0, min(9, new_kp))  # Limitar entre 0-9
            self.current_data["kp_index"] = new_kp
            
            # Atualizar vento solar
            wind = self.current_data["solar_wind"]
            wind["speed"] += random.uniform(-20, 20)
            wind["speed"] = max(200, min(800, wind["speed"]))
            wind["bz"] += random.uniform(-1, 1)
            wind["bz"] = max(-15, min(15, wind["bz"]))
            
            # Atualizar timestamp
            self.current_data["timestamp"] = datetime.now().isoformat()
        
        self._update_display()
    
    def update_from_service(self, noaa_data):
        """Atualiza dados a partir do serviço NOAA"""
        if noaa_data:
            self.current_data = noaa_data
            self._update_display()
    
    def get_panel_info(self):
        """Retorna informações do painel para integração"""
        return {
            "name": "NOAA Space Weather",
            "version": "2.1.0",
            "description": "Monitoramento de clima espacial em tempo real",
            "data_source": "NOAA/SWPC",
            "last_update": datetime.now().isoformat()
        }

# Teste do painel
def test_panel():
    """Testa o painel NOAA"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("NOAA Panel Test")
    root.geometry("800x600")
    
    panel = NOAAPanel(root)
    panel.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Botão de teste
    test_btn = ctk.CTkButton(
        root,
        text="Test Refresh",
        command=panel.refresh_data
    )
    test_btn.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_panel()
'''
    
    caminho = "noaa_updates/noaa_panel.py"
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"[OK] Arquivo criado: {caminho}")
    return True

def criar_arquivos_core():
    """Cria os arquivos de core atualizados"""
    
    # 1. config.py
    conteudo_config = '''"""
Configurações do sistema R2 Assistant - Atualizado para NOAA
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Gerenciador de configurações"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config_path = Path("config.json")
        self.default_config = self._get_default_config()
        self.config = self._load_config()
        
        # Configurações NOAA
        self.noaa_config = {
            "ENABLE_NOAA": True,
            "ENABLE_SOLAR_MONITOR": True,
            "NOAA_UPDATE_INTERVAL": 300,  # 5 minutos
            "NOAA_ALERT_ENABLED": True,
            "NOAA_AUTO_REPORTS": False,
            "NOAA_DATA_RETENTION_DAYS": 7,
            "NOAA_API_ENDPOINTS": {
                "SOLAR_WIND": "https://services.swpc.noaa.gov/json/ace/swepam.json",
                "GEOMAGNETIC_INDICES": "https://services.swpc.noaa.gov/json/goes/primary/xray-flares.json",
                "SOLAR_FLARES": "https://services.swpc.noaa.gov/json/goes/primary/xray-flares.json"
            },
            "NOAA_ALERT_THRESHOLDS": {
                "SOLAR_FLARE": ["M", "X", "X+"],
                "KP_INDEX": 6.0,
                "SOLAR_WIND_SPEED": 600
            }
        }
        
        # Mesclar configurações NOAA
        self.config.update(self.noaa_config)
        
        self._initialized = True
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        return {
            "VERSION": "2.1.0",
            "APP_NAME": "R2 Assistant",
            "THEME": "sci_fi",
            "LANGUAGE": "pt-BR",
            "VOICE_ENABLED": True,
            "AUTO_START": False,
            "LOG_LEVEL": "INFO",
            "ENABLE_NOAA": True,
            "ENABLE_SOLAR_MONITOR": True,
            "NOAA_UPDATE_INTERVAL": 300
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar config: {e}")
                return self.default_config.copy()
        else:
            # Criar arquivo de configuração
            self._save_config(self.default_config)
            return self.default_config.copy()
    
    def _save_config(self, config: Dict[str, Any]):
        """Salva configuração no arquivo"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
    
    def get(self, key: str, default=None):
        """Obtém valor de configuração"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Define valor de configuração"""
        self.config[key] = value
        self._save_config(self.config)
    
    def get_noaa_config(self) -> Dict[str, Any]:
        """Retorna configurações NOAA"""
        return {
            k: v for k, v in self.config.items() 
            if k.startswith("NOAA_") or k in ["ENABLE_NOAA", "ENABLE_SOLAR_MONITOR"]
        }
    
    def update_noaa_config(self, updates: Dict[str, Any]):
        """Atualiza configurações NOAA"""
        for key, value in updates.items():
            self.config[key] = value
        self._save_config(self.config)

# Instância global
config = Config()
'''
    
    caminho = "noaa_updates/config.py"
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo_config)
    
    print(f"[OK] Arquivo criado: {caminho}")
    
    # 2. command_system.py (versão simplificada)
    conteudo_command = '''"""
Sistema de Comandos - Atualizado para NOAA
"""

import asyncio
import importlib.util
from typing import Dict, List, Any, Optional, Callable

class CommandSystem:
    """Sistema de gerenciamento de comandos"""
    
    def __init__(self):
        self.commands: Dict[str, Dict] = {}
        self.categories = {
            "system": "Comandos do Sistema",
            "noaa": "Clima Espacial NOAA",
            "media": "Mídia e Entretenimento",
            "tools": "Ferramentas",
            "ai": "Inteligência Artificial"
        }
        
        self._register_builtin_commands()
    
    def _register_builtin_commands(self):
        """Registra comandos embutidos"""
        
        # Comandos de sistema
        self.register_command(
            name="ajuda",
            func=self.cmd_help,
            category="system",
            description="Mostra esta ajuda",
            aliases=["help", "comandos", "?"]
        )
        
        self.register_command(
            name="sair",
            func=self.cmd_exit,
            category="system",
            description="Fecha o R2 Assistant",
            aliases=["exit", "quit", "fechar"]
        )
        
        # Comandos NOAA (serão carregados do módulo NOAA)
        self.register_command(
            name="clima espacial",
            func=None,  # Será substituído pelo módulo NOAA
            category="noaa",
            description="Relatório completo de clima espacial",
            aliases=["climaespacial", "space weather", "weather space"]
        )
    
    def register_command(self, name: str, func: Callable, category: str, 
                         description: str = "", aliases: List[str] = None):
        """Registra um novo comando"""
        
        command_data = {
            "func": func,
            "category": category,
            "description": description,
            "aliases": aliases or []
        }
        
        self.commands[name.lower()] = command_data
        
        # Registrar aliases
        if aliases:
            for alias in aliases:
                self.commands[alias.lower()] = command_data
    
    async def execute(self, command_text: str, args: List[str] = None) -> Dict[str, Any]:
        """Executa um comando"""
        
        if args is None:
            args = []
        
        command_lower = command_text.lower().strip()
        
        if command_lower not in self.commands:
            # Tentar encontrar comando similar
            suggestions = self._suggest_command(command_lower)
            return {
                "success": False,
                "message": f"Comando não encontrado: {command_text}",
                "suggestions": suggestions
            }
        
        command_data = self.commands[command_lower]
        
        if command_data["func"] is None:
            return {
                "success": False,
                "message": f"Comando '{command_text}' não implementado"
            }
        
        try:
            # Executar comando
            result = await command_data["func"](args)
            result["command"] = command_text
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao executar comando: {str(e)}",
                "command": command_text
            }
    
    def _suggest_command(self, command: str) -> List[str]:
        """Sugere comandos similares"""
        suggestions = []
        for cmd in self.commands.keys():
            if command in cmd or cmd in command:
                suggestions.append(cmd)
        
        return suggestions[:5]  # Limitar a 5 sugestões
    
    def get_commands_by_category(self, category: str = None) -> Dict[str, Dict]:
        """Retorna comandos por categoria"""
        if category:
            return {k: v for k, v in self.commands.items() if v.get("category") == category}
        return self.commands
    
    def load_noaa_commands(self, noaa_module):
        """Carrega comandos do módulo NOAA"""
        try:
            # Obter comandos do módulo NOAA
            noaa_commands = getattr(noaa_module, "NOAACommands", None)
            if noaa_commands:
                noaa_instance = noaa_commands(None)  # Service será injetado depois
                
                for cmd_name, cmd_data in noaa_instance.commands.items():
                    self.register_command(
                        name=cmd_name,
                        func=cmd_data["func"],
                        category="noaa",
                        description=cmd_data["description"],
                        aliases=cmd_data.get("aliases", [])
                    )
                
                print(f"[OK] {len(noaa_instance.commands)} comandos NOAA carregados")
                return True
        except Exception as e:
            print(f"[ERRO] Falha ao carregar comandos NOAA: {e}")
        
        return False
    
    async def cmd_help(self, args: List[str] = None) -> Dict[str, Any]:
        """Comando de ajuda"""
        
        category = args[0] if args else None
        
        if category and category in self.categories:
            commands = self.get_commands_by_category(category)
            category_name = self.categories[category]
        else:
            commands = self.commands
            category_name = "Todos"
        
        # Formatar ajuda
        help_text = f"=== R2 Assistant - Comandos ({category_name}) ===\\n"
        
        # Agrupar por categoria
        by_category = {}
        for cmd_name, cmd_data in commands.items():
            cat = cmd_data.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            
            # Evitar duplicados (aliases)
            if cmd_name == list(self.commands.keys())[list(self.commands.values()).index(cmd_data)]:
                desc = cmd_data.get("description", "Sem descrição")
                aliases = cmd_data.get("aliases", [])
                alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
                by_category[cat].append(f"  {cmd_name:20} - {desc}{alias_text}")
        
        # Adicionar comandos por categoria
        for cat, cmd_list in by_category.items():
            if cmd_list:
                cat_name = self.categories.get(cat, cat.title())
                help_text += f"\\n{cat_name}:\\n"
                help_text += "\\n".join(cmd_list)
        
        help_text += "\\n\\nUse 'ajuda [categoria]' para ver comandos de uma categoria específica."
        
        return {
            "success": True,
            "message": help_text,
            "voice_response": "Lista de comandos disponível no painel."
        }
    
    async def cmd_exit(self, args: List[str] = None) -> Dict[str, Any]:
        """Comando de saída"""
        return {
            "success": True,
            "message": "Encerrando R2 Assistant...",
            "voice_response": "Até logo!",
            "action": "exit"
        }

# Instância global do sistema de comandos
command_system = CommandSystem()
'''
    
    caminho = "noaa_updates/command_system.py"
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo_command)
    
    print(f"[OK] Arquivo criado: {caminho}")
    
    return True

def criar_arquivos_restantes():
    """Cria os arquivos restantes necessários"""
    
    arquivos = [
        ("requirements_noaa.txt", """# Dependências para módulo NOAA
aiohttp>=3.8.0
matplotlib>=3.5.0
numpy>=1.21.0
requests>=2.28.0
psutil>=5.9.0
scipy>=1.9.0
customtkinter>=5.2.0
Pillow>=9.0.0
python-dateutil>=2.8.2
"""),
        
        ("test_noaa.py", '''#!/usr/bin/env python3
"""
Teste do módulo NOAA
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_noaa_service():
    """Testa o serviço NOAA"""
    print("=== Teste NOAA Service ===")
    
    try:
        from features.noaa.noaa_service import get_noaa_service
        
        service = get_noaa_service()
        print("[OK] NOAA Service importado")
        
        # Teste básico
        print("Configuração carregada:", service.config is not None)
        print("Endpoints configurados:", len(service.endpoints))
        
        return True
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_noaa_commands():
    """Testa comandos NOAA"""
    print("\\n=== Teste NOAA Commands ===")
    
    try:
        from commands.noaa_commands import NOAACommands
        
        commands = NOAACommands(None)
        print(f"[OK] {len(commands.commands)} comandos NOAA carregados")
        
        # Listar comandos
        print("Comandos disponíveis:")
        for cmd_name, cmd_data in commands.commands.items():
            print(f"  - {cmd_name}: {cmd_data['description']}")
        
        return True
    except Exception as e:
        print(f"[ERRO] {e}")
        return False

def test_noaa_panel():
    """Testa painel NOAA"""
    print("\\n=== Teste NOAA Panel ===")
    
    try:
        from gui.components.noaa_panel import NOAAPanel
        print("[OK] NOAA Panel importado")
        
        # Verificar se pode criar instância
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        
        root = ctk.CTk()
        root.withdraw()  # Não mostrar janela
        
        panel = NOAAPanel(root)
        print("[OK] Painel NOAA criado com sucesso")
        
        info = panel.get_panel_info()
        print(f"Info: {info}")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"[ERRO] {e}")
        return False

async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do módulo NOAA...")
    
    results = []
    
    # Testar serviço
    results.append(await test_noaa_service())
    
    # Testar comandos
    results.append(test_noaa_commands())
    
    # Testar painel
    results.append(test_noaa_panel())
    
    # Resumo
    print("\\n=== RESUMO DOS TESTES ===")
    for i, (test_name, result) in enumerate([
        ("NOAA Service", results[0]),
        ("NOAA Commands", results[1]),
        ("NOAA Panel", results[2])
    ]):
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:20} {status}")
    
    if all(results):
        print("\\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("\\n⚠️  ALGUNS TESTES FALHARAM")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
'''),
        
        ("README_NOAA.md", """# Módulo NOAA - R2 Assistant

Módulo de monitoramento de clima espacial para R2 Assistant v2.1.0.

## 🚀 Funcionalidades

- **Monitoramento em tempo real** de dados solares e geomagnéticos
- **Sistema de alertas** para eventos significativos
- **Interface Sci-Fi** integrada ao HUD principal
- **Comandos de voz/texto** para acesso rápido aos dados
- **Análise histórica** e relatórios automáticos

## 📊 Fontes de Dados

- NOAA Space Weather Prediction Center (SWPC)
- Dados do vento solar (DSCOVR, ACE)
- Índices geomagnéticos (Kp, Dst)
- Flares solares (GOES X-ray)
- Previsão de aurora

## 🎨 Interface

Tema visual Sci-Fi Militar com cores neon:
- Background: `#0a0a12` (Preto Espacial)
- Primary: `#00ffff` (Ciano Neon)
- Secondary: `#0099ff` (Azul Elétrico)
- Texto: `#ffffff` (Branco Puro)

## 🗣️ Comandos Principais

### Comandos de Voz:
- **"clima espacial"** - Relatório completo NOAA
- **"vento solar"** - Dados do vento solar em tempo real
- **"alerta solar"** - Verificar alertas ativos
- **"tempestade geomagnética"** - Status de tempestades
- **"aurora boreal"** - Previsão de aurora

### Comandos de Texto:
- **`/noaa`** - Menu interativo NOAA
- **`/noaa alertas`** - Listar alertas ativos
- **`/noaa vento`** - Histórico vento solar
- **`/noaa kp`** - Gráfico índice Kp (24h)

## ⚙️ Instalação

1. Execute o instalador:
   ```bash
   python install_noaa_updates_fixed.py