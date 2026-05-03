# filename: alpha_module.py
"""
Módulo Alpha v15 – Sistema de classificação quantitativa para opções binárias.
Integra OCR, análise técnica, filtros de S/R, score de sinal e execução.

Autor: R2 Ghost Protocol
Compatível com FastAPI e Playwright.

CHANGELOG v15 – Unificação de pipelines, correções de async/blocking, 
                 histórico baseado em preços reais, proteção anti-overtrade.
"""
import time
import logging
import threading
import re
import html
import urllib.request
import shutil
import os
import asyncio
import csv
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, Any, List, Callable
from enum import Enum
from datetime import datetime, time as dt_time
from playwright.sync_api import Page

import pytesseract
from PIL import Image
import io
logger = logging.getLogger("ModuloAlpha")



# ====================================================================
# CONFIGURAÇÃO CENTRAL (dataclass)
# ====================================================================
@dataclass
class AlphaConfig:
    """Parâmetros configuráveis do motor Alpha."""
    candle_period_seconds: int = 5
    asset_price_min: float = 0.0
    asset_price_max: float = 99999.0
    circuit_breaker_limit: int = 3
    circuit_pause_seconds: float = 30.0
    signal_score_threshold: int = 55   # BUG #5: aumentado para exigir DUPLA_CONFIRMACAO (60)
    news_update_interval: int = 60
    ocr_signal_cache_ttl: float = 8.0
    blocked_windows_brt: list = field(default_factory=lambda: [
        ("09:25", "09:35"),   # Abertura NY
        ("13:55", "14:05"),   # FOMC / dados EUA
        ("15:25", "15:35")    # Fechamento Europa
    ])  # MELHORIA #4 ativada
    trade_log_file: str = "trades_log.csv"
    sr_lookback_periods: tuple = (10, 30, 60, 100)
    sr_tolerance: float = 0.0005  # 0.05%
    analysis_window: int = 10     # Analisar 10 velas
    min_pattern_strength: float = 0.7  # 70% de concordância nas últimas 5 velas (para teste)
    tesseract_cmd: str = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    min_cooldown_between_trades_seconds: float = 30.0  # MELHORIA #8: cooldown mínimo

    def __post_init__(self):
        logger.info(f"[AlphaConfig] Configuração carregada: candle_period={self.candle_period_seconds}s, "
                    f"circuit_breaker_limit={self.circuit_breaker_limit}, score_threshold={self.signal_score_threshold}, "
                    f"analysis_window={self.analysis_window}, min_pattern_strength={self.min_pattern_strength}, "
                    f"cooldown_min={self.min_cooldown_between_trades_seconds}s")

# ====================================================================
# AUXILIARES: SESSION FILTER
# ====================================================================
class SessionFilter:
    """Bloqueia operações em janelas de notícias econômicas (horário BRT)."""
    def __init__(self, blocked_windows: List[Tuple[str, str]], disabled: bool = False):
        self.windows = [(dt_time.fromisoformat(s), dt_time.fromisoformat(e))
                        for s, e in blocked_windows]
        self.disabled = disabled # Nova flag para desativar o filtro
        logger.info(f"[SessionFilter] Inicializado com {len(self.windows)} janelas bloqueadas.")

    def is_blocked(self) -> bool:
        now = datetime.now().time()
        if self.disabled: # Se o filtro estiver desativado, nunca bloqueia
            return False
        for start, end in self.windows:
            if start <= now <= end:
                logger.debug(f"[SessionFilter] Horário bloqueado: {now} entre {start} e {end}")
                return True
        return False

# ====================================================================
# FILTRO DE ZONA S/R (Suporte/Resistência) – com cache atualizável
# ====================================================================
class SRZoneTracker:
    """Calcula níveis de suporte/resistência a partir do histórico de preços."""
    def __init__(self, lookback_periods: Tuple[int, ...] = (10, 30, 60, 100)):
        self.periods = lookback_periods
        self._levels_cache: Dict[int, Tuple[float, float]] = {}
        self.history: List[float] = []
        logger.debug(f"[SRZoneTracker] Inicializado, períodos={self.periods}")

    def update_history(self, history: List[float]):
        self.history = history
        self._levels_cache.clear()
        logger.debug(f"[SRZoneTracker] Histórico atualizado com {len(history)} preços")

    def _get_levels_for_period(self, period: int) -> Tuple[float, float]:
        if period in self._levels_cache:
            return self._levels_cache[period]
        if len(self.history) < period:
            logger.debug(f"[SRZoneTracker] Período {period} solicitado mas histórico insuficiente ({len(self.history)})")
            return (0.0, 0.0)
        recent = self.history[-period:]
        high = max(recent)
        low = min(recent)
        self._levels_cache[period] = (high, low)
        logger.debug(f"[SRZoneTracker] Período {period}: High={high:.5f}, Low={low:.5f}")
        return high, low

    def get_all_levels(self) -> List[float]:
        levels = []
        for p in self.periods:
            high, low = self._get_levels_for_period(p)
            levels.append(high)
            levels.append(low)
        return levels

    def is_near_resistance(self, price: float, tolerance: float = None) -> bool:
        if tolerance is None:
            tolerance = 0.0005
        for p in self.periods:
            high, _ = self._get_levels_for_period(p)
            if high == 0:
                continue
            if abs(price - high) / price < tolerance:
                logger.debug(f"[SRZoneTracker] Preço {price:.5f} próximo da resistência {high:.5f} (período {p})")
                return True
        return False

    def is_near_support(self, price: float, tolerance: float = None) -> bool:
        if tolerance is None:
            tolerance = 0.0005
        for p in self.periods:
            _, low = self._get_levels_for_period(p)
            if low == 0:
                continue
            if abs(price - low) / price < tolerance:
                logger.debug(f"[SRZoneTracker] Preço {price:.5f} próximo do suporte {low:.5f} (período {p})")
                return True
        return False

