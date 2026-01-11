import requests
from bs4 import BeautifulSoup

class NewsBriefing:
    def get_top_headlines(self):
        try:
            url = "https://g1.globo.com/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Busca as principais manchetes no G1
            manchetes = soup.find_all('a', class_='feed-post-link', limit=5)
            
            resumo = "📰 **BRIEFING DE NOTÍCIAS (G1)**\n\n"
            for i, item in enumerate(manchetes, 1):
                resumo += f"{i}. {item.text.strip()}\n"
            
            return resumo
        except Exception as e:
            return f"❌ Falha ao obter briefing: {e}"