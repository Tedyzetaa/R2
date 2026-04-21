import requests
import matplotlib
matplotlib.use('Agg') # Força o modo sem janela (Thread-safe)
import matplotlib.pyplot as plt
import io
import os

class AirTrafficControl:
    def __init__(self):
        # Coordenadas de IVINHEMA
        self.home_lat = -22.3044
        self.home_lon = -53.8197
        self.radius_deg = 1.0 

    def radar_scan(self, location_name="Ivinhema"):
        # Lógica de Geocoding simples
        lat = self.home_lat
        lon = self.home_lon
        
        if location_name.lower() != "ivinhema":
            try:
                # Busca coordenadas via Nominatim (OpenStreetMap)
                url_geo = "https://nominatim.openstreetmap.org/search"
                params = {'q': location_name, 'format': 'json', 'limit': 1}
                headers = {'User-Agent': 'R2Assistant/2.0'}
                resp = requests.get(url_geo, params=params, headers=headers, timeout=5)
                if resp.status_code == 200 and resp.json():
                    data = resp.json()[0]
                    lat = float(data['lat'])
                    lon = float(data['lon'])
            except Exception as e:
                print(f"Erro no geocoding: {e}")

        # Define a caixa de busca
        lamin = lat - self.radius_deg
        lamax = lat + self.radius_deg
        lomin = lon - self.radius_deg
        lomax = lon + self.radius_deg

        url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

        try:
            print(f"📡 [RADAR]: Escaneando setor: {location_name.upper()}...")
            headers = {'User-Agent': 'R2Assistant/2.0'}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            states = data.get('states', [])
            
            # --- GERAÇÃO DA IMAGEM ---
            filename = "radar_scan.png"
            self._plotar_radar(states, filename, lat, lon, location_name)
            
            qtd = len(states) if states else 0
            
            return filename, qtd, f"📡 Radar Tático (Setor {location_name.upper()}): {qtd} alvos detectados."

        except Exception as e:
            print(f"Erro no radar: {e}")
            return None, 0, f"Falha no sistema de radar: {e}"

    def _plotar_radar(self, aircrafts, filename, center_lat, center_lon, location_name):
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Legenda do ponto central dinâmico
        ax.plot(center_lon, center_lat, marker='P', color='#00ffff', markersize=15, label=f'BASE ({location_name.upper()})')
        
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
        circle1 = plt.Circle((center_lon, center_lat), 0.3, color='#00ff00', fill=False, linestyle='--', alpha=0.5)
        circle2 = plt.Circle((center_lon, center_lat), 0.6, color='#00ff00', fill=False, linestyle='--', alpha=0.3)
        ax.add_patch(circle1)
        ax.add_patch(circle2)

        # Título do Gráfico
        ax.set_title(f"R2 TACTICAL RADAR - SECTOR {location_name.upper()}", color='#00ff00', fontsize=14)
        ax.set_xlabel("LONGITUDE")
        ax.set_ylabel("LATITUDE")
        ax.grid(True, color='#003300', linestyle='-')
        ax.legend(loc='upper right')
        
        plt.savefig(filename, facecolor='black')
        plt.close()