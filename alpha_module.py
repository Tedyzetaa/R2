# filename: alpha_module.py
# ============================================================
# ESTRATÉGIA: FIRST TOUCH COMMAND (Ghost Protocol v21)
# ============================================================
# - Detecta Velas de Comando (bull: open==low, bear: open==high)
# - Cria zonas de Suporte (verde) e Resistência (vermelha)
# - No primeiro toque da zona, dispara ordem imediatamente e remove a zona
# - Logs detalhados para observabilidade
# ============================================================

import time
import logging
import threading
import re
import html
import urllib.request
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, Any, List, Union
from enum import Enum
from playwright.sync_api import Page
import requests
from bs4 import BeautifulSoup

# --- OCR imports ---
import pytesseract
from PIL import Image
import io
import os
from collections import deque, Counter

logger = logging.getLogger("ModuloAlpha")

ASSET_PRICE_MIN = 3.0
ASSET_PRICE_MAX = 7.0

import numpy as np

# ====================================================================
# CONFIGURAÇÃO DE RISCO (Money Management)
# ====================================================================
@dataclass
class RiskConfig:
    """Gerencia Stop Loss diário, Take Profit e recuperação."""
    daily_loss_limit: float = 100.0          
    daily_profit_target: float = 300.0       # Take Profit diário
    base_risk_per_trade: float = 10.0        # Risco base por trade (padrão)
    recovery_factor_soros: float = 0.5       # Após 2 perdas consecutivas, reduz exposição em 50%
    max_consecutive_losses_before_reduce: int = 2
    min_risk_per_trade: float = 2.0
    
    def __post_init__(self):
        self._daily_pnl = 0.0
        self._consecutive_losses = 0
        logger.info(f"[RiskConfig] Limite diário={self.daily_loss_limit}, "
                    f"Meta diária={self.daily_profit_target}, Fator Soros={self.recovery_factor_soros}")
    
    def reset_daily(self):
        self._daily_pnl = 0.0
        self._consecutive_losses = 0
        logger.info("[RiskConfig] Reset diário aplicado.")
    
    def update_result(self, pnl: float):
        self._daily_pnl += pnl
        if pnl < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0
    
    def get_position_size_multiplier(self) -> float:
        if self._consecutive_losses >= self.max_consecutive_losses_before_reduce:
            return self.recovery_factor_soros
        return 1.0
    
    def is_daily_stopped(self) -> bool:
        return self._daily_pnl <= -self.daily_loss_limit or self._daily_pnl >= self.daily_profit_target
    
    def get_remaining_daily_capacity(self) -> float:
        return max(0, self.daily_loss_limit + self._daily_pnl) if self._daily_pnl < 0 else float('inf')

# ====================================================================
# ANALISADOR DE ESTRUTURA DE MERCADO (Topos, Fundos, Tendência)
# ====================================================================
class MarketStructure:
    """Identifica topos/fundos e classifica tendência: ALTA, BAIXA, LATERAL."""
    def __init__(self, lookback: int = 20, min_touch: int = 2):
        self.lookback = lookback
        self.min_touch = min_touch
        self.history_high: List[float] = []
        self.history_low: List[float] = []
        self.trend: str = "LATERAL"
        self._last_update = 0
        
    def update(self, high: float, low: float, close: float):
        self.history_high.append(high)
        self.history_low.append(low)
        if len(self.history_high) > self.lookback:
            self.history_high.pop(0)
            self.history_low.pop(0)
        self._detect_trend()
    
    def _detect_trend(self):
        if len(self.history_high) < 10:
            self.trend = "LATERAL"
            return
        highs = self.history_high
        lows = self.history_low
        tops = [highs[i] for i in range(2, len(highs)-2)
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                   highs[i] > highs[i+1] and highs[i] > highs[i+2]]
        bottoms = [lows[i] for i in range(2, len(lows)-2)
                   if lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                      lows[i] < lows[i+1] and lows[i] < lows[i+2]]
        if len(tops) >= 2 and len(bottoms) >= 2:
            rising_tops = all(tops[i] < tops[i+1] for i in range(len(tops)-1))
            rising_bottoms = all(bottoms[i] < bottoms[i+1] for i in range(len(bottoms)-1))
            if rising_tops and rising_bottoms:
                self.trend = "ALTA"
                return
            falling_tops = all(tops[i] > tops[i+1] for i in range(len(tops)-1))
            falling_bottoms = all(bottoms[i] > bottoms[i+1] for i in range(len(bottoms)-1))
            if falling_tops and falling_bottoms:
                self.trend = "BAIXA"
                return
        self.trend = "LATERAL"
    
    def allowed_direction(self, direction: str) -> bool:
        if self.trend == "ALTA" and direction == "PUT":
            return False
        if self.trend == "BAIXA" and direction == "CALL":
            return False
        return True
    
    def get_trend_description(self) -> str:
        return self.trend

