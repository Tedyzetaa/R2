# --- CONFIGURAÇÕES DE SENSIBILIDADE (PATCH AGRESSIVO) ---

# No seu alpha_module.py, localize e altere estas variáveis:

class TacticalConfig:
    # Aumentado de 3.0 para 5.0: Aceita sinais que o OCR detectou há mais tempo
    MAX_SIGNAL_AGE_SECONDS = 5.0 
    
    # Reduzido de 0.50 para 0.15: O mercado não precisa estar em super tendência
    # para o Sniper disparar. Se houver inclinação mínima, ele entra.
    MIN_BIAS_THRESHOLD = 0.15 
    
    # Ajuste no filtro de Tick (Micro-momentum)
    # Permite uma variação maior de preço contra a entrada antes de abortar
    TICK_VOLATILITY_TOLERANCE = 0.0008 # Valor sugerido para maior fluidez