# ====================================================================
# SCORE DE QUALIDADE DO SINAL (com suporte a pattern_strength)
# ====================================================================
class SignalScore:
    def __init__(self, direction: str, signal_name: str, news_sentiment: str,
                 near_resistance: bool, near_support: bool, pattern_strength: float = 0.0,
                 is_flash: bool = False):
        self.direction = direction          # "CALL" ou "PUT"
        self.signal_name = signal_name
        self.news_sentiment = news_sentiment
        self.near_resistance = near_resistance
        self.near_support = near_support
        self.pattern_strength = pattern_strength
        self.is_flash = is_flash
        self.score = self._compute()
        logger.debug(f"[SignalScore] direction={direction}, signal={signal_name}, news={news_sentiment}, "
                     f"near_res={near_resistance}, near_sup={near_support}, pattern_strength={pattern_strength:.2f}, "
                     f"is_flash={is_flash} -> score={self.score}")

    def _compute(self) -> int:
        base = 0
        if self.signal_name in ("JustWin_Solo", "GenInd_Solo"):
            base = 40
        elif self.signal_name == "DUPLA_CONFIRMACAO":
            base = 60
        elif self.signal_name == "TRIPLE_CONFIRMACAO":
            base = 80
        # Ajuste por sentimento de notícias
        if self.direction == "CALL" and self.news_sentiment == "BULLISH_USD":
            base += 10
        elif self.direction == "PUT" and self.news_sentiment == "BEARISH_USD":
            base += 10
        elif (self.direction == "CALL" and self.news_sentiment == "BEARISH_USD") or \
             (self.direction == "PUT" and self.news_sentiment == "BULLISH_USD"):
            base -= 15
        # Penalidade por proximidade de zonas contrárias
        if self.direction == "CALL" and self.near_resistance:
            base -= 20
        if self.direction == "PUT" and self.near_support:
            base -= 20
        # Bônus para padrão forte (MELHORIA #7)
        if self.pattern_strength >= 0.8:
            base += 15
        elif self.pattern_strength >= 0.7:
            base += 8
        # Bônus para sinal FLASH
        if self.is_flash:
            base += 10
        return max(0, min(100, base))

# ====================================================================
# RADAR GEOPOLÍTICO (com flag de stale e keywords em inglês)
# ====================================================================
class NewsSentimentAnalyzer:
    def __init__(self, update_interval: int = 60):
        self.current_sentiment = "NEUTRAL"
        self.bullish_score = 0
        self.bearish_score = 0
        self.last_update = 0.0
        self.last_successful_update = 0.0
        self.update_interval = update_interval
        self._lock = threading.Lock()
        logger.info(f"[NewsAnalyzer] Inicializado com intervalo de {update_interval}s")

    def get_sentiment(self) -> str:
        now = time.time()
        if now - self.last_update > self.update_interval:
            logger.debug("[NewsAnalyzer] Disparando atualização de notícias (assíncrono)")
            threading.Thread(target=self._fetch_news, daemon=True).start()
            self.last_update = now
        # Se os dados estiverem muito antigos (>5 min), tratar como NEUTRAL
        if self.is_stale(max_age_seconds=300):
            return "NEUTRAL"
        with self._lock:
            logger.debug(f"[NewsAnalyzer] Sentimento atual: {self.current_sentiment}")
            return self.current_sentiment

    def get_scores(self) -> Tuple[int, int]:
        with self._lock:
            return (self.bullish_score, self.bearish_score)

    def is_stale(self, max_age_seconds: int = 300) -> bool:
        stale = (time.time() - self.last_successful_update) > max_age_seconds
        if stale:
            logger.warning(f"[NewsAnalyzer] Dados desatualizados (última atualização há {time.time()-self.last_successful_update:.0f}s)")
        return stale

    def _fetch_news(self):
        try:
            logger.info("[NewsAnalyzer] Buscando notícias econômicas...")
            url = "https://news.google.com/rss/search?q=dolar+real+eua+brasil+geopolitica+economia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=10)
            xml_data = response.read().decode('utf-8', errors='ignore')
            titulos = re.findall(r'<title>(.*?)</title>', xml_data)
            bullish_usd = 0
            bearish_usd = 0
            bull_keywords_pt = ['alta', 'sobe', 'avança', 'tensão', 'guerra', 'conflito', 'juros eua', 'fuga', 'risco']
            bull_keywords_en = ['high', 'rises', 'tension', 'conflict', 'hawkish', 'surge']
            bear_keywords_pt = ['cai', 'recua', 'baixa', 'corte', 'estabilidade', 'acordo', 'paz', 'trégua', 'alívio']
            bear_keywords_en = ['falls', 'drops', 'cut', 'stable', 'peace', 'dovish']
            all_bull = bull_keywords_pt + bull_keywords_en
            all_bear = bear_keywords_pt + bear_keywords_en
            for t in titulos[1:25]:
                t_lower = t.lower()
                if any(k in t_lower for k in all_bull):
                    bullish_usd += 1
                elif any(k in t_lower for k in all_bear):
                    bearish_usd += 1
            with self._lock:
                self.bullish_score = bullish_usd
                self.bearish_score = bearish_usd
                if bullish_usd > bearish_usd + 1:
                    self.current_sentiment = "BULLISH_USD"
                elif bearish_usd > bullish_usd + 1:
                    self.current_sentiment = "BEARISH_USD"
                else:
                    self.current_sentiment = "NEUTRAL"
                self.last_successful_update = time.time()
            logger.info(f"[NewsAnalyzer] Resultado: Força Dólar={bullish_usd}, Fraqueza={bearish_usd} → {self.current_sentiment}")
        except Exception as e:
            logger.error(f"[NewsAnalyzer] Falha ao buscar notícias: {e}")

