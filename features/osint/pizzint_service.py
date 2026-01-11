import requests
import numpy as np
from collections import deque
from datetime import datetime
import threading
import time
import random  # Fallback para simulação se o site estiver offline/bloqueado

class PizzaINTService:
    def __init__(self, config):
        self.config = config
        self.url = "https://www.pizzint.watch/api/current" # URL hipotética, ajustaremos no scraping
        self.history = deque(maxlen=50)  # Janela de dados para média móvel
        self.threshold = 2.0  # Desvios padrão para considerar anomalia (Sigma)
        self.current_level = 0
        self.is_monitoring = False
        self._lock = threading.Lock()

    def start(self):
        self.is_monitoring = True
        # Em produção, usaríamos requests reais.
        # Como o site pode ter proteção Cloudflare, começamos com uma simulação baseada em Random Walk
        # para garantir que seu HUD funcione imediatamente.
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def stop(self):
        self.is_monitoring = False

    def _monitor_loop(self):
        while self.is_monitoring:
            try:
                # 1. Coleta de Dados (Simulação robusta para dev / Scraper real entraria aqui)
                # Tentaríamos: response = requests.get(self.url)
                
                # Simula flutuação normal entre 30-50 pedidos/hora
                noise = np.random.normal(0, 5)
                base_activity = 40 
                
                # Ocasionalmente gera um pico (Crise Geopolítica Simulada)
                if random.random() < 0.05: 
                    noise += 40  # Pico repentino
                
                new_value = max(0, base_activity + noise)
                
                with self._lock:
                    self.current_level = new_value
                    self.history.append(new_value)

                time.sleep(5)  # Atualiza a cada 5 segundos

            except Exception as e:
                print(f"⚠️ PizzaINT Error: {e}")
                time.sleep(10)

    def check_anomaly(self) -> tuple[bool, str]:
        """
        Retorna (is_anomaly, message) baseado em análise estatística (Z-Score).
        """
        with self._lock:
            if len(self.history) < 10:
                return False, ""

            data = np.array(self.history)
            mean = np.mean(data)
            std = np.std(data)

            if std == 0:
                return False, ""

            # Cálculo do Z-Score
            z_score = (self.current_level - mean) / std

            if z_score > self.threshold:
                severity = "ALTO" if z_score > 3 else "MODERADO"
                return True, f"Fluxo de Pizza {self.current_level:.0f} (Z: {z_score:.2f}). Desvio {severity} detectado!"
            
            return False, ""

    def get_status(self):
        with self._lock:
            return {
                "level": self.current_level,
                "history": list(self.history)
            }