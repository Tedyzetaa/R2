# filename: alpha_module.py
# ============================================================
# CHANGELOG DE CORREÇÕES — MÓDULO ALPHA (revisão 2026-04-25)
# ============================================================
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔥 CORREÇÃO DO FLASH FALSO (entradas no final da tendência)
#   PROBLEMA: C0 > C1 era muito sensível, causava entradas
#             em ruídos e no final do movimento.
#   FIX: FLASH agora exige rompimento de consolidação:
#        - CALL: C0 > max(últimos 3 closes)
#        - PUT:  C0 < min(últimos 3 closes)
#        - Amplitude mínima de 0.0002 (20 pips)
#        - Bloqueio se movimento já consumiu >70% da amplitude média
#        - Janela reduzida para 1.5 segundos (precisão fracionária)
#
# 🔧 Melhoria: Idade da vela agora usa time.time() com fração
#   para evitar o corte brusco de segundos inteiros.
#
# 🔧 FLASH pendente agora respeita o mesmo filtro de ticks
#   (mas com required_ticks = 0) para garantir condições no clique.
# ============================================================

import time
import logging
import threading
import re
import html
import urllib.request
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, Any
from enum import Enum
from playwright.sync_api import Page

# --- OCR imports ---
import pytesseract
from PIL import Image
import io

logger = logging.getLogger("ModuloAlpha")

# Configuração explícita do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
    def __init__(self):
        self.current_sentiment = "NEUTRAL"
        self.bullish_score = 0
        self.bearish_score = 0
        self.last_update = 0.0
        self.update_interval = 60
        self._lock = threading.Lock()

    def get_sentiment(self) -> str:
        now = time.time()
        if now - self.last_update > self.update_interval:
            threading.Thread(target=self._fetch_news, daemon=True).start()
            self.last_update = now
        with self._lock:
            return self.current_sentiment

    def get_scores(self) -> Tuple[int, int]:
        with self._lock:
            return (self.bullish_score, self.bearish_score)

    def _fetch_news(self):
        try:
            url = "https://news.google.com/rss/search?q=dolar+real+eua+brasil+geopolitica+economia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            response = urllib.request.urlopen(req, timeout=10)
            xml_data = response.read().decode('utf-8', errors='ignore')

            titulos = re.findall(r'<title>(.*?)</title>', xml_data)
            bullish_usd = 0
            bearish_usd = 0

            bull_keywords = ['alta', 'sobe', 'avança', 'tensão', 'guerra', 'conflito', 'juros eua', 'fuga', 'risco',
                             'pressiona', 'dispara']
            bear_keywords = ['cai', 'recua', 'baixa', 'corte', 'estabilidade', 'acordo', 'paz', 'exportação', 'selic',
                             'trégua', 'alívio']

            for t in titulos[1:25]:
                t_lower = t.lower()
                if any(k in t_lower for k in bull_keywords):
                    bullish_usd += 1
                elif any(k in t_lower for k in bear_keywords):
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

            print(f"\n📰 [RADAR GEOPOLÍTICO] Força Dólar: {bullish_usd} | Fraqueza: {bearish_usd} | Viés: {self.current_sentiment}\n")
        except Exception:
            pass