# ====================================================================
# TRACKER DE MERCADO (cálculos quantitativos)
# ====================================================================
class MarketTracker:
    def __init__(self, config: AlphaConfig):
        self.config = config
        self.assets: Dict[int, Dict[str, Any]] = {} # {asset_id: state}
        self._lock = threading.Lock()
        self._pattern_history: List[float] = [] # Armazena apenas closes para cálculo de padrão
        logger.info("[MarketTracker] Inicializado")

    def _init_asset_state(self, asset_id: int) -> Dict[str, Any]:
        logger.debug(f"[MarketTracker] Novo ativo {asset_id} inicializado")
        return {
            "history_c": [],
            "history_o": [],
            "candles": [],          # lista de (open, close, candle_time)
            "current_open": None,
            "current_close": None,
            "last_candle_time": None,
            "consecutive_ticks": 0,
            "last_color_state": "UNKNOWN",
        }

    def update_robust(self, asset_id: int, op: float, cl: float, candle_time: int) -> bool:
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
                if state["current_close"] is not None and state["current_open"] is not None:
                    state["candles"].append((state["current_open"], state["current_close"], state["last_candle_time"]))
                    if len(state["candles"]) > 150:
                        state["candles"].pop(0)
                    # Atualiza padrão global (para o ativo principal, asset_id=1)
                    self._pattern_history = [c for _, c, _ in state["candles"][-self.config.analysis_window:]]
                state["last_candle_time"] = candle_time
                state["current_open"] = op
                is_new_candle = True
                logger.debug(f"[MarketTracker] Nova vela para ativo {asset_id}: open={op:.5f}, close={cl:.5f}")
            if state["current_open"] is None:
                state["current_open"] = op
            state["current_close"] = cl
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
            # Retorna o último close do último candle
            if self.assets[asset_id]["candles"]:
                return self.assets[asset_id]["candles"][-1][1]
            return None

    def get_history_len(self, asset_id: int) -> int:
        with self._lock:
            if asset_id not in self.assets:
                return 0
            return len(self.assets[asset_id]["candles"])

    def get_history(self, asset_id: int) -> List[float]:
        with self._lock:
            if asset_id not in self.assets:
                return []
            return [c for _, c, _ in self.assets[asset_id]["candles"]]

    def calculate_pattern_strength(self) -> float:
        """
        Calcula a força do padrão nas últimas N velas (baseado em preços reais).
        Retorna proporção de candles verdes (alta) ou vermelhos (baixa) conforme dominância.
        """
        if len(self._pattern_history) < 2: # Precisa de pelo menos 2 candles para ter open/close
            return 0.0
        
        # O _pattern_history já é uma lista de closes.
        # Para calcular a cor, precisamos do open e close de cada candle.
        # Vamos usar a lista 'candles' do ativo 1, que contém (open, close, time).
        with self._lock:
            if 1 not in self.assets:
                return 0.0
            
            candles = self.assets[1]["candles"]
            if len(candles) < self.config.analysis_window:
                return 0.0
            
            recent_candles = candles[-self.config.analysis_window:]
            
            greens = sum(1 for o, c, _ in recent_candles if c > o)
            reds = self.config.analysis_window - greens
            strength = max(greens, reds) / self.config.analysis_window
            logger.debug(f"[MarketTracker] Padrão: greens={greens}, reds={reds}, strength={strength:.2f}")
            return strength

    def evaluate_scripts(self, asset_id: int, sr_tracker) -> Tuple[Optional[str], str, float]:
        """
        Retorna (direção, nome_sinal, score_bruto) baseado em indicadores.
        """
        with self._lock:
            if asset_id not in self.assets:
                return (None, "NO_DATA", 0.0)
            state = self.assets[asset_id]
            
            # Usar a nova estrutura 'candles'
            candles = state["candles"]
            if len(candles) < 20:
                return (None, "INSUFFICIENT_DATA", 0.0)

            # Extrair closes e opens para cálculos
            closes = [c for _, c, _ in candles[-30:]]
            opens = [o for o, _, _ in candles[-30:]]

            ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else closes[-1]
            ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else closes[-1]
            current_price = closes[-1]

            tendencia_alta = (ma5 > ma10) and (current_price > ma5)
            tendencia_baixa = (ma5 < ma10) and (current_price < ma5)

            # RSI simplificado (14 períodos)
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else sum(gains)/len(gains) if gains else 0
            avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else sum(losses)/len(losses) if losses else 0
            rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))

            if tendencia_alta and rsi < 70:
                direction = "CALL"
                signal_name = "JustWin_Solo"
                strength = 0.7
            elif tendencia_baixa and rsi > 30:
                direction = "PUT"
                signal_name = "JustWin_Solo"
                strength = 0.7
            else:
                return (None, "NEUTRAL", 0.0)

            pattern_strength = self.calculate_pattern_strength()
            if pattern_strength >= 0.8:
                signal_name = "DUPLA_CONFIRMACAO"
                strength = pattern_strength

            return (direction, signal_name, strength)

