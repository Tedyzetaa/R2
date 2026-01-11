import requests
import matplotlib.pyplot as plt
import io

class OrbitalSystem:
    def __init__(self):
        self.url = "http://api.open-notify.org/iss-now.json"

    def rastrear_iss(self):
        try:
            # 1. Obtém dados da NASA/OpenNotify
            response = requests.get(self.url, timeout=10)
            data = response.json()
            
            lat = float(data['iss_position']['latitude'])
            lon = float(data['iss_position']['longitude'])
            
            # 2. Gera o Mapa Orbital
            filename = "orbital_scan.png"
            self._plotar_orbita(lat, lon, filename)
            
            # 3. Verifica se está sobre o Brasil (Lat -33 a +5, Lon -74 a -34 aprox)
            sobre_brasil = (-33 <= lat <= 5) and (-74 <= lon <= -34)
            status = "⚠️ ALERTA: ISS SOBRE O BRASIL!" if sobre_brasil else "ISS em órbita padrão."
            
            return filename, f"🛰️ TELEMETRIA ORBITAL:\nLat: {lat}\nLon: {lon}\n{status}"

        except Exception as e:
            return None, f"❌ Erro no Uplink Orbital: {e}"

    def _plotar_orbita(self, lat, lon, filename):
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Plota a ISS
        ax.plot(lon, lat, marker='o', color='#00ffff', markersize=15, label='ISS')
        ax.text(lon, lat + 5, "ISS TARGET", color='#00ffff', ha='center', fontsize=9)
        
        # Configuração do Grid (Mapa Mundi Abstrato)
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.grid(True, color='#003366', linestyle='--', alpha=0.5)
        
        # Linha do Equador e Meridiano
        ax.axhline(0, color='#004488', linewidth=1)
        ax.axvline(0, color='#004488', linewidth=1)
        
        ax.set_title("R2 ORBITAL TRACKER", color='#00ffff')
        
        plt.savefig(filename, facecolor='black')
        plt.close()