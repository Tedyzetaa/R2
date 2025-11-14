import pandas as pd
import numpy as np
from typing import List

def calculate_sma(prices: List[float], period: int) -> float:
    """Calcula Simple Moving Average"""
    if len(prices) < period:
        return None
    
    return sum(prices[-period:]) / period

def calculate_ema(prices: List[float], period: int) -> float:
    """Calcula Exponential Moving Average"""
    if len(prices) < period:
        return None
    
    df = pd.DataFrame(prices, columns=['close'])
    ema = df['close'].ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])