# ====================================================================
# CLASSIFICADOR QUANTITATIVO + OCR (com cache de sinal e pipeline unificada)
# ====================================================================
class QuantClassifier:
    def __init__(self, config: AlphaConfig):
        self.config = config
        self.pending_signal = None
        self._data_lock = threading.Lock()
        self.candle_maturity_delay = 0.0
        self.signal_timeout = config.candle_period_seconds * 2.5
        self.news_analyzer = NewsSentimentAnalyzer(update_interval=config.news_update_interval)
        self.market = MarketTracker(config=config)
        self._last_asset_id = 1
        self._last_ocr_scan_time = 0.0
        self.OCR_SCAN_INTERVAL = 0.0
        self._ocr_error_logged = False
        self._last_warmup_log = 0.0
        self._system_armed_logged = False
        self.news_analyzer.get_sentiment()
        # Cache de sinal OCR
        if self.config.tesseract_cmd and os.path.exists(self.config.tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd
            logger.info(f"[OCR] Tesseract configurado: {self.config.tesseract_cmd}")
        else:
            logger.warning(f"[OCR] Tesseract não encontrado em {self.config.tesseract_cmd}. Verifique o caminho.")
        self._signal_cache = {"direction": None, "x_center": None, "timestamp": 0.0}
        # SRZoneTracker como atributo persistente
        self.sr_tracker = SRZoneTracker(config.sr_lookback_periods)
        logger.info("[QuantClassifier] Inicializado")

    def _is_signal_cached(self, direction: str, x_center: int) -> bool:
        now = time.time()
        cached = (self._signal_cache["direction"] == direction and
                  self._signal_cache["x_center"] == x_center and
                  now - self._signal_cache["timestamp"] < self.config.ocr_signal_cache_ttl)
        if cached:
            logger.debug(f"[OCR Cache] Sinal {direction} na posição {x_center} ainda em cache (TTL ativo)")
        return cached

    def _update_signal_cache(self, direction: str, x_center: int):
        self._signal_cache = {"direction": direction, "x_center": x_center, "timestamp": time.time()}
        logger.debug(f"[OCR Cache] Sinal armazenado: {direction} @ x={x_center}")

    async def _extract_visual_signal(self, page: Page) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        now = time.time()
        if now - self._last_ocr_scan_time < self.OCR_SCAN_INTERVAL:
            return None, None, None
        self._last_ocr_scan_time = now
        logger.debug("[OCR] Iniciando captura e reconhecimento...")
        try:
            screenshot_bytes = await page.screenshot(full_page=False)

            def _ocr_work(img_bytes):
                img = Image.open(io.BytesIO(img_bytes))
                width, height = img.size
                crop_x1 = int(width * 0.30)   # antes era 0.50
                crop_x2 = int(width * 0.98)
                crop_y1 = int(height * 0.10)
                crop_y2 = int(height * 0.90)
                if crop_x1 >= crop_x2 or crop_y1 >= crop_y2:
                    logger.debug("[OCR] Região de recorte inválida")
                    return None, None, None
                cropped = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                gray = cropped.convert('L')
                threshold_img = gray.point(lambda p: 255 if p > 150 else 0)
                scale = 2
                new_size = (threshold_img.width * scale, threshold_img.height * scale)
                big_img = threshold_img.resize(new_size, Image.Resampling.LANCZOS)
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÇçÁáÃãÂâÉéÍíÓóÚúÊêÔôÕõ '
                data = pytesseract.image_to_data(big_img, lang='por+eng', config=custom_config, output_type=pytesseract.Output.DICT)
                target_words = {"CALL": "CALL", "COMPRA": "CALL", "PUT": "PUT", "VENDA": "PUT"}
                best_direction = None
                best_text = None
                max_x = -1
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
                    x = data['left'][i]
                    w = data['width'][i]
                    x_center = x + w // 2
                    x_center_orig = x_center // scale + crop_x1
                    if x_center_orig > max_x:
                        max_x = x_center_orig
                        best_direction = direction
                        best_text = text
                return best_direction, best_text, max_x
            best_direction, best_text, max_x = await asyncio.to_thread(_ocr_work, screenshot_bytes)
            if best_direction:
                logger.info(f"[OCR] Texto detectado: '{best_text}' -> {best_direction} (x={max_x})")
                self._ocr_error_logged = False
                if self._is_signal_cached(best_direction, max_x):
                    logger.info("[OCR] Sinal já processado recentemente, ignorando")
                    return None, None, None
                self._update_signal_cache(best_direction, max_x)
                return best_direction, best_text, max_x
        except Exception as e:
            if not self._ocr_error_logged:
                logger.error(f"[OCR] Erro crítico: {e}")
                self._ocr_error_logged = True
            return None, None, None
        logger.debug("[OCR] Nenhum sinal visual detectado")
        return None, None, None

    def process_network_packet(self, payload: str):
        try:
            if len(payload) < 5:
                return
            payload_lower = payload.lower()

            # Captura QUALQUER número decimal com 2-6 casas que apareça após chaves conhecidas
            prices = re.findall(
                r'"(?:close|ask|bid|value|price|rate|c|last|current|quote|val)"\s*:\s*"?([1-9][0-9]*\.[0-9]{2,6})"?',
                payload_lower
            )
            opens = re.findall(
                r'"(?:open|o|from|start|first)"\s*:\s*"?([1-9][0-9]*\.[0-9]{2,6})"?',
                payload_lower
            )

            # Fallback ultra-agressivo: pega qualquer número plausível de preço forex/crypto
            if not prices and not opens:
                # Procura padrões numéricos que parecem preço (ex: 5.23456, 1.09234, 0.8823)
                all_numbers = re.findall(r':\s*"?([0-9]{1,5}\.[0-9]{3,6})"?', payload_lower)
                plausible = [n for n in all_numbers
                             if self.config.asset_price_min <= float(n) <= self.config.asset_price_max]
                if plausible:
                    cl = float(plausible[-1])
                    op = float(plausible[0]) if len(plausible) > 1 else cl
                    if op == cl:
                        return  # sem variação, ignora
                else:
                    return
            else:
                cl = float(prices[-1]) if prices else float(opens[-1])
                op = float(opens[-1]) if opens else cl

            if not (self.config.asset_price_min <= op <= self.config.asset_price_max):
                return

            match_id = re.search(r'"(?:active_id|asset_id|id|symbol_id)"\s*:\s*(\d+)', payload_lower)
            if match_id:
                asset_id = int(match_id.group(1))
                with self._data_lock:
                    self._last_asset_id = asset_id
            else:
                asset_id = self._last_asset_id # Fallback to last known asset_id

            # FORÇAR APENAS O ATIVO QUE VOCÊ QUER (Exemplo: 76 para USD/BRL)
            if asset_id != 76:
                return

            candle_time = int(time.time()) // self.config.candle_period_seconds
            is_new = self.market.update_robust(asset_id, op, cl, candle_time)

            if is_new and asset_id == self._last_asset_id:
                hist = self.market.get_history(asset_id)
                if hist:
                    self.sr_tracker.update_history(hist)

            logger.debug(f"[Packet] Ativo {asset_id}: O={op:.5f} C={cl:.5f}")

        except Exception as e:
            logger.debug(f"[Packet] Erro: {e} | payload[:100]={payload[:100]}")

    async def _detect_posicao_aberta(self, page: Page) -> bool:
        try:
            locator = page.locator("text=/Op[ç]*[ãe]s.*\\(\\d+\\)/i")
            count = await locator.count()
            if count > 0:
                text = await locator.first.text_content()
                if text:
                    match = re.search(r'\((\d+)\)', text)
                    if match and int(match.group(1)) > 0:
                        logger.info(f"[Posição Aberta] Detectada via locator: {text}")
                        return True
            screenshot_bytes = await page.screenshot(full_page=False)

            def _ocr_work(img_bytes):
                img = Image.open(io.BytesIO(img_bytes))
                width, height = img.size
                crop = img.crop((int(width*0.2), int(height*0.8), int(width*0.8), height))
                return pytesseract.image_to_string(crop, lang='por+eng')

            text = await asyncio.to_thread(_ocr_work, screenshot_bytes)
            text_lower = text.lower()

            # NOVA LÓGICA: Verifica se as palavras existem E se NÃO existe a palavra "nenhuma"
            if ("posição" in text_lower or "aberta" in text_lower) and "nenhuma" not in text_lower:
                logger.info(f"[Posição Aberta] Detectada via OCR fallback: {text[:50]}")
                return True
        except Exception as e:
            logger.debug(f"[Posição Aberta] Erro: {e}")
        return False

    async def classify(self, page: Page) -> 'InferenceResult':
        # SessionFilter (horário bloqueado)
        if hasattr(self, 'session_filter') and self.session_filter.is_blocked():
            logger.info("[Classify] Horário bloqueado por SessionFilter → COOLDOWN")
            return InferenceResult(state=ScreenState.COOLDOWN, confidence=0.9, recommended_action="WAIT",
                                   details={"reason": "Horário bloqueado (notícias)"})

        try:
            if await self._detect_posicao_aberta(page):
                self.pending_signal = None
                logger.info("[Classify] Trade em andamento detectado → POSITION_OPEN")
                return InferenceResult(state=ScreenState.POSITION_OPEN, confidence=1.0, recommended_action="WAIT")
        except Exception as e:
            logger.error(f"[Classify] Falha ao detectar posição aberta: {e}")
            return InferenceResult(state=ScreenState.UNKNOWN, recommended_action="ABORT")

        asset_id = self._last_asset_id
        history_len = self.market.get_history_len(asset_id)
        if history_len < 10:
            now = time.time()
            if now - self._last_warmup_log > 5.0:
                logger.info(f"[Classify] Aquecimento: {history_len}/10 velas para ativo {asset_id}")
                self._last_warmup_log = now
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=1.0, recommended_action="WAIT")
        elif not self._system_armed_logged:
            logger.info(f"[Classify] Sistema armado! Ativo {asset_id} pronto para análise.")
            self._system_armed_logged = True

        # Pipeline unificada: verifica sinal pendente -> OCR + quant + score
        # 1. Sinal pendente (confirmado via OCR anterior)
        if self.pending_signal:
            elapsed = time.time() - self.pending_signal["timestamp"]
            if elapsed > self.signal_timeout:
                logger.warning(f"[Classify] Timeout do sinal pendente ({elapsed:.1f}s > {self.signal_timeout}s)")
                self.pending_signal = None
                return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
            if elapsed < self.candle_maturity_delay:
                logger.debug(f"[Classify] Aguardando maturação do candle ({elapsed:.1f}s / {self.candle_maturity_delay}s)")
                return InferenceResult(state=ScreenState.ARMED, confidence=0.8, recommended_action="WAIT")

            asset_id = self.pending_signal["asset_id"]
            direction = self.pending_signal["direction"]
            signal_name = self.pending_signal.get("name", "")
            is_flash = (signal_name == "FLASH")

            if is_flash:
                quant_dir, quant_name, _ = self.market.evaluate_scripts(asset_id, self.sr_tracker)
                if quant_dir != direction or quant_name != "FLASH":
                    logger.warning(f"[Classify] Sinal FLASH expirado: esperado {direction}, obtido {quant_dir}")
                    self.pending_signal = None
                    return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
                logger.info(f"[Classify] FLASH confirmado! Executando ordem imediata.")
                entry_price = self.market.get_current_close(asset_id) or 0.0
                self.pending_signal = None
                return self._create_inference_from_direction(direction, asset_id, entry_price, signal_name, is_flash=True)

            # Para outros sinais: avalia score + cor
            candle_color, ticks_forca = self.market.get_color_ticks(asset_id)
            news_sentiment = self.news_analyzer.get_sentiment()
            hist = self.market.get_history(asset_id)
            pattern_strength = 0.0
            if hist:
                pattern_strength = self.market.calculate_pattern_strength()
            near_res = self.sr_tracker.is_near_resistance(self.market.get_current_close(asset_id) or 0.0, self.config.sr_tolerance) if self.sr_tracker else False
            near_sup = self.sr_tracker.is_near_support(self.market.get_current_close(asset_id) or 0.0, self.config.sr_tolerance) if self.sr_tracker else False

            score_obj = SignalScore(direction, signal_name, news_sentiment, near_res, near_sup, pattern_strength, is_flash=False)
            logger.info(f"[Classify] Sinal pendente {direction} ({signal_name}): score={score_obj.score}, ticks={ticks_forca}, cor={candle_color}, pattern={pattern_strength:.2f}")
            if score_obj.score >= self.config.signal_score_threshold:
                if direction == "CALL" and candle_color == "GREEN":
                    logger.info(f"[Classify] Sinal CALL confirmado por Score e cor verde. Disparando!")
                    entry_price = self.market.get_current_close(asset_id) or 0.0
                    self.pending_signal = None
                    return self._create_inference_from_direction(direction, asset_id, entry_price, signal_name)
                if direction == "PUT" and candle_color == "RED":
                    logger.info(f"[Classify] Sinal PUT confirmado por Score e cor vermelha. Disparando!")
                    entry_price = self.market.get_current_close(asset_id) or 0.0
                    self.pending_signal = None
                    return self._create_inference_from_direction(direction, asset_id, entry_price, signal_name)
            else:
                logger.debug(f"[Classify] Score insuficiente ({score_obj.score} < {self.config.signal_score_threshold})")
            return InferenceResult(state=ScreenState.ARMED, confidence=score_obj.score/100.0, recommended_action="WAIT")

        # 2. Nenhum sinal pendente: OCR + validação quantitativa
        visual_dir, raw_text, x_center = await self._extract_visual_signal(page)
        if visual_dir is None:
            logger.debug("[Classify] Nenhum sinal visual detectado no OCR")
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=1.0, recommended_action="WAIT")

        logger.info(f"[Classify] OCR detectou: {visual_dir} (texto='{raw_text}', x={x_center})")
        quant_dir, quant_name, _ = self.market.evaluate_scripts(asset_id, self.sr_tracker)
        if quant_dir is None:
            logger.info(f"[Classify] Sinal visual ignorado: matemática não confirmou ({quant_name})")
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
        if quant_dir != visual_dir:
            logger.info(f"[Classify] Falso positivo: OCR viu {visual_dir}, matemática aponta {quant_dir}")
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")

        logger.info(f"[Classify] Confirmação híbrida: OCR + Math ({quant_name}) alinhados!")
        self.pending_signal = {
            "asset_id": asset_id,
            "direction": visual_dir,
            "name": quant_name,
            "timestamp": time.time()
        }
        if quant_name == "FLASH":
            logger.info("[Classify] Sinal FLASH armado. Pronto para execução imediata no próximo ciclo.")
        else:
            logger.info(f"[Classify] Sinal {quant_name} armado. Aguardando alinhamento de score.")
        return InferenceResult(state=ScreenState.ARMED, confidence=0.9, recommended_action="WAIT")

    def _create_inference_from_direction(self, direction: str, asset_id: int, entry_price: float,
                                         signal_name: str, is_flash: bool = False) -> 'InferenceResult':
        details = {"asset_id": asset_id, "entry_price": entry_price, "signal_name": signal_name, "flash": is_flash}
        logger.info(f"[Inference] Criando ordem {direction} para ativo {asset_id} a {entry_price:.5f} (sinal={signal_name})")
        if direction == "CALL":
            return InferenceResult(state=ScreenState.GATINHO_CALL, confidence=1.0,
                                   recommended_action="CLICK_ACIMA", details=details)
        else:
            return InferenceResult(state=ScreenState.GATINHO_PUT, confidence=1.0,
                                   recommended_action="CLICK_ABAIXO", details=details)

