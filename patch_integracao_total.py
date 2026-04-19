# filename: patch_integracao_total.py
import os
import re

FILE_PATH = "main2.py"

def apply_total_integration():
    print("🛰️ [SISTEMA]: Iniciando Integração de Grande Escala do Ghost Protocol...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. INJEÇÃO DE IMPORTS (No topo do arquivo)
    new_imports = """
# ── MODULOS TÁTICOS INTEGRADOS ────────────────────────
from features.sentinel_system import SentinelSystem
from features.network_scanner import NetworkScanner
from features.news_briefing import NewsBriefing
from features.noaa_service import NOAAService
from features.orbital_system import OrbitalSystem
from features.orbital_trajectory import OrbitalTrajectorySystem
from features.pizzint_service import PizzaINTService
from features.radio_scanner import RadioScanner
from features.geo_seismic import GeoSeismicSystem
from features.geopolitics import GeopoliticsManager
from features.image_gen import ImageGenerator
from features.intel_war import IntelWar
from features.liveuamap_intel import FrontlineIntel
from features.market_system import MarketSystem
from features.net_speed import NetSpeedModule
from features.volcano_monitor import VolcanoMonitor
from features.weather_system import WeatherSystem
from features.astro_timelapse import AstroTimelapseSystem
"""
    if "from features.sentinel_system" not in content:
        content = re.sub(r"(import .*?\n)", r"\1" + new_imports, content, count=1)

    # 2. INICIALIZAÇÃO DE MOTORES (Antes do setup do FastAPI)
    init_engines = """
# ── INSTANCIAÇÃO DE MOTORES TÁTICOS ──────────────────
sentinel = SentinelSystem()
net_scan = NetworkScanner()
news_svc = NewsBriefing()
noaa_svc = NOAAService()
iss_track = OrbitalSystem()
astro_vis = OrbitalTrajectorySystem()
pizzint = PizzaINTService()
radio_scan = RadioScanner()
seismic = GeoSeismicSystem()
geopol_svc = GeopoliticsManager()
# img_gen = ImageGenerator() # Desativado por padrão para economizar VRAM
intel_war = IntelWar()
war_map = FrontlineIntel()
market_svc = MarketSystem()
speed_test = NetSpeedModule()
volcano_svc = VolcanoMonitor()
# weather_svc = WeatherSystem(api_key="SUA_CHAVE_AQUI")
astro_cine = AstroTimelapseSystem()
"""
    if "sentinel = SentinelSystem()" not in content:
        content = content.replace('app = FastAPI(title="R2 TACTICAL OS")', init_engines + '\napp = FastAPI(title="R2 TACTICAL OS")')

    # 3. NOVAS ROTAS DE API (Endpoints para o menu lateral)
    new_routes = """
@app.get("/api/sentinel")
async def run_sentinel():
    path, msg = sentinel.capturar_intruso()
    return {"ok": True, "text": msg, "url": f"/static/media/{os.path.basename(path)}" if path else None}

@app.get("/api/net_scan")
async def run_net_scan():
    return {"ok": True, "text": net_scan.scan()}

@app.get("/api/market")
async def run_market():
    return {"ok": True, "text": market_svc.obter_cotacoes()}

@app.get("/api/geo_seismic")
async def run_seismic():
    return {"ok": True, "text": seismic.get_seismic_data_text()}

@app.get("/api/orbital")
async def run_orbital():
    path, msg = iss_track.rastrear_iss()
    return {"ok": True, "text": msg, "url": f"/static/media/{os.path.basename(path)}" if path else None}

@app.get("/api/defcon")
async def run_defcon():
    status = pizzint.get_status()
    return {"ok": True, "text": "Relatório DEFCON Atualizado.", "html": pizzint.generate_report_html(status)}
"""
    if "/api/sentinel" not in content:
        content = content.replace('@app.post("/api/stop")', new_routes + '\n@app.post("/api/stop")')

    # 4. MENU LATERAL (HTML) - Adicionando botões táticos
    new_buttons = """
        <div class="sidebar-section">VIGILÂNCIA</div>
        <div class="menu-item" onclick="triggerAction('/api/sentinel')">👁️ SENTINELA (CÂMERA)</div>
        <div class="menu-item" onclick="triggerAction('/api/net_scan')">📶 SCANNER DE REDE</div>
        
        <div class="sidebar-section">INTEL GLOBAL</div>
        <div class="menu-item" onclick="triggerAction('/api/defcon')">🍕 RADAR GEOPOLÍTICO</div>
        <div class="menu-item" onclick="triggerAction('/api/market')">💰 MARKET INTEL</div>
        
        <div class="sidebar-section">SENSORES TERRESTRES</div>
        <div class="menu-item" onclick="triggerAction('/api/geo_seismic')">🌋 MONITOR SÍSMICO</div>
        <div class="menu-item" onclick="triggerAction('/api/orbital')">🛰️ TELEMETRIA ISS</div>
"""
    content = content.replace('<div class="sidebar-section">CONTEÚDO</div>', new_buttons + '\n        <div class="sidebar-section">CONTEÚDO</div>')

    # 5. JAVASCRIPT: Lógica para disparar ações do menu e exibir no chat
    js_action = """
function triggerAction(endpoint) {
  showToast('Disparando Protocolo...');
  closeSidebar();
  fetch(endpoint)
    .then(res => res.json())
    .then(data => {
      if(data.ok) {
        if(data.url) {
          appendMsg('bot', 'SISTEMA', '<img src="'+data.url+'" style="max-width:100%; border-radius:8px;"><br>'+data.text);
        } else if(data.html) {
          appendMsg('bot', 'SISTEMA', data.html);
        } else {
          appendMsg('bot', 'SISTEMA', data.text);
        }
      }
    });
}
"""
    if "function triggerAction" not in content:
        content = content.replace('function toggleSidebar() {', js_action + '\nfunction toggleSidebar() {')

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ [MISSÃO CUMPRIDA]: Todos os módulos integrados e menu lateral atualizado!")
    print("🔄 Reinicie o R2 e verifique o novo painel de Vigilância e Intel.")

if __name__ == "__main__":
    apply_total_integration()