# ============================================================
# 2. MESO: MOTOR QUANTITATIVO AUTO-ADAPTÁVEL
# ============================================================
class MarketTracker:
    def __init__(self):
        self.assets: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _init_asset_state(self, asset_id: int) -> Dict[str, Any]:
        return {
            "history_c": [],
            "history_o": [],
            "last_candle_time": None,
            "current_close": None,
            "current_open": None,
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
                if state["current_close"] is not None:
                    state["history_c"].append(state["current_close"])
                    state["history_o"].append(state["current_open"])
                    if len(state["history_c"]) > 20:
                        state["history_c"].pop(0)
                        state["history_o"].pop(0)
                state["last_candle_time"] = candle_time
                state["current_open"] = op
                is_new_candle = True

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
            return self.assets[asset_id]["current_close"]

    def get_history_len(self, asset_id: int) -> int:
        with self._lock:
            if asset_id not in self.assets:
                return 0
            return len(self.assets[asset_id]["history_c"])

    def evaluate_scripts(self, asset_id: int) -> Tuple[Optional[str], str]:
        # Cópias rasas das listas criadas DENTRO do lock
        with self._lock:
            if asset_id not in self.assets:
                return None, ""
            state = self.assets[asset_id]
            history_c = list(state["history_c"])
            history_o = list(state["history_o"])
            C0 = state["current_close"]
            O0 = state["current_open"]

        if len(history_c) < 10:
            return None, f"MATRIZ_INCOMPLETA: apenas {len(history_c)} velas"

        # ========== IDADE DA VELA (precisão fracionária) ==========
        # Obtém o timestamp atual em fração de segundo
        now = time.time()
        candle_start = (int(now) // 5) * 5
        age_in_seconds = now - candle_start
        # =========================================================

        recent = history_c[-5:]
        amplitude = (max(recent) - min(recent)) / max(recent)
        if amplitude < 0.00008:
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

        # ========== PADRÃO FLASH CORRIGIDO (rompimento de consolidação) ==========
        # Só é válido nos primeiros 1.5 segundos da vela
        if age_in_seconds < 1.5:
            # Para evitar entradas no fim do movimento, verifica se o preço está rompendo uma faixa de consolidação
            # Usa as últimas 3 velas fechadas como referência
            last_3_closes = history_c[-3:]
            range_high = max(last_3_closes)
            range_low = min(last_3_closes)
            range_size = range_high - range_low
            
            # CALL: preço atual acima do ponto mais alto das últimas 3 velas, com amplitude mínima
            if C0 > range_high and (C0 - range_high) >= 0.0002:
                # Verifica se o movimento não está exausto (evita entrada no topo)
                # Calcula a amplitude média das últimas 5 velas
                avg_range_5 = (max(history_c[-5:]) - min(history_c[-5:])) / 5
                if avg_range_5 > 0:
                    # Se já percorreu mais de 70% da amplitude média, bloqueia
                    distance_from_low = C0 - min(history_c[-5:])
                    if distance_from_low / avg_range_5 < 0.7:
                        return "CALL", "FLASH"
                else:
                    return "CALL", "FLASH"
                    
            # PUT: preço atual abaixo do ponto mais baixo das últimas 3 velas, com amplitude mínima
            if C0 < range_low and (range_low - C0) >= 0.0002:
                avg_range_5 = (max(history_c[-5:]) - min(history_c[-5:])) / 5
                if avg_range_5 > 0:
                    distance_from_high = max(history_c[-5:]) - C0
                    if distance_from_high / avg_range_5 < 0.7:
                        return "PUT", "FLASH"
                else:
                    return "PUT", "FLASH"
        # ============================================================

        # Bloqueio geral para entradas tardias (após 3 segundos)
        if age_in_seconds >= 3.0:
            return None, f"ENTRADA_TARDIA (Idade {age_in_seconds:.1f}s)"

        # Padrão JustWin: tendência de médio prazo confirmando direção atual
        justwin_curr = None
        if (C0 > C2) and (C2 > O2) and (C4 > C8):
            justwin_curr = "CALL"
        elif (C0 < C2) and (C2 < O2) and (C4 < C8):
            justwin_curr = "PUT"

        # Padrão GenInd: impulso de curto prazo com vela fechada bullish/bearish
        genind_curr = None
        if (C0 > C1) and (C1 > O1) and (C3 > C2):
            genind_curr = "CALL"
        elif (C0 < C1) and (C1 < O1) and (C3 < C2):
            genind_curr = "PUT"

        sig_dir = None
        sig_name = ""

        if justwin_curr == genind_curr and justwin_curr is not None:
            sig_dir = justwin_curr
            sig_name = "DUPLA_CONFIRMACAO"
        elif justwin_curr is not None:
            sig_dir = justwin_curr
            sig_name = "JustWin_Solo"
        elif genind_curr is not None:
            sig_dir = genind_curr
            sig_name = "GenInd_Solo"

        return sig_dir, sig_name


# ============================================================
# 3. MICRO: CLASSIFICADOR QUANTITATIVO + VISÃO COMPUTACIONAL
# ============================================================
class QuantClassifier:
    def __init__(self):
        self.pending_signal = None
        self._data_lock = threading.Lock()

        self.candle_maturity_delay = 0.0
        self.signal_timeout = 15.0

        self.news_analyzer = NewsSentimentAnalyzer()
        self.market = MarketTracker()

        self._last_asset_id = 1

        # --- OCR ---
        self._last_ocr_scan_time = 0.0
        self.OCR_SCAN_INTERVAL = 0.0
        self._ocr_error_logged = False

        self._last_warmup_log = 0.0
        self._system_armed_logged = False

        self.news_analyzer.get_sentiment()

    def _extract_visual_signal(self, page: Page) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        now = time.time()
        if now - self._last_ocr_scan_time < self.OCR_SCAN_INTERVAL:
            return None, None, None
        self._last_ocr_scan_time = now

        try:
            screenshot_bytes = page.screenshot(full_page=False)
            img = Image.open(io.BytesIO(screenshot_bytes))
            width, height = img.size

            # Visão em túnel (50% a 98% do eixo X)
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

            if best_direction:
                self._ocr_error_logged = False
                return best_direction, best_text, max_x

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

            # Aspirador universal de ticks
            prices = re.findall(r'"(?:close|ask|bid|value)"\s*:\s*"?([0-9]+\.[0-9]+)"?', payload_lower)
            opens = re.findall(r'"open"\s*:\s*([0-9]+\.[0-9]+)', payload_lower)

            if not prices and not opens:
                return

            cl = float(prices[-1]) if prices else float(opens[-1])
            op = float(opens[-1]) if opens else cl

            # Proteção Multi-Aba: ignora ativos baratos (EUR, DOGE, etc)
            if op < 3.0 or op > 7.0:
                return

            match_id = re.search(r'"active_id"\s*:\s*(\d+)', payload_lower)
            if match_id:
                asset_id = int(match_id.group(1))
                with self._data_lock:
                    self._last_asset_id = asset_id
            else:
                asset_id = self._last_asset_id

            # Relógio absoluto (PC clock) - velas de 5 em 5s
            candle_time = int(time.time()) // 5

            self.market.update_robust(asset_id, op, cl, candle_time)

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

        asset_id = self._last_asset_id

        # Modo de aquecimento silencioso
        history_len = self.market.get_history_len(asset_id)
        if history_len < 10:
            now = time.time()
            if now - self._last_warmup_log > 5.0:
                print(f"⏳ [AQUECIMENTO TÁTICO] A calibrar histórico matemático da corretora... ({history_len}/10 velas completas).")
                self._last_warmup_log = now
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=1.0, recommended_action="WAIT")
        elif not self._system_armed_logged:
            print(f"\n🎯 [SISTEMA ARMADO] Matriz 100% carregada! Sniper silencioso ativado. Aguardando alvos na tela...")
            self._system_armed_logged = True

        # Verifica se há um sinal pendente (já confirmado anteriormente)
        if self.pending_signal:
            elapsed = time.time() - self.pending_signal["timestamp"]
            if elapsed > self.signal_timeout:
                print("\n⚠️ TIMEOUT: O sinal visual expirou.")
                self.pending_signal = None
                return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")

            if elapsed < self.candle_maturity_delay:
                return InferenceResult(state=ScreenState.ARMED, confidence=0.8, recommended_action="WAIT")

            candle_color, ticks_forca = self.market.get_color_ticks(asset_id)
            direction = self.pending_signal["direction"]
            signal_name = self.pending_signal.get("name", "")

            # Para sinais FLASH, agora também verificamos as condições novamente (evita entrada tardia)
            if signal_name == "FLASH":
                # Reavalia as condições do FLASH para garantir que ainda é válido
                quant_dir, quant_name = self.market.evaluate_scripts(asset_id)
                if quant_dir != direction or quant_name != "FLASH":
                    print(f"⚠️ SINAL FLASH EXPIRADO: Condições de rompimento não se mantêm.")
                    self.pending_signal = None
                    return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")
                
                # FLASH executa imediatamente, sem esperar ticks adicionais
                print("⚡ SINAL FLASH VÁLIDO! Execução instantânea.")
                entry_price = self.market.get_current_close(asset_id) or 0.0
                self.pending_signal = None
                if direction == "CALL":
                    return InferenceResult(
                        state=ScreenState.GATINHO_CALL,
                        confidence=1.0,
                        recommended_action="CLICK_ACIMA",
                        details={"asset_id": asset_id, "entry_price": entry_price}
                    )
                else:
                    return InferenceResult(
                        state=ScreenState.GATINHO_PUT,
                        confidence=1.0,
                        recommended_action="CLICK_ABAIXO",
                        details={"asset_id": asset_id, "entry_price": entry_price}
                    )

            # Demais sinais (JustWin, GenInd, DUPLA) seguem a lógica original com ticks
            news_sentiment = self.news_analyzer.get_sentiment()
            bull, bear = self.news_analyzer.get_scores()

            base_ticks = 0 if "DUPLA" in signal_name else 1
            required_ticks = base_ticks
            is_counter_trend = False

            if (direction == "CALL" and news_sentiment == "BEARISH_USD") or \
               (direction == "PUT" and news_sentiment == "BULLISH_USD"):
                required_ticks = base_ticks + 2
                is_counter_trend = True

            if ticks_forca >= required_ticks:
                if direction == "CALL" and candle_color == "GREEN":
                    print("✅ ALINHAMENTO TOTAL (TIRO INSTANTÂNEO)! Disparando ACIMA!")
                    entry_price = self.market.get_current_close(asset_id) or 0.0
                    self.pending_signal = None
                    return InferenceResult(
                        state=ScreenState.GATINHO_CALL,
                        confidence=1.0,
                        recommended_action="CLICK_ACIMA",
                        details={"asset_id": asset_id, "entry_price": entry_price}
                    )
                if direction == "PUT" and candle_color == "RED":
                    print("✅ ALINHAMENTO TOTAL (TIRO INSTANTÂNEO)! Disparando ABAIXO!")
                    entry_price = self.market.get_current_close(asset_id) or 0.0
                    self.pending_signal = None
                    return InferenceResult(
                        state=ScreenState.GATINHO_PUT,
                        confidence=1.0,
                        recommended_action="CLICK_ABAIXO",
                        details={"asset_id": asset_id, "entry_price": entry_price}
                    )

            return InferenceResult(state=ScreenState.ARMED, confidence=0.8, recommended_action="WAIT")

        # --- Nenhum sinal pendente: tenta detectar novo sinal visual + matemático ---
        visual_dir, raw_text, x_center = self._extract_visual_signal(page)
        if visual_dir is None:
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=1.0, recommended_action="WAIT")

        print(f"🔍 OCR detectou: {visual_dir} (texto='{raw_text}', x={x_center})")

        quant_dir, quant_name = self.market.evaluate_scripts(asset_id)

        if quant_dir is None:
            print(f"🚫 SINAL VISUAL IGNORADO: Matemática não confirmou (filtro: {quant_name or 'SEM_ALINHAMENTO'})")
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")

        if quant_dir != visual_dir:
            print(f"⚠️ FALSO POSITIVO GRÁFICO: OCR viu {visual_dir}, mas Matemática aponta {quant_dir}. Ignorado.")
            return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=0.5, recommended_action="WAIT")

        print(f"✅ CONFIRMAÇÃO HÍBRIDA: OCR ({visual_dir}) + Math ({quant_name}) alinhados!")

        # Para sinais FLASH, armamos o pending_signal mas a execução será no próximo ciclo
        # (para garantir que a condição de rompimento se mantém por pelo menos um tick)
        self.pending_signal = {
            "asset_id": asset_id,
            "direction": visual_dir,
            "name": quant_name,
            "timestamp": time.time()
        }
        
        # Se for FLASH, já avisamos que está armado e será executado no próximo ciclo (rápido)
        if quant_name == "FLASH":
            print("⚡ SINAL FLASH ARMADO. Aguardando confirmação de manutenção do rompimento...")
        else:
            print(f"🔫 SINAL {quant_name} ARMADO. Aguardando alinhamento de ticks...")
            
        return InferenceResult(state=ScreenState.ARMED, confidence=0.9, recommended_action="WAIT")

    def _detect_posicao_aberta(self, html_str: str) -> bool:
        m = re.search(r'Op[çõesçõe]es\s*\((\d+)\)', html.unescape(html_str), re.IGNORECASE)
        return int(m.group(1)) > 0 if m else False


