#!/usr/bin/env python3
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
