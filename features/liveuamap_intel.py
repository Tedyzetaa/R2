import feedparser
import webbrowser
import cloudscraper
import time

class FrontlineIntel:
    def __init__(self, region="ukraine"):
        self.current_region = region
        self.last_update = []
        
        # URLs dos Mapas Interativos (Visual)
        self.maps_urls = {
            "ukraine": "https://ukraine.liveuamap.com",
            "israel": "https://israelpalestine.liveuamap.com",
            "syria": "https://syria.liveuamap.com",
            "global": "https://liveuamap.com"
        }
        
        # Feeds de Notícias (Texto)
        self.feeds_primary = {
            "ukraine": "https://ukraine.liveuamap.com/rss",
            "israel": "https://israelpalestine.liveuamap.com/rss",
            "syria": "https://syria.liveuamap.com/rss",
            "global": "https://liveuamap.com/rss"
        }
        
        self.feeds_backup = {
            "ukraine": "https://news.google.com/rss/search?q=Guerra+Ucrânia+front&hl=pt-BR&gl=BR&ceid=BR:pt-419",
            "israel": "https://news.google.com/rss/search?q=Guerra+Israel+Gaza&hl=pt-BR&gl=BR&ceid=BR:pt-419",
            "syria": "https://news.google.com/rss/search?q=Guerra+Síria&hl=pt-BR&gl=BR&ceid=BR:pt-419",
            "global": "https://news.google.com/rss/topics/CAAqJggBCiSJQVnBm8Oueg8LEg0vZy/11r0v7_6l1KggQECAQw1?hl=pt-BR&gl=BR&ceid=BR:pt-419"
        }

    def get_available_theaters(self):
        return "\n".join([f"➤ {key.upper()}" for key in self.feeds_primary.keys()])

    def open_tactical_map(self):
        """Abre o mapa interativo da região atual"""
        url = self.maps_urls.get(self.current_region, self.maps_urls["global"])
        print(f"🗺️ [INTEL]: Carregando projeção cartográfica de {self.current_region.upper()}...")
        webbrowser.open(url)
        return f"🗺️ Mapa tático do setor {self.current_region.upper()} projetado no visor principal."

    def get_tactical_report(self, limit=5):
        # ... (O código anterior do relatório continua idêntico aqui) ...
        # (Vou resumir para não ocupar espaço, mantenha a lógica do Cloudscraper da V3.0)
        url = self.feeds_primary.get(self.current_region, self.feeds_primary["global"])
        backup_url = self.feeds_backup.get(self.current_region, self.feeds_backup["global"])
        
        data = None
        source_name = "LIVEUAMAP"

        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url)
            if response.status_code == 200: data = response.content
            else: raise Exception("Block")
        except:
            import requests
            try:
                data = requests.get(backup_url, timeout=5).content
                source_name = "GOOGLE INTEL"
            except: return "❌ Falha total de sinal."

        try:
            feed = feedparser.parse(data)
            if not feed.entries: return f"⚠️ Setor vazio ({source_name})."
            
            report = [f"📊 RELATÓRIO TÁTICO: {self.current_region.upper()} [{source_name}]"]
            self.last_update = feed.entries[:limit]
            
            for i, entry in enumerate(self.last_update):
                title = entry.title.replace("&quot;", '"').replace("&#39;", "'").replace("<b>", "").replace("</b>", "")
                data_pub = entry.get("published", "Recente")
                item = (
                    f"\n\n[{i+1}] ⏰ {data_pub}\n"
                    f"⚠️ {title}\n"
                    f"{entry.link}"
                )
                report.append(item)
            return "".join(report)
        except Exception as e: return f"❌ Erro: {e}"

    def open_source_evidence(self, index):
        # (Mantém igual ao anterior)
        try:
            idx = int(index) - 1
            if 0 <= idx < len(self.last_update):
                webbrowser.open(self.last_update[idx].link)
                return f"✅ Visualizando alvo #{index}."
            return "⚠️ Índice inválido."
        except: return "⚠️ Erro."