# ====================================================================
# EXECUTOR DE AÇÕES (apenas para compatibilidade – não usado diretamente para cliques)
# ====================================================================
class ActionExecutor:
    def __init__(self, page: Page, coord_acima=(1221, 375), coord_abaixo=(1208, 483)):
        self.page = page
        self.coord_acima = coord_acima
        self.coord_abaixo = coord_abaixo
        logger.info(f"[ActionExecutor] Coordenadas: CALL={(coord_acima[0], coord_acima[1])}, PUT={(coord_abaixo[0], coord_abaixo[1])}")

    def execute(self, result: 'InferenceResult') -> Dict:
        # Este método não é mais usado para cliques reais (delegado ao BrokerOperator)
        logger.debug("[ActionExecutor] Execução ignorada (cliques delegados ao BrokerOperator)")
        return {"ok": True, "action_taken": "DELEGATED_TO_BROKER"}

# ====================================================================
# ORQUESTRADOR: ALPHA ENGINE (sem cliques, apenas recomendação)
# ====================================================================
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

class AlphaEngine:
    def __init__(self, config: AlphaConfig = None):
        if config is None:
            config = AlphaConfig()
        self.config = config
        self.classifier = QuantClassifier(config) # Inicializa QuantClassifier com a nova config
        self.classifier.session_filter = SessionFilter(config.blocked_windows_brt, disabled=True) # Desativa o filtro de notícias para teste
        self._active_page = None
        self._cycle_count = 0
        self._last_result = None
        self._trade_in_progress = False
        self._trade_start_time = 0.0
        self._cooldown_until = 0.0
        self._stop_requested = False
        self._lock = threading.Lock()
        self._consecutive_losses = 0
        self.CIRCUIT_BREAKER_LIMIT = config.circuit_breaker_limit
        self.CIRCUIT_PAUSE_SECONDS = config.circuit_pause_seconds
        self._trade_entry_price = 0.0
        self._trade_direction = ""
        self._trade_asset_id = None
        self._trade_signal_name = ""
        # Último tempo de trade (para cooldown mínimo)
        self._last_trade_time = 0.0
        logger.info("[AlphaEngine] Inicializado com configuração personalizada (modo recomendação apenas)")

    def attach(self, page: Page):
        self._active_page = page
        logger.info("[AlphaEngine] Página anexada ao motor")

    async def start_trade(self, direction: str, entry_price: float, signal_name: str):
        with self._lock:
            self._trade_in_progress = True
            self._trade_start_time = time.time()
            self._trade_direction = direction
            self._trade_entry_price = entry_price
            self._trade_signal_name = signal_name
            self._trade_asset_id = self.classifier._last_asset_id
        logger.info(f"[AlphaEngine] Trade iniciado: {direction} a {entry_price:.5f} ({signal_name})")

    def process_network_packet(self, payload: str):
        self.classifier.process_network_packet(payload)

    def request_stop(self):
        with self._lock:
            self._stop_requested = True
        logger.info("[AlphaEngine] Solicitação de parada registrada")

    async def perceive_and_act(self) -> Dict:
        """
        Percepção e recomendação (sem executar cliques).
        Retorna um dicionário compatível com o esperado pelo BrokerOperator.
        """
        with self._lock:
            if self._stop_requested:
                self._stop_requested = False
                logger.info("[AlphaEngine] Parada solicitada, retornando IDLE")
                return {"cycle_id": str(self._cycle_count), "state": ScreenState.IDLE, "recommended_action": "WAIT"}
            cooldown = self._cooldown_until
            trade_was_active = self._trade_in_progress
            trade_start_time = self._trade_start_time

        if time.time() < cooldown:
            logger.debug(f"[AlphaEngine] Em cooldown por mais {cooldown - time.time():.1f}s")
            return {"cycle_id": "WAIT", "state": ScreenState.COOLDOWN, "recommended_action": "WAIT"}

        if trade_was_active:
            time_in_trade = time.time() - trade_start_time
            if time_in_trade < 8.0:
                logger.debug(f"[AlphaEngine] Trade ativo há {time_in_trade:.1f}s, aguardando resultado")
                await asyncio.sleep(0.2)  # BUG #3 corrigido: asyncio.sleep
                return {"cycle_id": str(self._cycle_count), "state": ScreenState.POSITION_OPEN,
                        "recommended_action": "WAITING_RESULT"}

        self._cycle_count += 1
        logger.info(f"[AlphaEngine] 🔍 Ciclo #{self._cycle_count} — Analisando ativo {self.classifier._last_asset_id} | Período={self.config.candle_period_seconds}s")

        inf = await self.classifier.classify(self._active_page)
        self._last_result = inf

        if inf.state == ScreenState.GATINHO_CALL or inf.state == ScreenState.GATINHO_PUT:
            # Retorna recomendação, sem executar clique
            logger.info(f"[AlphaEngine] ⚡ RECOMENDAÇÃO: {inf.recommended_action} | Score: {inf.confidence*100:.0f} | Detalhes: {inf.details}")
        elif inf.state == ScreenState.ARMED:
            logger.info("[AlphaEngine] ⏳ Aguardando confirmação dos indicadores...")
        else:
            logger.debug(f"[AlphaEngine] Estado atual: {inf.state}")

        # Gerencia trade em andamento (após execução pelo BrokerOperator)
        if trade_was_active:
            if inf.state != ScreenState.POSITION_OPEN:
                await asyncio.sleep(0.5)
                with self._lock:
                    exit_price = self.classifier.market.get_current_close(self._trade_asset_id)
                    if exit_price is None:
                        exit_price = self.classifier.market.get_current_close(self.classifier._last_asset_id) or 0.0
                    is_win = False
                    if self._trade_direction == "CLICK_ACIMA":
                        is_win = exit_price > self._trade_entry_price
                    elif self._trade_direction == "CLICK_ABAIXO":
                        is_win = exit_price < self._trade_entry_price
                    if is_win:
                        self._consecutive_losses = 0
                        self._cooldown_until = max(time.time() + 5.0,
                                                   self._last_trade_time + self.config.min_cooldown_between_trades_seconds)
                        logger.info(f"[AlphaEngine] ✅ WIN: entry={self._trade_entry_price:.5f} exit={exit_price:.5f}")
                        self._log_trade(win=True, exit_price=exit_price)
                    else:
                        self._consecutive_losses += 1
                        logger.warning(f"[AlphaEngine] ❌ LOSS: entry={self._trade_entry_price:.5f} exit={exit_price:.5f}")
                        self._log_trade(win=False, exit_price=exit_price)
                        if self._consecutive_losses >= self.CIRCUIT_BREAKER_LIMIT:
                            logger.warning(f"[AlphaEngine] Circuit breaker acionado após {self._consecutive_losses} perdas, pausa de {self.CIRCUIT_PAUSE_SECONDS}s")
                            self._cooldown_until = time.time() + self.CIRCUIT_PAUSE_SECONDS
                            self._consecutive_losses = 0
                        else:
                            self._cooldown_until = max(time.time() + 5.0,
                                                       self._last_trade_time + self.config.min_cooldown_between_trades_seconds)
                    self._trade_in_progress = False
                    self._trade_asset_id = None
                    self._last_trade_time = time.time()
                return {"cycle_id": str(self._cycle_count), "state": ScreenState.COOLDOWN, "action_result": {"ok": True}}
            return {"cycle_id": str(self._cycle_count), "state": inf.state, "recommended_action": "WAITING_RESULT"}

        if inf.state == ScreenState.POSITION_OPEN:
            with self._lock:
                self._trade_in_progress = True
            logger.info("[AlphaEngine] Nova posição aberta detectada")
            return {"cycle_id": str(self._cycle_count), "state": inf.state, "recommended_action": "WAITING_RESULT"}

        # Se o classificador retornou um estado que recomenda ação, retornamos a recomendação.
        # A execução real do clique será feita pelo BrokerOperator (execute_safe com base nessa recomendação)
        return {"cycle_id": str(self._cycle_count), "state": inf.state, "recommended_action": inf.recommended_action,
                "confidence": inf.confidence, "details": inf.details}

    def _log_trade(self, win: bool, exit_price: float):
        import csv
        from datetime import datetime
        try:
            with open(self.config.trade_log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if f.tell() == 0:
                    writer.writerow(["timestamp", "asset_id", "direction", "entry_price", "exit_price",
                                     "result", "signal_name", "news_sentiment"])
                writer.writerow([
                    datetime.now().isoformat(),
                    self._trade_asset_id,
                    self._trade_direction,
                    self._trade_entry_price,
                    exit_price,
                    "WIN" if win else "LOSS",
                    self._trade_signal_name,
                    self.classifier.news_analyzer.get_sentiment()
                ])
            logger.info(f"[TradeLog] Trade registrado: {self._trade_signal_name} {self._trade_direction} -> {'WIN' if win else 'LOSS'}")
        except Exception as e:
            logger.error(f"[TradeLog] Erro ao escrever: {e}")

    def get_status(self) -> Dict:
        with self._lock:
            if not self._last_result:
                return {"state": ScreenState.IDLE, "last_state": ScreenState.IDLE, "confidence": 0.0,
                        "last_confidence": 0.0, "recommended_action": "WAIT", "last_action": "WAIT",
                        "cycles": self._cycle_count, "status": "IDLE"}
            return {"state": self._last_result.state, "last_state": self._last_result.state,
                    "confidence": self._last_result.confidence, "last_confidence": self._last_result.confidence,
                    "recommended_action": self._last_result.recommended_action,
                    "last_action": self._last_result.recommended_action,
                    "cycles": self._cycle_count, "status": "ACTIVE"}

    def run_autopilot(self, max_cycles: int = 9999, delay_between: float = 0.5) -> Dict:
        """
        Mantido por compatibilidade, mas o autopilot agora é controlado pelo BrokerOperator.
        """
        logger.warning("[AlphaEngine] run_autopilot chamado, mas o gerenciamento de loop deve ser feito no BrokerOperator")
        return {"ok": False, "msg": "Autopilot deve ser gerenciado pelo BrokerOperator"}

# ====================================================================
# INSTÂNCIA GLOBAL (compatível com main2.py)
# ====================================================================
default_config = AlphaConfig(
    candle_period_seconds=5,
    circuit_breaker_limit=3,
    signal_score_threshold=55
)
alpha_engine = AlphaEngine(config=default_config)
logger.info("Módulo Alpha v15 carregado com pipeline unificada e correções de async")