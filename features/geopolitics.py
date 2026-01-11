import feedparser
from datetime import datetime

class GeopoliticsManager:
    def __init__(self):
        # Lista de fontes estratégicas (Reuters e BBC World)
        self.feeds = [
            "http://feeds.reuters.com/reuters/worldNews",
            "http://feeds.bbci.co.uk/news/world/rss.xml"
        ]

    def get_briefing(self, limit=5):
        briefing = []
        for url in self.feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit]:
                # Lógica simples de prioridade
                priority = "INFO"
                lower_title = entry.title.lower()
                
                if any(word in lower_title for word in ["war", "nuclear", "attack", "conflict", "missile"]):
                    priority = "CRÍTICO"
                elif any(word in lower_title for word in ["china", "russia", "usa", "election", "economy"]):
                    priority = "ESTRATÉGICO"

                briefing.append({
                    "priority": priority,
                    "title": entry.title,
                    "link": entry.link
                })
        return briefing