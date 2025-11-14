import pandas as pd
from typing import List

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calcula Relative Strength Index"""
    if len(prices) < period + 1:
        return None
    
    df = pd.DataFrame(prices, columns=['close'])
    delta = df['close'].diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0