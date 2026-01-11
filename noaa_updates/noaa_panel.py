#!/usr/bin/env python3
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
                self.alerts_text.insert("end", f"• {alert}\n")
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
