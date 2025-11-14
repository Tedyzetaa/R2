import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class Settings:
    # Configurações de API
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
    
    # Configurações do Assistente
    ASSISTANT_NAME = "R2"
    LANGUAGE = "pt-BR"
    USE_AUDIO = True
    
    # Configurações de Trading
    TRADING_ENABLED = bool(BINANCE_API_KEY and BINANCE_SECRET_KEY)
    TESTNET = False  # Use testnet para desenvolvimento
    
    # Configurações de UI
    THEME = "dark"
    
    @classmethod
    def validate_apis(cls):
        """Valida se as APIs necessárias estão configuradas."""
        missing_apis = []
        
        if not cls.NEWS_API_KEY:
            missing_apis.append("NEWS_API_KEY")
        if not cls.WEATHER_API_KEY:
            missing_apis.append("WEATHER_API_KEY")
            
        # Binance API é opcional para funcionalidades básicas
        if not cls.BINANCE_API_KEY or not cls.BINANCE_SECRET_KEY:
            print("⚠️  Binance API não configurada - Funcionalidades de trading desativadas")
            
        if missing_apis:
            print(f"⚠️  APIs não configuradas: {', '.join(missing_apis)}")
            print("   Algumas funcionalidades podem não funcionar.")
            
        return len(missing_apis) == 0