# ============================================================
# 4. MICRO: EXECUTOR DE AÇÕES
# ============================================================
class ActionExecutor:
    def __init__(self, page: Page, coord_acima=(1221, 375), coord_abaixo=(1208, 483)):
        self.page = page
        self.coord_acima = coord_acima
        self.coord_abaixo = coord_abaixo

    def execute(self, result: InferenceResult):
        if result.recommended_action == "CLICK_ACIMA":
            return self._click(self.coord_acima, "BUY")
        if result.recommended_action == "CLICK_ABAIXO":
            return self._click(self.coord_abaixo, "SELL")
        return {"ok": True, "action_taken": "WAIT"}

    def _click(self, coord, type):
        try:
            self.page.bring_to_front()
            self.page.mouse.click(coord[0], coord[1])
            return {"ok": True, "action_taken": f"{type}_EXECUTED"}
        except Exception:
            return {"ok": False, "error": "Click failed"}


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

        self._consecutive_losses = 0
        self.CIRCUIT_BREAKER_LIMIT = 2
        self.CIRCUIT_PAUSE_SECONDS = 30.0
        self._trade_entry_price = 0.0
        self._trade_direction = ""
        self._trade_asset_id = None

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

        # Blind Spot Bypass: evita sobrecarga de CPU durante trade aberto
        if trade_was_active:
            time_in_trade = time.time() - trade_start_time
            if time_in_trade < 8.0:
                time.sleep(0.2)
                return {"cycle_id": str(self._cycle_count), "state": ScreenState.POSITION_OPEN,
                        "recommended_action": "WAITING_RESULT"}

        self._cycle_count += 1
        inf = self.classifier.classify(self._active_page)
        self._last_result = inf

        if trade_was_active:
            if inf.state != ScreenState.POSITION_OPEN:
                time.sleep(0.5)
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
                        self._cooldown_until = time.time() + 5.0
                        print(f"\n✅ WIN REGISTADO. (Entrada: {self._trade_entry_price:.5f} | Saída: {exit_price:.5f})")
                    else:
                        self._consecutive_losses += 1
                        print(f"\n❌ LOSS REGISTADO. (Entrada: {self._trade_entry_price:.5f} | Saída: {exit_price:.5f})")

                        if self._consecutive_losses >= self.CIRCUIT_BREAKER_LIMIT:
                            print(f"🛑 CIRCUIT BREAKER ACIONADO! {self.CIRCUIT_BREAKER_LIMIT} perdas consecutivas.")
                            print(f"Pausando motores por {self.CIRCUIT_PAUSE_SECONDS} segundos...\n")
                            self._cooldown_until = time.time() + self.CIRCUIT_PAUSE_SECONDS
                            self._consecutive_losses = 0
                        else:
                            self._cooldown_until = time.time() + 5.0

                    self._trade_in_progress = False
                    self._trade_asset_id = None
                return {"cycle_id": str(self._cycle_count), "state": ScreenState.COOLDOWN, "action_result": {"ok": True}}

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

        return {"cycle_id": str(self._cycle_count), "state": inf.state, "action_result": res}

    def get_status(self) -> Dict:
        with self._lock:
            if not self._last_result:
                return {"status": "IDLE"}
            return {"status": "ACTIVE", "last_state": self._last_result.state}


alpha_engine = AlphaEngine()