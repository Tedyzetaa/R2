"""
Configurações do sistema R2 Assistant - Atualizado para NOAA
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Gerenciador de configurações"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config_path = Path("config.json")
        self.default_config = self._get_default_config()
        self.config = self._load_config()
        
        # Configurações NOAA
        self.noaa_config = {
            "ENABLE_NOAA": True,
            "ENABLE_SOLAR_MONITOR": True,
            "NOAA_UPDATE_INTERVAL": 300,  # 5 minutos
            "NOAA_ALERT_ENABLED": True,
            "NOAA_AUTO_REPORTS": False,
            "NOAA_DATA_RETENTION_DAYS": 7,
            "NOAA_API_ENDPOINTS": {
                "SOLAR_WIND": "https://services.swpc.noaa.gov/json/ace/swepam.json",
                "GEOMAGNETIC_INDICES": "https://services.swpc.noaa.gov/json/goes/primary/xray-flares.json",
                "SOLAR_FLARES": "https://services.swpc.noaa.gov/json/goes/primary/xray-flares.json"
            },
            "NOAA_ALERT_THRESHOLDS": {
                "SOLAR_FLARE": ["M", "X", "X+"],
                "KP_INDEX": 6.0,
                "SOLAR_WIND_SPEED": 600
            }
        }
        
        # Mesclar configurações NOAA
        self.config.update(self.noaa_config)
        
        self._initialized = True
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        return {
            "VERSION": "2.1.0",
            "APP_NAME": "R2 Assistant",
            "THEME": "sci_fi",
            "LANGUAGE": "pt-BR",
            "VOICE_ENABLED": True,
            "AUTO_START": False,
            "LOG_LEVEL": "INFO",
            "ENABLE_NOAA": True,
            "ENABLE_SOLAR_MONITOR": True,
            "NOAA_UPDATE_INTERVAL": 300
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar config: {e}")
                return self.default_config.copy()
        else:
            # Criar arquivo de configuração
            self._save_config(self.default_config)
            return self.default_config.copy()
    
    def _save_config(self, config: Dict[str, Any]):
        """Salva configuração no arquivo"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
    
    def get(self, key: str, default=None):
        """Obtém valor de configuração"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Define valor de configuração"""
        self.config[key] = value
        self._save_config(self.config)
    
    def get_noaa_config(self) -> Dict[str, Any]:
        """Retorna configurações NOAA"""
        return {
            k: v for k, v in self.config.items() 
            if k.startswith("NOAA_") or k in ["ENABLE_NOAA", "ENABLE_SOLAR_MONITOR"]
        }
    
    def update_noaa_config(self, updates: Dict[str, Any]):
        """Atualiza configurações NOAA"""
        for key, value in updates.items():
            self.config[key] = value
        self._save_config(self.config)

# Instância global
config = Config()
