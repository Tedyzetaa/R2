import requests
import random

class RadioScanner:
    def __init__(self):
        # Base da API pública do Radio-Browser
        self.base_url = "http://de1.api.radio-browser.info/json/stations"

    def scan_active_transmissions(self, mode="global", limit=10):
        """
        Analisa frequências ativas.
        Modos: 'global' (Top cliques), 'news', 'emergency', 'music'
        """
        try:
            results = []
            endpoint = ""
            
            # 1. Seleção de Alvo
            if mode == "global":
                # Pega as estações mais ouvidas no momento (Garantia de transmissão)
                endpoint = f"{self.base_url}/topclick/{limit}"
            elif mode == "local":
                # Estações do Brasil
                endpoint = f"{self.base_url}/bycountry/brazil?limit={limit}&order=clickcount&reverse=true"
            else:
                # Busca por tag (ex: news, 80s, police)
                endpoint = f"{self.base_url}/bytag/{mode}?limit={limit}&order=clickcount&reverse=true"

            # 2. Interceptação
            print(f"📡 [SCANNER]: Varrendo espectro: {endpoint}...")
            res = requests.get(endpoint, timeout=10)
            
            if res.status_code == 200:
                stations = res.json()
                
                # 3. Análise de Sinal
                for s in stations:
                    # Filtra dados vitais
                    info = {
                        "nome": s.get("name", "Desconhecido").strip(),
                        "url": s.get("url_resolved", ""),
                        "pais": s.get("country", "Intl"),
                        "bitrate": s.get("bitrate", 0),
                        "tags": s.get("tags", "")
                    }
                    if info["url"]: # Só adiciona se tiver link de áudio
                        results.append(info)
                
                return results
            return []
        except Exception as e:
            print(f"❌ Erro no Scanner de Rádio: {e}")
            return []

    def format_report(self, stations):
        """Formata o relatório para o Telegram"""
        if not stations:
            return "⚠️ Nenhuma transmissão ativa detectada neste setor."
        
        msg = "📡 **RELATÓRIO DE INTERCEPTAÇÃO DE RÁDIO** 📡\n\n"
        for i, s in enumerate(stations[:8]): # Limita a 8 para não poluir
            msg += f"📻 **{i+1}. {s['nome']}** ({s['pais']})\n"
            msg += f"   qualidade: {s['bitrate']} kbps | tags: {s['tags'][:30]}...\n"
            msg += f"   🔗 [Ouvir Transmissão]({s['url']})\n\n"
        
        msg += "⚠️ *Clique no link para sintonizar no player do celular.*"
        return msg