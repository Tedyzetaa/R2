import requests
import webbrowser
import json
import os
import logging
from typing import Optional

def register_web_commands(command_system, falar, ouvir_comando):
    """Registra comandos web."""
    logger = logging.getLogger(__name__)

    def pesquisar_google(query="", falar_func=None, ouvir_func=None):
        if not query:
            falar_func("O que você gostaria de pesquisar?")
            query = ouvir_func()
            
        if query:
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            falar_func(f"Pesquisando por {query} no Google.")
        else:
            falar_func("Não entendi o que pesquisar.")

    def obter_noticias_principais(falar_func=None, ouvir_func=None):
        try:
            # Usando NewsAPI (gratuita - precisa de chave)
            api_key = os.getenv("NEWS_API_KEY")
            
            if not api_key:
                falar_func("Chave da API de notícias não configurada.")
                # Fallback: abre site de notícias
                webbrowser.open("https://news.google.com")
                falar_func("Abrindo notícias no Google News.")
                return

            url = f"https://newsapi.org/v2/top-headlines?country=br&apiKey={api_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data["status"] == "ok" and data["articles"]:
                falar_func("Aqui estão as principais notícias:")
                for i, article in enumerate(data["articles"][:3]):
                    falar_func(f"{i+1}. {article['title']}")
            else:
                falar_func("Não foi possível obter as notícias no momento.")
        except Exception as e:
            logger.error(f"Erro ao obter notícias: {e}")
            falar_func("Erro ao buscar notícias. Abrindo site alternativo.")
            webbrowser.open("https://g1.globo.com")

    def obter_previsao_tempo(falar_func=None, ouvir_func=None):
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            
            if not api_key:
                falar_func("Chave da API de clima não configurada.")
                return

            falar_func("Para qual cidade você quer a previsão do tempo?")
            cidade = ouvir_func()
            
            if cidade:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&units=metric&lang=pt"
                response = requests.get(url, timeout=10)
                data = response.json()

                if data["cod"] == 200:
                    temp = data["main"]["temp"]
                    desc = data["weather"][0]["description"]
                    cidade_nome = data["name"]
                    falar_func(f"Em {cidade_nome} está {desc} com temperatura de {temp:.1f} graus.")
                else:
                    falar_func(f"Cidade {cidade} não encontrada.")
            else:
                falar_func("Não entendi o nome da cidade.")
        except Exception as e:
            logger.error(f"Erro ao obter previsão: {e}")
            falar_func("Erro ao buscar previsão do tempo.")

    def obter_cotacao_cripto(cripto="", falar_func=None, ouvir_func=None):
        try:
            if not cripto:
                cripto = "bitcoin"
                
            cripto = cripto.lower().strip()
            moedas = {
                'bitcoin': 'bitcoin',
                'ethereum': 'ethereum',
                'doge': 'dogecoin',
                'cardano': 'cardano'
            }
            
            moeda_id = moedas.get(cripto, cripto)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={moeda_id}&vs_currencies=brl"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if moeda_id in data:
                preco = data[moeda_id]["brl"]
                falar_func(f"O preço do {cripto} é R$ {preco:,.2f}")
            else:
                falar_func(f"Criptomoeda {cripto} não encontrada.")
        except Exception as e:
            logger.error(f"Erro ao obter cotação: {e}")
            falar_func("Erro ao buscar cotação de criptomoeda.")

    def cotacao_bitcoin(falar_func=None, ouvir_func=None):
        obter_cotacao_cripto("bitcoin", falar_func, ouvir_func)

    def cotacao_ethereum(falar_func=None, ouvir_func=None):
        obter_cotacao_cripto("ethereum", falar_func, ouvir_func)

    # Registra os comandos
    command_system.register_command("pesquisar", pesquisar_google, "Pesquisa no Google")
    command_system.register_command("notícias", obter_noticias_principais, "Mostra as principais notícias")
    command_system.register_command("previsão do tempo", obter_previsao_tempo, "Mostra a previsão do tempo")
    command_system.register_command("cotação", obter_cotacao_cripto, "Mostra cotação de criptomoeda")
    command_system.register_command("bitcoin", cotacao_bitcoin, "Cotação do Bitcoin")
    command_system.register_command("ethereum", cotacao_ethereum, "Cotação do Ethereum")