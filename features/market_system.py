import requests

class MarketSystem:
    def __init__(self):
        # USD-BRL, EUR-BRL, BTC-BRL
        self.url = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL"

    def obter_cotacoes(self):
        try:
            response = requests.get(self.url, timeout=5)
            data = response.json()
            
            usd = float(data['USDBRL']['bid'])
            eur = float(data['EURBRL']['bid'])
            btc = float(data['BTCBRL']['bid']) / 1000 # Converte para 'k'
            
            var_usd = float(data['USDBRL']['pctChange'])
            icon_usd = "🔼" if var_usd >= 0 else "🔽"
            
            relatorio = (
                "💰 **MARKET INTEL**\n"
                f"💵 USD: R$ {usd:.2f} {icon_usd} ({var_usd}%)\n"
                f"💶 EUR: R$ {eur:.2f}\n"
                f"🪙 BTC: R$ {btc:.1f}k"
            )
            return relatorio
        except Exception as e:
            return f"❌ Erro de conexão financeira: {e}"