# ====================================================================
# DETECTOR DE ROMPIMENTO (Breakout + Pullback) - mantido para compatibilidade
# ====================================================================
class BreakoutDetector:
    """Detecta zonas de consolidação (mínimo 3 toques), rompimento e pullback."""
    def __init__(self, lookback: int = 100, min_touches: int = 3, volume_avg_period: int = 5):
        self.lookback = lookback
        self.min_touches = min_touches
        self.volume_avg_period = volume_avg_period
        self.consolidation_zones: List[Tuple[float, float]] = []
        self.breakout_detected: bool = False
        self.breakout_direction: Optional[str] = None
        self.pullback_confirmed: bool = False
        self._last_breakout_candle_volume = 0.0
        self._volume_history: List[float] = []
    
    def update(self, high: float, low: float, close: float, volume: float, price_history: List[float]):
        self._volume_history.append(volume)
        if len(self._volume_history) > self.volume_avg_period:
            self._volume_history.pop(0)
        self._detect_consolidation_zones(price_history)
        self._check_breakout(high, low, close)
        if self.breakout_detected and not self.pullback_confirmed:
            self._check_pullback(close)
    
    def _detect_consolidation_zones(self, prices: List[float]):
        if len(prices) < 20:
            return
        self.consolidation_zones.clear()
        window = 5
        for i in range(0, len(prices) - window, window // 2):
            chunk = prices[i:i + window]
            if len(chunk) < window:
                continue
            sup = min(chunk)
            res = max(chunk)
            touches_sup = sum(1 for p in prices if abs(p - sup) / sup < 0.002)
            touches_res = sum(1 for p in prices if abs(p - res) / res < 0.002)
            if touches_sup >= self.min_touches and touches_res >= self.min_touches:
                self.consolidation_zones.append((sup, res))

    def _check_breakout(self, high: float, low: float, close: float):
        for sup, res in self.consolidation_zones:
            if close > res and high > res * 1.002:
                avg_vol = np.mean(self._volume_history) if self._volume_history else 1
                if self._volume_history and self._volume_history[-1] > avg_vol * 1.5:
                    self.breakout_detected = True
                    self.breakout_direction = "CALL"
                    self._last_breakout_candle_volume = self._volume_history[-1]
                    break
            elif close < sup and low < sup * 0.998:
                avg_vol = np.mean(self._volume_history) if self._volume_history else 1
                if self._volume_history and self._volume_history[-1] > avg_vol * 1.5:
                    self.breakout_detected = True
                    self.breakout_direction = "PUT"
                    self._last_breakout_candle_volume = self._volume_history[-1]
                    break
    
    def _check_pullback(self, close: float):
        if self.breakout_direction == "CALL":
            for sup, res in self.consolidation_zones:
                if abs(close - res) / res < 0.003:
                    self.pullback_confirmed = True
                    logger.info(f"[Breakout] Pullback confirmado para CALL perto de {res:.5f}")
                    break
        elif self.breakout_direction == "PUT":
            for sup, res in self.consolidation_zones:
                if abs(close - sup) / sup < 0.003:
                    self.pullback_confirmed = True
                    logger.info(f"[Breakout] Pullback confirmado para PUT perto de {sup:.5f}")
                    break
    
    def is_valid_breakout_signal(self, direction: str) -> bool:
        return (self.breakout_detected and self.pullback_confirmed and
                self.breakout_direction == direction)
    
    def reset(self):
        self.breakout_detected = False
        self.pullback_confirmed = False
        self.breakout_direction = None

# --- CONFIGURAÇÕES TÁTICAS ---
class TacticalConfig:
    MAX_SIGNAL_AGE_SECONDS = 5.0
    MIN_BIAS_THRESHOLD = 0.15
    TICK_VOLATILITY_TOLERANCE = 0.0008

_tess_path = os.environ.get("TESSERACT_CMD", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
if os.path.exists(_tess_path):
    pytesseract.pytesseract.tesseract_cmd = _tess_path

class ScreenState(str, Enum):
    IDLE = "IDLE"
    WAITING_SIGNAL = "WAITING_SIGNAL"
    GATINHO_CALL = "GATINHO_CALL"
    GATINHO_PUT = "GATINHO_PUT"
    POSITION_OPEN = "POSITION_OPEN"
    COOLDOWN = "COOLDOWN"
    ARMED = "ARMED"
    UNKNOWN = "UNKNOWN"

@dataclass
class InferenceResult:
    state: str = ScreenState.UNKNOWN
    confidence: float = 0.0
    recommended_action: str = "WAIT"
    details: dict = field(default_factory=dict)


# ============================================================
# 1. MACRO: RADAR GEOPOLÍTICO
# ============================================================
class NewsSentimentAnalyzer:
    def __init__(self, symbol: str = "USD-BRL", logger_instance=None):
        self.symbol = symbol
        self.news_bias = 0.0
        self.last_news_update = 0.0
        self.update_interval = 30
        self._lock = threading.Lock()
        self.logger = logger_instance if logger_instance else logging.getLogger("NewsSentimentAnalyzer")

    def get_sentiment(self) -> float:
        now = time.time()
        if now - self.last_news_update > self.update_interval:
            threading.Thread(target=self._fetch_news, daemon=True).start()
        with self._lock:
            return self.news_bias

    def _fetch_news(self):
        now = time.time()
        if now - self.last_news_update < 30:
            return
        self.last_news_update = now
        combined_sentiment = 0
        sources = [
            f"https://www.google.com/search?q={self.symbol}+finance+news&tbm=nws",
            f"https://www.reuters.com/search/news?blob={self.symbol}",
            "https://www.bloomberg.com/markets"
        ]
        try:
            for url in sources:
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    headlines = soup.find_all(['h3', 'h4', 'a'], limit=5)
                    for h in headlines:
                        text = h.get_text().lower()
                        if any(w in text for w in ['surge', 'boost', 'growth', 'upward', 'bull']):
                            combined_sentiment += 0.15
                        if any(w in text for w in ['drop', 'fall', 'crisis', 'down', 'bear']):
                            combined_sentiment -= 0.15
            with self._lock:
                self.news_bias = max(-1.0, min(1.0, combined_sentiment))
                self.logger.info(f"Feed atualizado (30s). Bias resultante: {self.news_bias:.2f}")
        except Exception as e:
            self.logger.error(f"Erro na varredura de notícias: {e}")


# ============================================================
# ESTRATÉGIA FIRST TOUCH COMMAND (Primeiro Toque)
# ============================================================
class FirstTouchManager:
    """
    Gerencia zonas de Suporte (verde) e Resistência (vermelha) baseadas em Velas de Comando.
    - No primeiro toque do preço na zona (distância <= tolerance), dispara sinal imediato.
    - Remove a zona após o toque (uso único).
    - Logs detalhados de mapeamento, monitoramento e gatilho.
    """
    def __init__(self, tolerance: float = 0.0002):
        self.zones = []          # cada zona: {'level': float, 'type': str, 'color': str, 'price': float}
        self.tolerance = tolerance

    def add_zone(self, level: float, zone_type: str, color: str) -> None:
        """Adiciona uma nova zona (Suporte ou Resistência). Evita duplicatas próximas."""
        for z in self.zones:
            if abs(z['level'] - level) < self.tolerance and z['type'] == zone_type:
                # Zona já existente, log silencioso (apenas debug)
                logger.debug(f"[SCANNER] Zona {zone_type} já existente em {level:.5f} - ignorada.")
                return
        self.zones.append({
            'level': level,
            'type': zone_type,
            'color': color,
            'price': level
        })
        # LOG DE MAPEAMENTO
        logger.info(f"[SCANNER] 📍 Nova zona detectada | Cor: {color} | Preço Estimado: {level:.5f} | Tipo: {zone_type}")

    def update(self, current_price: float) -> Optional[str]:
        """
        Verifica se o preço tocou alguma zona ativa (first touch).
        Retorna 'CALL' para toque em SUPORTE, 'PUT' para RESISTÊNCIA, ou None.
        Remove a zona imediatamente após o toque.
        """
        now = time.time()
        for i, zone in enumerate(self.zones):
            if abs(current_price - zone['level']) <= self.tolerance:
                # TOQUE DETECTADO!
                signal = 'CALL' if zone['type'] == 'SUPPORT' else 'PUT'
                cor = zone['color']
                level = zone['level']
                # LOG DE GATILHO
                logger.info(f"[🎯 TRIGGER] ⚡ TOQUE DETECTADO! Linha {cor} em {level:.5f}. Enviando ordem de {signal}...")
                # Remove a zona (uso único)
                self.zones.pop(i)
                return signal
        return None

    def get_active_zones(self) -> List[Dict]:
        """Retorna as zonas ativas para monitoramento externo."""
        return self.zones

    def reset(self) -> None:
        self.zones.clear()


# ============================================================
# 2. MESO: MOTOR QUANTITATIVO AUTO-ADAPTÁVEL
# ============================================================
class MarketTracker:
    def __init__(self):
        self.assets: Dict[int, Dict[str, Any]] = {}
        self.direcao_tendencia = "NEUTRAL"
        self._lock = threading.Lock()
        self.market_structure = MarketStructure(lookback=20)
        self.breakout_detector = BreakoutDetector()
        self.volumes: List[float] = []

    def _init_asset_state(self, asset_id: int) -> Dict[str, Any]:
        return {
            "history_c": deque(maxlen=20),
            "history_o": deque(maxlen=20),
            "history_h": deque(maxlen=20),
            "history_l": deque(maxlen=20),
            "last_candle_time": None,
            "current_close": None,
            "current_open": None,
            "current_high": None,
            "current_low": None,
            "consecutive_ticks": 0,
            "last_color_state": "UNKNOWN",
        }

    def update_robust(self, asset_id: int, op: float, cl: float, candle_time: int, volume: float = 1.0) -> bool:
        with self._lock:
            if asset_id not in self.assets:
                self.assets[asset_id] = self._init_asset_state(asset_id)
            state = self.assets[asset_id]
            is_new_candle = False
            current_color = "UNKNOWN"
            if cl > op:
                current_color = "GREEN"
            elif cl < op:
                current_color = "RED"
            if current_color == "UNKNOWN":
                state["consecutive_ticks"] = 0
                state["last_color_state"] = "UNKNOWN"
            else:
                if current_color == state["last_color_state"]:
                    state["consecutive_ticks"] += 1
                else:
                    state["consecutive_ticks"] = 1
                    state["last_color_state"] = current_color
            if state["last_candle_time"] is None:
                state["last_candle_time"] = candle_time
            if candle_time != state["last_candle_time"]:
                if state["current_close"] is not None:
                    state["history_c"].append(state["current_close"])
                    state["history_o"].append(state["current_open"])
                    state["history_h"].append(state.get("current_high", state["current_close"]))
                    state["history_l"].append(state.get("current_low", state["current_close"]))
                state["last_candle_time"] = candle_time
                state["current_open"] = op
                state["current_high"] = cl
                state["current_low"] = cl
                is_new_candle = True
            if state["current_open"] is None:
                state["current_open"] = op
                state["current_high"] = cl
                state["current_low"] = cl
            state["current_close"] = cl
            state["current_high"] = max(state.get("current_high", cl), cl)
            state["current_low"] = min(state.get("current_low", cl), cl)
            return is_new_candle

    def get_color_ticks(self, asset_id: int) -> Tuple[str, int]:
        with self._lock:
            if asset_id not in self.assets:
                return ("UNKNOWN", 0)
            state = self.assets[asset_id]
            return (state["last_color_state"], state["consecutive_ticks"])

    def get_current_close(self, asset_id: int) -> Optional[float]:
        with self._lock:
            if asset_id not in self.assets:
                return None
            return self.assets[asset_id]["current_close"]

    def get_history_len(self, asset_id: int) -> int:
        with self._lock:
            if asset_id not in self.assets:
                return 0
            return len(self.assets[asset_id]["history_c"])

    def get_history(self, asset_id: int) -> List[float]:
        with self._lock:
            if asset_id not in self.assets:
                return []
            return self.assets[asset_id]["history_c"]

    def get_ma20(self, asset_id: int) -> Optional[float]:
        hist = self.get_history(asset_id)
        if len(hist) >= 20:
            return sum(hist[-20:]) / 20
        return None
    
    def get_rsi14(self, asset_id: int) -> Optional[float]:
        hist = self.get_history(asset_id)
        if len(hist) < 15:
            return None
        deltas = [hist[i] - hist[i-1] for i in range(1, len(hist))]
        gains = [max(d, 0) for d in deltas]
        losses = [max(-d, 0) for d in deltas]
        avg_gain = sum(gains[:14]) / 14
        avg_loss = sum(losses[:14]) / 14
        for i in range(14, len(gains)):
            avg_gain = (avg_gain * 13 + gains[i]) / 14
            avg_loss = (avg_loss * 13 + losses[i]) / 14
        if avg_loss == 0:
            return 100.0
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    def get_volume_avg(self, period: int = 5) -> float:
        with self._lock:
            if len(self.volumes) >= period:
                return sum(self.volumes[-period:]) / period
            return 1.0

    def check_confirmacao_vela(self, candle_atual, candle_anterior):
        if self.direcao_tendencia == "CALL":
            if candle_atual['close'] > (candle_anterior['high'] * 0.9985):
                return True
        elif self.direcao_tendencia == "PUT":
            if candle_atual['close'] < (candle_anterior['low'] * 1.0015):
                return True
        return False

    def evaluate_scripts(self, asset_id: int) -> Tuple[Optional[str], str]:
        with self._lock:
            if asset_id not in self.assets:
                return None, ""
            state = self.assets[asset_id]
            history_c = list(state["history_c"])
            history_o = list(state["history_o"])
            history_h = list(state["history_h"])
            history_l = list(state["history_l"])
            C0 = state["current_close"]
            O0 = state["current_open"]
        if len(history_c) < 10:
            return None, f"MATRIZ_INCOMPLETA: apenas {len(history_c)} velas"
        now = time.time()
        candle_start = (int(now) // 5) * 5
        age_in_seconds = now - candle_start
        recent = history_c[-5:]
        amplitude = (max(recent) - min(recent)) / max(recent) if max(recent) > 0 else 0
        if amplitude < 0.00004:
            return None, "LATERAL_BLOQUEADO"
        momentum = abs(history_c[-1] - history_c[-3])
        avg_move = sum(abs(history_c[i] - history_c[i - 1]) for i in range(-5, -1)) / 4
        if avg_move > 0 and momentum > avg_move * 2.5:
            return None, "MOMENTUM_ESGOTADO"
        C1 = history_c[-1]
        C2 = history_c[-2]
        C3 = history_c[-3]
        C4 = history_c[-4]
        C5 = history_c[-5]
        C8 = history_c[-8]
        O2 = history_o[-2]
        O1 = history_o[-1]
        sig_dir = None
        sig_name = ""
        # FLASH pattern (mantido)
        if age_in_seconds < 1.5:
            last_3_closes = history_c[-3:]
            range_high = max(last_3_closes)
            range_low = min(last_3_closes)
            if C0 > range_high and (C0 - range_high) >= 0.0002:
                avg_range_5 = (max(history_c[-5:]) - min(history_c[-5:])) / 5
                if avg_range_5 > 0:
                    distance_from_low = C0 - min(history_c[-5:])
                    if distance_from_low / avg_range_5 < 0.7:
                        sig_dir, sig_name = "CALL", "FLASH"
                else:
                    sig_dir, sig_name = "CALL", "FLASH"
            elif C0 < range_low and (range_low - C0) >= 0.0002:
                avg_range_5 = (max(history_c[-5:]) - min(history_c[-5:])) / 5
                if avg_range_5 > 0:
                    distance_from_high = max(history_c[-5:]) - C0
                    if distance_from_high / avg_range_5 < 0.7:
                        sig_dir, sig_name = "PUT", "FLASH"
                else:
                    sig_dir, sig_name = "PUT", "FLASH"
        if not sig_dir:
            if age_in_seconds >= 4.2:
                return None, f"ENTRADA_TARDIA (Idade {age_in_seconds:.1f}s)"
            justwin_curr = None
            if (C0 > C2) and (C2 > O2) and (C4 > C8):
                justwin_curr = "CALL"
            elif (C0 < C2) and (C2 < O2) and (C4 < C8):
                justwin_curr = "PUT"
            genind_curr = None
            if (C0 > C1) and (C1 > O1) and (C3 > C2):
                genind_curr = "CALL"
            elif (C0 < C1) and (C1 < O1) and (C3 < C2):
                genind_curr = "PUT"
            if justwin_curr == genind_curr and justwin_curr is not None:
                sig_dir = justwin_curr
                sig_name = "DUPLA_CONFIRMACAO"
            elif justwin_curr is not None:
                sig_dir = justwin_curr
                sig_name = "JustWin_Solo"
            elif genind_curr is not None:
                sig_dir = genind_curr
                sig_name = "GenInd_Solo"
        if sig_dir and history_h and history_l:
            self.direcao_tendencia = sig_dir
            candle_atual = {'close': C0}
            candle_anterior = {'high': history_h[-1], 'low': history_l[-1]}
            if not self.check_confirmacao_vela(candle_atual, candle_anterior):
                return None, f"FILTRO_PA_RECUSADO ({sig_name})"
        return sig_dir, sig_name


# ============================================================
# GERENCIADOR ESTRATÉGICO (Placar)
# ============================================================
class StrategicManager:
    def __init__(self):
        self.stop_loss_diario = 2
        self.meta_diaria = 4
        self.wins = 0
        self.losses = 0
        self.losses_seguidas = 0
        
    def registrar_resultado(self, resultado):
        if resultado == "WIN":
            self.wins += 1
            self.losses_seguidas = 0
        else:
            self.losses += 1
            self.losses_seguidas += 1
        
    def check_permitir_operacao(self):
        if self.losses_seguidas >= self.stop_loss_diario:
            return False, "STOP_LOSS"
        if self.wins >= self.meta_diaria:
            return False, "META_BATIDA"
        return True, "OK"

def atualizar_painel_visual(manager):
    placar_str = f"STRIKE: {manager.wins}W - {manager.losses}L"
    print(f"\n[HUD UPDATE] {placar_str} | Sequência Loss: {manager.losses_seguidas}")

# ============================================================
# 3. MICRO: CLASSIFICADOR QUANTITATIVO + VISÃO COMPUTACIONAL
# ============================================================
class QuantClassifier:
    def __init__(self, alpha_engine_instance=None):
        self.pending_signal = None
        self._data_lock = threading.Lock()
        self.candle_maturity_delay = 0.0
        self.signal_timeout = TacticalConfig.MAX_SIGNAL_AGE_SECONDS
        self.market = MarketTracker()
        self.first_touch = FirstTouchManager(tolerance=0.0002)   # Estratégia principal
        self.last_signal: Optional[str] = None
        self._last_asset_id = 1
        self._last_ocr_scan_time = 0.0
        self.OCR_SCAN_INTERVAL = 0.0
        self._ocr_error_logged = False
        self._last_warmup_log = 0.0
        self._system_armed_logged = False
        self.news_analyzer = NewsSentimentAnalyzer(symbol="USD-BRL", logger_instance=logger)
        self.alpha_engine_instance = alpha_engine_instance
        self.risk_config = RiskConfig()

    def _extract_visual_signal(self, page: Page) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        now = time.time()
        if now - self._last_ocr_scan_time < self.OCR_SCAN_INTERVAL:
            return None, None, None
        self._last_ocr_scan_time = now
        try:
            screenshot_bytes = page.screenshot(full_page=False)
            img = Image.open(io.BytesIO(screenshot_bytes))
            width, height = img.size
            crop_x1 = int(width * 0.50)
            crop_x2 = int(width * 0.98)
            crop_y1 = int(height * 0.10)
            crop_y2 = int(height * 0.90)
            if crop_x1 >= crop_x2 or crop_y1 >= crop_y2:
                return None, None, None
            cropped = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            gray = cropped.convert('L')
            threshold_img = gray.point(lambda p: 255 if p > 150 else 0)
            scale = 2
            new_size = (threshold_img.width * scale, threshold_img.height * scale)
            big_img = threshold_img.resize(new_size, Image.Resampling.LANCZOS)
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÇçÁáÃãÂâÉéÍíÓóÚúÊêÔôÕõ '
            data = pytesseract.image_to_data(big_img, lang='por+eng', config=custom_config, output_type=pytesseract.Output.DICT)
            target_words = {
                "CALL": "CALL",
                "COMPRA": "CALL",
                "PUT": "PUT",
                "VENDA": "PUT"
            }
            best_direction = None
            best_text = None
            best_conf = -1
            best_x = -1
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip().upper()
                if not text:
                    continue
                direction = None
                for k, v in target_words.items():
                    if k == text:
                        direction = v
                        break
                if direction is None:
                    continue
                conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
                if conf < 50:
                    continue
                if conf > best_conf:
                    best_conf = conf
                    best_direction = direction
                    best_text = text
                    x = data['left'][i]
                    w = data['width'][i]
                    best_x = (x + w // 2) // scale + crop_x1
            if best_direction:
                self._ocr_error_logged = False
                return best_direction, best_text, best_x
        except Exception as e:
            if not self._ocr_error_logged:
                print(f"\n⚠️ ERRO NO MÓDULO DE VISÃO (OCR): {e}\n[Verifique se o Tesseract está instalado]")
                self._ocr_error_logged = True
            return None, None, None
        return None, None, None

    def process_network_packet(self, payload: str):
        try:
            if "{" not in payload and "[" not in payload:
                return
            payload_lower = payload.lower()
            prices = re.findall(r'"(?:close|ask|bid|value)"\s*:\s*"?([0-9]+\.[0-9]+)"?', payload_lower)
            opens = re.findall(r'"open"\s*:\s*([0-9]+\.[0-9]+)', payload_lower)
            if not prices and not opens:
                return
            cl = float(prices[-1]) if prices else float(opens[-1])
            op = float(opens[-1]) if opens else cl
            if op < 3.0 or op > 7.0:
                return
            match_id = re.search(r'"active_id"\s*:\s*(\d+)', payload_lower)
            if match_id:
                asset_id = int(match_id.group(1))
                with self._data_lock:
                    self._last_asset_id = asset_id
            else:
                asset_id = self._last_asset_id
            candle_time = int(time.time()) // 5
            self.market.update_robust(asset_id, op, cl, candle_time, volume=1)
        except Exception:
            pass

    def classify(self, page: Page) -> InferenceResult:
        try:
            html_content = page.content()
            if self._detect_posicao_aberta(html_content):
                self.pending_signal = None
                return InferenceResult(state=ScreenState.POSITION_OPEN, confidence=1.0, recommended_action="WAIT")
        except Exception:
            return InferenceResult(state=ScreenState.UNKNOWN, recommended_action="ABORT")

        if self.risk_config.is_daily_stopped():
            logger.warning("[Risk] Stop diário atingido. Nenhum trade será executado.")
            return InferenceResult(state=ScreenState.COOLDOWN, confidence=0.9,
                                   recommended_action="WAIT", details={"reason": "Daily limit"})

        asset_id = self._last_asset_id

        # Modo de aquecimento
        history_len = self.market.get_history_len(asset_id)
        if history_len < 10:
            now = time.time()
            if now - self._last_warmup_log > 5.0:
                print(f"⏳ [AQUECIMENTO TÁTICO] A calibrar histórico... ({history_len}/10 velas).")
                self._last_warmup_log = now
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=1.0, recommended_action="WAIT")
        elif not self._system_armed_logged:
            print(f"\n🎯 [SISTEMA ARMADO] Matriz 100% carregada! Aguardando first touch...")
            self._system_armed_logged = True

        # Verifica se há sinal pendente (outras estratégias)
        if self.pending_signal:
            elapsed = time.time() - self.pending_signal["timestamp"]
            if elapsed > self.signal_timeout:
                quant_dir, quant_name = self.market.evaluate_scripts(asset_id)
                if quant_dir == self.pending_signal["direction"] and not self.pending_signal.get("renewed"):
                    self.pending_signal["timestamp"] = time.time()
                    self.pending_signal["renewed"] = True
                    print(f"🔄 SINAL RENOVADO: Matemática confirma.")
                    return InferenceResult(state=ScreenState.ARMED, confidence=0.8, recommended_action="WAIT")
                print("\n⚠️ TIMEOUT: Sinal expirou.")
                self.pending_signal = None
                return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
            if elapsed < self.candle_maturity_delay:
                return InferenceResult(state=ScreenState.ARMED, confidence=0.8, recommended_action="WAIT")

            candle_color, ticks_forca = self.market.get_color_ticks(asset_id)
            direction = self.pending_signal["direction"]
            signal_name = self.pending_signal.get("name", "")

            # Tratamento de FLASH
            if signal_name == "FLASH":
                quant_dir, quant_name = self.market.evaluate_scripts(asset_id)
                if quant_dir != direction or quant_name != "FLASH":
                    print(f"⚠️ SINAL FLASH EXPIRADO.")
                    self.pending_signal = None
                    return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
                entry_price = self.market.get_current_close(asset_id) or 0.0
                self.pending_signal = None
                if direction == "CALL":
                    return InferenceResult(state=ScreenState.GATINHO_CALL, confidence=1.0,
                                           recommended_action="CLICK_ACIMA",
                                           details={"asset_id": asset_id, "entry_price": entry_price})
                else:
                    return InferenceResult(state=ScreenState.GATINHO_PUT, confidence=1.0,
                                           recommended_action="CLICK_ABAIXO",
                                           details={"asset_id": asset_id, "entry_price": entry_price})

            # Sinais JustWin/GenInd com ticks
            news_bias = self.news_analyzer.get_sentiment()
            BIAS_THRESHOLD = TacticalConfig.MIN_BIAS_THRESHOLD
            base_ticks = 0 if "DUPLA" in signal_name else 1
            required_ticks = base_ticks
            if (direction == "CALL" and news_bias < -BIAS_THRESHOLD) or (direction == "PUT" and news_bias > BIAS_THRESHOLD):
                required_ticks = base_ticks + 2

            if signal_name == "FIRST_TOUCH":  # Para compatibilidade com first touch
                entry_price = self.market.get_current_close(asset_id) or 0.0
                self.pending_signal = None
                if direction == "CALL":
                    return InferenceResult(state=ScreenState.GATINHO_CALL, confidence=1.0,
                                           recommended_action="CLICK_ACIMA",
                                           details={"asset_id": asset_id, "entry_price": entry_price})
                else:
                    return InferenceResult(state=ScreenState.GATINHO_PUT, confidence=1.0,
                                           recommended_action="CLICK_ABAIXO",
                                           details={"asset_id": asset_id, "entry_price": entry_price})

            if ticks_forca >= required_ticks:
                if direction == "CALL" and candle_color == "GREEN":
                    print("✅ ALINHAMENTO TOTAL! Disparando ACIMA!")
                    entry_price = self.market.get_current_close(asset_id) or 0.0
                    self.pending_signal = None
                    return InferenceResult(state=ScreenState.GATINHO_CALL, confidence=1.0,
                                           recommended_action="CLICK_ACIMA",
                                           details={"asset_id": asset_id, "entry_price": entry_price})
                if direction == "PUT" and candle_color == "RED":
                    print("✅ ALINHAMENTO TOTAL! Disparando ABAIXO!")
                    entry_price = self.market.get_current_close(asset_id) or 0.0
                    self.pending_signal = None
                    return InferenceResult(state=ScreenState.GATINHO_PUT, confidence=1.0,
                                           recommended_action="CLICK_ABAIXO",
                                           details={"asset_id": asset_id, "entry_price": entry_price})
            return InferenceResult(state=ScreenState.ARMED, confidence=0.8, recommended_action="WAIT")

        # ========== ESTRATÉGIA FIRST TOUCH COMMAND ==========
        # 1) Detectar Velas de Comando (vela anterior já fechada)
        history_o = self.market.assets[asset_id]["history_o"] if asset_id in self.market.assets else []
        history_c = self.market.assets[asset_id]["history_c"] if asset_id in self.market.assets else []
        history_h = self.market.assets[asset_id]["history_h"] if asset_id in self.market.assets else []
        history_l = self.market.assets[asset_id]["history_l"] if asset_id in self.market.assets else []

        if len(history_o) >= 2 and len(history_c) >= 2:
            prev_open = history_o[-2]
            prev_close = history_c[-2]
            prev_high = history_h[-2] if len(history_h) >= 2 else prev_open
            prev_low = history_l[-2] if len(history_l) >= 2 else prev_open

            is_bullish = prev_close > prev_open
            is_bearish = prev_close < prev_open

            # Vela de Comando de Alta (bull_command: open == low and close > open)
            if is_bullish and prev_low == prev_open:
                self.first_touch.add_zone(prev_open, 'SUPPORT', 'VERDE')
                print(f"📊 [VELA DE COMANDO] Alta -> Suporte em {prev_open:.5f}")

            # Vela de Comando de Baixa (bear_command: open == high and close < open)
            if is_bearish and prev_high == prev_open:
                self.first_touch.add_zone(prev_open, 'RESISTANCE', 'VERMELHA')
                print(f"📊 [VELA DE COMANDO] Baixa -> Resistência em {prev_open:.5f}")

        # 2) Verificar first touch nas zonas ativas
        current_price = self.market.get_current_close(asset_id)
        if current_price:
            # LOG DE MONITORAMENTO (distância) - será chamado a cada ciclo do alpha engine
            for zone in self.first_touch.get_active_zones():
                diff = abs(current_price - zone['level'])
                logger.info(f"[TRACKER] 🔍 Monitorando: Preço Atual: {current_price:.5f} | Alvo: {zone['level']:.5f} | Distância: {diff:.5f} pips")
            touch_signal = self.first_touch.update(current_price)
            if touch_signal:
                print(f"🔁 [FIRST TOUCH] Sinal: {touch_signal}")
                self.pending_signal = {
                    "asset_id": asset_id,
                    "direction": touch_signal,
                    "name": "FIRST_TOUCH",
                    "timestamp": time.time(),
                    "required_ticks": 0
                }
                return InferenceResult(state=ScreenState.ARMED, confidence=0.9, recommended_action="WAIT")
        # ========================================================

        # Se não houver sinal de first touch, tenta outras estratégias (OCR + matemática)
        visual_dir, raw_text, x_center = self._extract_visual_signal(page)
        if visual_dir is None:
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=1.0, recommended_action="WAIT")

        print(f"🔍 OCR detectou: {visual_dir} (texto='{raw_text}')")

        # Filtros de suporte/resistência e tendência
        history = self.market.get_history(asset_id)
        current_price = self.market.get_current_close(asset_id)
        if current_price and len(history) >= 10:
            resistencia = max(history[-10:])
            suporte = min(history[-10:])
            range_total = resistencia - suporte
            if range_total > 0:
                if current_price >= resistencia - (range_total * 0.2):
                    print(f"🛡️ Preço colado na RESISTÊNCIA! Forçando PUT.")
                    visual_dir = "PUT"
                elif current_price <= suporte + (range_total * 0.2):
                    print(f"🛡️ Preço colado no SUPORTE! Forçando CALL.")
                    visual_dir = "CALL"
            self.market.market_structure.update(max(history[-2:]), min(history[-2:]), current_price)
            tendencia = self.market.market_structure.get_trend_description()
            if tendencia == "ALTA" and visual_dir == "PUT":
                print(f"📉 TENDÊNCIA CONTRÁRIA: Ignorando PUT.")
                return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
            if tendencia == "BAIXA" and visual_dir == "CALL":
                print(f"📈 TENDÊNCIA CONTRÁRIA: Ignorando CALL.")
                return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")

        quant_dir, quant_name = self.market.evaluate_scripts(asset_id)
        if quant_dir is None:
            print(f"🚫 SINAL VISUAL IGNORADO: Matemática não confirmou ({quant_name})")
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
        if quant_dir != visual_dir:
            print(f"⚠️ FALSO POSITIVO: OCR viu {visual_dir}, Matemática {quant_dir}.")
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
        print(f"✅ CONFIRMAÇÃO HÍBRIDA: OCR ({visual_dir}) + Math ({quant_name}) alinhados!")
        self.last_signal = visual_dir
        self.pending_signal = {
            "asset_id": asset_id,
            "direction": visual_dir,
            "name": quant_name,
            "timestamp": time.time()
        }
        if quant_name == "FLASH":
            print("⚡ SINAL FLASH ARMADO.")
        else:
            print(f"🔫 SINAL {quant_name} ARMADO.")
        return InferenceResult(state=ScreenState.ARMED, confidence=0.9, recommended_action="WAIT")

    def _detect_posicao_aberta(self, html_str: str) -> bool:
        m = re.search(r'Op[çõesçõe]es\s*\((\d+)\)', html.unescape(html_str), re.IGNORECASE)
        return int(m.group(1)) > 0 if m else False

    def filtro_justiceiro_pavio(self, candle):
        tamanho_total = abs(candle['high'] - candle['low'])
        pavio_superior = candle['high'] - max(candle['open'], candle['close'])
        pavio_inferior = min(candle['open'], candle['close']) - candle['low']
        if self.last_signal == "PUT" and pavio_superior > (tamanho_total * 0.3):
            return True, "REJEICAO_ALTA_CONFIRMADA"
        if self.last_signal == "CALL" and pavio_inferior > (tamanho_total * 0.3):
            return True, "REJEICAO_BAIXA_CONFIRMADA"
        return False, "SEM_REJEICAO_SUFICIENTE"


# ============================================================
# 4. MICRO: EXECUTOR DE AÇÕES
# ============================================================
class ActionExecutor:
    def __init__(self, page: Page, coord_acima=(1221, 375), coord_abaixo=(1208, 483)):
        self.page = page
        self.coord_acima = coord_acima
        self.coord_abaixo = coord_abaixo
        self._at_work = False
        self._timeframe_set = False

    def execute(self, result: InferenceResult):
        if result.recommended_action == "CLICK_ACIMA":
            return self._click(self.coord_acima, "BUY")
        if result.recommended_action == "CLICK_ABAIXO":
            return self._click(self.coord_abaixo, "SELL")
        return {"ok": True, "action_taken": "WAIT"}

    def _set_timeframe_m1(self):
        try:
            m1_selector = "button[data-value='1']"
            if self._timeframe_set:
                return
            dropdown = self.page.query_selector(".timeframe-selector")
            if dropdown:
                dropdown.click()
                time.sleep(0.3)
            m1_button = self.page.query_selector(m1_selector)
            if m1_button:
                m1_button.click()
                time.sleep(0.2)
                self._timeframe_set = True
                logger.info("⏱️ Timeframe ajustado para 1 Minuto (M1)")
        except Exception as e:
            logger.warning(f"Falha ao ajustar timeframe M1: {e}")

    def _click(self, coord, type):
        if self._at_work:
            print("⚠️ BLOQUEIO: Já existe uma operação em curso.")
            return {"ok": False, "error": "Already at work"}
        try:
            self._at_work = True
            self._set_timeframe_m1()
            self.page.bring_to_front()
            self.page.mouse.click(coord[0], coord[1])
            time.sleep(0.1)
            # LOG DE EXECUÇÃO
            logger.info(f"[✅ EXECUÇÃO] Ordem enviada com sucesso. Maratona de zona encerrada (First Touch).")
            return {"ok": True, "action_taken": f"{type}_EXECUTED"}
        finally:
            self._at_work = False


# ============================================================
# 5. ORQUESTRADOR: ALPHA ENGINE
# ============================================================
class AlphaEngine:
    def __init__(self):
        self.classifier = QuantClassifier()
        self._active_page = None
        self._cycle_count = 0
        self._last_result = None
        self._trade_in_progress = False
        self._trade_start_time = 0.0
        self._cooldown_until = 0.0
        self._stop_requested = False
        self._lock = threading.Lock()
        self.historico_velas = []
        self.last_candle_time = 0
        self.risk = RiskConfig()
        self.manager = StrategicManager()
        self.broker_ops = None
        self.last_trade_time = 0
        self.cooldown_period = 10
        self._consecutive_losses = 0
        self.CIRCUIT_BREAKER_LIMIT = 3
        self.CIRCUIT_PAUSE_SECONDS = 180.0
        self._trade_entry_price = 0.0
        self._trade_direction = ""
        self._trade_asset_id = None
        self._balance_before = 0.0
        self._at_work = False

    def _calculate_final_pnl(self, entry_price, exit_price, side):
        if side == 'BUY':
            return exit_price - entry_price
        elif side == 'SELL':
            return entry_price - exit_price
        return 0

    def get_balance(self):
        if not self._active_page:
            return None
        try:
            html = self._active_page.content()
            m = re.search(r'Saldo:\s*\$?([0-9,]+\.[0-9]+)', html, re.IGNORECASE)
            if m:
                return float(m.group(1).replace(',', ''))
            return None
        except:
            return None

    def process_trade_result(self, amount_invested):
        time.sleep(0.5)
        current_balance = self.get_balance()
        if current_balance is None or self._balance_before is None:
            return "UNKNOWN", 0.0
        pnl = current_balance - self._balance_before
        if current_balance < self._balance_before:
            logger.error(f"❌ LOSS: Antes ${self._balance_before} | Depois ${current_balance}")
            return "LOSS", pnl
        elif current_balance > self._balance_before:
            logger.info(f"✅ WIN: Antes ${self._balance_before} | Depois ${current_balance}")
            return "WIN", pnl
        else:
            return "TIE", pnl

    def attach(self, page: Page):
        self._active_page = page

    def process_network_packet(self, payload: str):
        self.classifier.process_network_packet(payload)

    def request_stop(self):
        with self._lock:
            self._stop_requested = True

    def perceive_and_act(self) -> Dict:
        with self._lock:
            if self._stop_requested:
                self._stop_requested = False
                return {"cycle_id": str(self._cycle_count), "state": ScreenState.IDLE, "recommended_action": "WAIT"}
            cooldown = self._cooldown_until
            trade_was_active = self._trade_in_progress
            trade_start_time = self._trade_start_time

        if time.time() < cooldown:
            return {"cycle_id": "WAIT", "state": ScreenState.COOLDOWN, "recommended_action": "WAIT"}

        if trade_was_active:
            time_in_trade = time.time() - trade_start_time
            if time_in_trade < 8.0:
                return {"cycle_id": str(self._cycle_count), "state": ScreenState.POSITION_OPEN,
                        "recommended_action": "WAITING_RESULT"}

        self._cycle_count += 1
        balance_pre = self.get_balance()
        inf = self.classifier.classify(self._active_page)
        self._last_result = inf

        if trade_was_active:
            if inf.state != ScreenState.POSITION_OPEN:
                with self._lock:
                    trade_dir = self._trade_direction
                    trade_entry = self._trade_entry_price
                    trade_asset = self._trade_asset_id
                    bal_before = self._balance_before
                result, pnl = self.process_trade_result(0)
                with self._lock:
                    if result == "WIN":
                        self.manager.registrar_resultado("WIN")
                        self._consecutive_losses = 0
                        self._cooldown_until = time.time() + 5.0
                    elif result == "LOSS":
                        self.manager.registrar_resultado("LOSS")
                        self._consecutive_losses = self.manager.losses_seguidas
                        if self.manager.losses_seguidas >= self.CIRCUIT_BREAKER_LIMIT:
                            print(f"🛑 CIRCUIT BREAKER! {self.CIRCUIT_BREAKER_LIMIT} perdas consecutivas.")
                            print(f"Pausa de {self.CIRCUIT_PAUSE_SECONDS}s")
                            self._cooldown_until = time.time() + self.CIRCUIT_PAUSE_SECONDS
                        else:
                            self._cooldown_until = time.time() + 5.0
                    elif result == "TIE":
                        self._cooldown_until = time.time() + 5.0
                    else:
                        exit_price = self.classifier.market.get_current_close(trade_asset)
                        if exit_price is None:
                            exit_price = self.classifier.market.get_current_close(self.classifier._last_asset_id) or 0.0
                        is_win = (trade_dir == "CLICK_ACIMA" and exit_price > trade_entry) or \
                                 (trade_dir == "CLICK_ABAIXO" and exit_price < trade_entry)
                        if is_win:
                            self.manager.registrar_resultado("WIN")
                            self._consecutive_losses = 0
                            self._cooldown_until = time.time() + 2.0
                            print(f"\n✅ WIN: Entrada {trade_entry:.5f} | Saída {exit_price:.5f}")
                        else:
                            self.manager.registrar_resultado("LOSS")
                            self._consecutive_losses = self.manager.losses_seguidas
                            print(f"\n❌ LOSS: Entrada {trade_entry:.5f} | Saída {exit_price:.5f}")
                            if self.manager.losses_seguidas >= self.CIRCUIT_BREAKER_LIMIT:
                                print(f"🛑 CIRCUIT BREAKER!")
                                self._cooldown_until = time.time() + self.CIRCUIT_PAUSE_SECONDS
                            else:
                                self._cooldown_until = time.time() + 5.0
                        pnl = self._calculate_final_pnl(trade_entry, exit_price, 'BUY' if trade_dir == "CLICK_ACIMA" else 'SELL')
                    self.risk.update_result(pnl)
                    if self.broker_ops:
                        log_data = {
                            "sinal_visual": self._trade_direction,
                            "estrategia": getattr(self, "_trade_signal_name", "N/A"),
                            "direcao": self._trade_direction,
                            "entry_price": trade_entry,
                            "exit_price": self.classifier.market.get_current_close(trade_asset) or 0.0,
                            "balance_before": bal_before,
                            "balance_after": current_balance,
                            "status": result
                        }
                        self.broker_ops.save_transaction_log(log_data)
                    atualizar_painel_visual(self.manager)
                    self._trade_in_progress = False
                    self._trade_asset_id = None
                    self._at_work = False
                status_hud = f"{ScreenState.COOLDOWN} | {self.manager.wins}W - {self.manager.losses}L"
                return {"cycle_id": str(self._cycle_count), "state": status_hud, "action_result": {"ok": True}}
            return {"cycle_id": str(self._cycle_count), "state": inf.state, "recommended_action": "WAITING_RESULT"}

        if inf.state == ScreenState.POSITION_OPEN:
            with self._lock:
                self._trade_in_progress = True
            return {"cycle_id": str(self._cycle_count), "state": inf.state, "recommended_action": "WAITING_RESULT"}

        res = ActionExecutor(self._active_page).execute(inf)
        if "EXECUTED" in res.get("action_taken", ""):
            with self._lock:
                asset_id = inf.details.get("asset_id", self.classifier._last_asset_id)
                self._trade_in_progress = True
                self._trade_start_time = time.time()
                self._trade_entry_price = inf.details.get("entry_price") or \
                                          self.classifier.market.get_current_close(asset_id) or 0.0
                self._trade_direction = inf.recommended_action
                self._trade_asset_id = asset_id
                self._balance_before = self.get_balance()
                self._at_work = True

        score_str = f"{self.manager.wins}W - {self.manager.losses}L"
        display_state = f"{inf.state} | {score_str}"
        return {"cycle_id": str(self._cycle_count), "state": display_state, "action_result": res}

    def get_status(self) -> Dict:
        with self._lock:
            if not self._last_result:
                return {"status": "IDLE"}
            score_str = f"{self.manager.wins}W - {self.manager.losses}L"
            display_state = f"{self._last_result.state} | {score_str}"
            return {"status": "ACTIVE", "last_state": display_state}


alpha_engine = AlphaEngine()

class BreakoutAnalyzer:
    @staticmethod
    def is_valid_breakout(history_c, current_price, direction):
        if len(history_c) < 5:
            return False
        high_zone = max(history_c[-5:-1])
        low_zone = min(history_c[-5:-1])
        if direction == "CALL":
            return current_price > high_zone and (current_price - high_zone) > 0.0001
        elif direction == "PUT":
            return current_price < low_zone and (low_zone - current_price) > 0.0001
        return False

# ============================================================
# NÚCLEO ESTRATÉGICO (mantido para compatibilidade)
# ============================================================
class StrategicManager:
    def __init__(self):
        self.stop_loss_diario = 2
        self.meta_diaria = 4
        self.wins = 0
        self.losses = 0
        self.losses_seguidas = 0
        
    def registrar_resultado(self, resultado):
        if resultado == "WIN":
            self.wins += 1
            self.losses_seguidas = 0
        else:
            self.losses += 1
            self.losses_seguidas += 1
        
    def check_permitir_operacao(self):
        if self.losses_seguidas >= self.stop_loss_diario:
            return False, "STOP_LOSS"
        if self.wins >= self.meta_diaria:
            return False, "META_BATIDA"
        return True, "OK"

def atualizar_painel_visual(manager):
    placar_str = f"STRIKE: {manager.wins}W - {manager.losses}L"
    print(f"\n[HUD UPDATE] {placar_str} | Sequência Loss: {manager.losses_seguidas}")