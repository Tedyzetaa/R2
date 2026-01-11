import requests
import matplotlib.pyplot as plt
import io
import os

class AirTrafficControl:
    def __init__(self):
        # Coordenadas de IVINHEMA
        self.home_lat = -22.3044
        self.home_lon = -53.8197
        self.radius_deg = 1.0 

    def radar_scan(self):
        # Define a caixa de busca
        lamin = self.home_lat - self.radius_deg
        lamax = self.home_lat + self.radius_deg
        lomin = self.home_lon - self.radius_deg
        lomax = self.home_lon + self.radius_deg

        url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

        try:
            print(f"📡 [RADAR]: Escaneando setor Ivinhema...")
            headers = {'User-Agent': 'R2Assistant/2.0'}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            states = data.get('states', [])
            
            # --- GERAÇÃO DA IMAGEM ---
            filename = "radar_scan.png"
            self._plotar_radar(states, filename)
            
            qtd = len(states) if states else 0
            
            # CORREÇÃO AQUI: Texto de retorno ajustado para Ivinhema
            return filename, qtd, f"📡 Radar Tático (Setor Ivinhema): {qtd} alvos detectados."

        except Exception as e:
            print(f"Erro no radar: {e}")
            return None, 0, f"Falha no sistema de radar: {e}"

    def _plotar_radar(self, aircrafts, filename):
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # CORREÇÃO AQUI: Legenda do ponto central
        ax.plot(self.home_lon, self.home_lat, marker='P', color='#00ffff', markersize=15, label='BASE (IVINHEMA)')
        
        if aircrafts:
            for plane in aircrafts:
                lon = plane[5]
                lat = plane[6]
                callsign = plane[1].strip()
                origin = plane[2]
                
                if lat is None or lon is None: continue

                ax.plot(lon, lat, marker='^', color='#ff0000', markersize=10)
                label = f"{callsign}\n({origin})"
                ax.text(lon, lat, label, fontsize=8, color='#ffff00', ha='right')

        # Círculos de Distância
        circle1 = plt.Circle((self.home_lon, self.home_lat), 0.3, color='#00ff00', fill=False, linestyle='--', alpha=0.5)
        circle2 = plt.Circle((self.home_lon, self.home_lat), 0.6, color='#00ff00', fill=False, linestyle='--', alpha=0.3)
        ax.add_patch(circle1)
        ax.add_patch(circle2)

        # CORREÇÃO AQUI: Título do Gráfico
        ax.set_title(f"R2 TACTICAL RADAR - SECTOR IVINHEMA", color='#00ff00', fontsize=14)
        ax.set_xlabel("LONGITUDE")
        ax.set_ylabel("LATITUDE")
        ax.grid(True, color='#003300', linestyle='-')
        ax.legend(loc='upper right')
        
        plt.savefig(filename, facecolor='black')
        plt.close()