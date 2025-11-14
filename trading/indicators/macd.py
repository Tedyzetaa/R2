import pandas as pd
from typing import Tuple
from typing import List

def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[float, float, float]:
    """Calcula MACD, Signal Line e Histogram"""
    if len(prices) < slow_period + signal_period:
        return None, None, None
    
    df = pd.DataFrame(prices, columns=['close'])
    
    exp1 = df['close'].ewm(span=fast_period, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow_period, adjust=False).mean()
    
    macd = exp1 - exp2
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal
    
    return float(macd.iloc[-1]), float(signal.iloc[-1]), float(histogram.iloc[-1])