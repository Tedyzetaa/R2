import os
import requests
import random
import time
from playwright.sync_api import sync_playwright

class IntelWar:
    def __init__(self):
        # 🛰️ DICIONÁRIO DE INTELIGÊNCIA (ALVOS ESTRATÉGICOS)
        self.urls = {
            "global": "https://liveuamap.com/",
            "ucrania": "https://ukraine.liveuamap.com/",
            "israel": "https://israelpalestine.liveuamap.com/",
            "defcon": "https://www.defconlevel.com/",
            "pizzint": "https://www.pizzint.watch/"
        }
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]

    def _obter_chave_segura(self, texto_usuario):
        """Mapeia o comando do usuário para uma chave do dicionário"""
        if not texto_usuario: return "global"
        
        texto = texto_usuario.lower().strip()
        mapa = {
            "ucrânia": "ucrania", "ucrania": "ucrania", "ukraine": "ucrania",
            "israel": "israel", "gaza": "israel", "palestina": "israel",
            "defcon": "defcon", "pizzint": "pizzint", "global": "global", "mundo": "global"
        }
        return mapa.get(texto, "global")

    def get_war_report_with_screenshot(self, setor_input="global"):
        """Captura visual dos fronts de batalha"""
        chave = self._obter_chave_segura(setor_input)
        
        # Fallback seguro para evitar KeyError
        url = self.urls.get(chave, self.urls["global"])
        
        # Caminho absoluto para garantir entrega no Telegram
        pasta_raiz = os.path.dirname(os.path.abspath(__file__))
        screenshot_path = os.path.join(os.path.dirname(pasta_raiz), f"intel_{chave}.png")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=random.choice(self.user_agents)
                )
                page = context.new_page()
                
                print(f"🛰️ [INTEL]: Infiltrando no setor {chave.upper()}...")
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Tempo para carregar camadas do mapa
                time.sleep(6)
                
                # Tenta fechar banners de cookies/popups
                try: page.locator("button:has-text('Accept'), .popup-close").click(timeout=2000)
                except: pass
                
                page.screenshot(path=screenshot_path)
                
                headlines = ""
                if "liveuamap" in url:
                    titles = page.locator(".title").all_text_contents()
                    if titles: headlines = "\n".join([f"• {t.strip()}" for t in titles[:5]])
                
                browser.close()
                return headlines, screenshot_path
        except Exception as e:
            print(f"❌ Erro na extração visual: {e}")
            return f"⚠️ Falha técnica: {str(e)}", None

    def get_pizzint_text_only(self):
        """Extração de dados brutos (Sem Print) para PIZZINT"""
        headers = {'User-Agent': random.choice(self.user_agents)}
        try:
            response = requests.get(self.urls["pizzint"], headers=headers, timeout=10)
            html = response.text
            
            # Extração simples via Regex/Busca
            import re
            defcon_match = re.search(r'DEFCON\s+(\d+)', html)
            status = f"DEFCON {defcon_match.group(1)}" if defcon_match else "Status Oculto"
            
            orders_match = re.search(r'(\d+)\s+Orders', html)
            pedidos = orders_match.group(1) if orders_match else "0"

            return f"🚨 *PIZZINT WATCH MONITOR*\n🔹 {status}\n🔹 Atividade: {pedidos} ordens ativas."
        except:
            return "⚠️ PIZZINT: Erro de interceptação de dados."