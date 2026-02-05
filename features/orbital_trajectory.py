import os
import time
import re
from playwright.sync_api import sync_playwright

class OrbitalTrajectorySystem:
    def __init__(self):
        # Fonte Visual: The Sky Live (Visual estilo Stellarium/Sci-Fi)
        self.base_url = "https://theskylive.com/3dsolarsystem?obj={}&h=00&m=00"

    def _gerar_slug_theskylive(self, nome_bruto):
        """
        Engenharia Reversa de Nomes:
        Converte '2340 Hathor (1976 UA)' -> '2340-hathor'
        Converte '(2022 SU)' -> '2022-su'
        """
        # 1. Remove parênteses e conteúdo extra se houver um nome próprio antes
        # Ex: "2340 Hathor (1976 UA)" vira "2340 Hathor"
        nome_limpo = re.sub(r'\s*\(.*?\)', '', nome_bruto).strip()
        
        # Se ficou vazio (ex: o nome era só '(2022 SU)'), recupera o conteúdo dos parênteses
        if not nome_limpo:
            match = re.search(r'\((.*?)\)', nome_bruto)
            if match:
                nome_limpo = match.group(1)
            else:
                nome_limpo = nome_bruto

        # 2. Formata para URL (minusculo e com hifens)
        # Ex: "2022 SU" -> "2022-su"
        slug = nome_limpo.lower().replace(' ', '-')
        return slug

    def get_trajectory_screenshot(self, asteroid_id, asteroid_name):
        # Gera o slug compatível com o site
        slug = self._gerar_slug_theskylive(asteroid_name)
        url = self.base_url.format(slug)
        
        pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        screenshot_path = os.path.join(pasta_raiz, "astro_orbit.png")

        if os.path.exists(screenshot_path):
            try: os.remove(screenshot_path)
            except: pass

        print(f"🌌 [VISUAL]: Acessando TheSkyLive 3D para alvo: {slug}...")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True, 
                    args=[
                        "--headless=new",
                        "--no-sandbox",
                        "--ignore-gpu-blocklist",
                        "--enable-webgl",
                        "--enable-webgl2",
                        "--high-dpi-support=1"
                    ]
                )
                
                # Resolução ajustada para pegar o Sistema Solar centralizado
                context = browser.new_context(
                    viewport={"width": 1200, "height": 1000},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # 1. Acessa o Simulador 3D
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # 2. Checagem de Erro (404 ou Objeto não encontrado)
                if "Object not found" in page.title() or "404" in page.title():
                    print(f"⚠️ Objeto '{slug}' não renderizado no TheSkyLive. Tentando fallback...")
                    # Se falhar, tenta apenas o ID (alguns objetos funcionam pelo ID)
                    url_fallback = self.base_url.format(asteroid_id)
                    page.goto(url_fallback, wait_until="domcontentloaded")

                print("🌌 [VISUAL]: Renderizando Sistema Solar (Aguarde)...")
                
                # 3. Limpeza de Interface (Remove anúncios e barras laterais para a foto ficar limpa)
                try:
                    # Injeta Javascript para sumir com menus e ads, deixando só o mapa
                    page.evaluate("""
                        var removes = ['.top-bar', '.footer', '.adsbygoogle', '.sidebar', '#pw-container'];
                        removes.forEach(s => {
                            var els = document.querySelectorAll(s);
                            els.forEach(e => e.style.display = 'none');
                        });
                    """)
                except: pass

                # Espera o motor 3D carregar os planetas e traços
                time.sleep(8)

                # 4. Zoom Out Tático (Opcional, para ver a Terra e o Asteroide)
                # Simulamos scroll do mouse para afastar a câmera se necessário
                try: page.mouse.wheel(0, 100)
                except: pass

                page.screenshot(path=screenshot_path, quality=90, type='jpeg')
                browser.close()
                
                if os.path.exists(screenshot_path):
                    print("✅ [VISUAL]: Mapa estelar gerado.")
                    return screenshot_path
                return None
                    
        except Exception as e:
            print(f"❌ Erro Visual: {e}")
            return None