import os
import requests
import matplotlib
# FORÇA O MODO SEM INTERFACE (Essencial para não travar com a GUI do R2)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
import time

class RadarAereoAPI:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="r2_tatico_v3")
        self.api_url = "https://opensky-network.org/api/states/all"

    def gerar_radar(self, cidade_nome):
        try:
            # 1. GPS
            location = self.geolocator.geocode(cidade_nome)
            if not location:
                return f"⚠️ Localização '{cidade_nome}' inválida.", None
            
            lat, lon = location.latitude, location.longitude
            delta = 1.8 # Raio de 200km

            # 2. API OpenSky
            params = {"lamin": lat-delta, "lamax": lat+delta, "lomin": lon-delta, "lomax": lon+delta}
            response = requests.get(self.api_url, params=params, timeout=15)
            data = response.json()
            states = data.get("states") or []

            # 3. Desenho do Gráfico (Modo Agg)
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(7, 7))
            
            # Círculos táticos
            for r in [0.45, 0.9, 1.35, 1.8]:
                circle = plt.Circle((lon, lat), r, color='#00ff00', fill=False, alpha=0.2, linestyle='--')
                ax.add_patch(circle)

            # Plota Aeronaves
            if states:
                lons = [s[5] for s in states if s[5]]
                lats = [s[6] for s in states if s[6]]
                ax.scatter(lons, lats, color='#00ff00', marker='+', s=80)
                for s in states:
                    if s[5] and s[6]:
                        ax.annotate(s[1].strip() or "UNK", (s[5], s[6]), color='#00ff00', fontsize=7, xytext=(3,3), textcoords='offset points')

            # Centro (Base)
            ax.plot(lon, lat, 'ro', markersize=8)
            ax.set_title(f"RADAR: {cidade_nome.upper()}\nALVOS DETECTADOS: {len(states)}", color='#00ff00')
            ax.set_facecolor('black')
            
            # Força o caminho absoluto na raiz do projeto
            path = os.path.abspath("radar_final.png")
            
            # Limpeza de segurança: remove o antigo antes de salvar o novo
            if os.path.exists(path):
                try: os.remove(path)
                except: pass

            plt.savefig(path, facecolor='black', dpi=120)
            plt.close(fig) # Fecha a figura para liberar memória
            
            return f"✅ Varredura concluída. {len(states)} aeronaves detectadas.", path

        except Exception as e:
            return f"❌ Erro API/Gráfico: {str(e)}", None