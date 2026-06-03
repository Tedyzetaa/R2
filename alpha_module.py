# filename: alpha_module.py
# ============================================================
# REFATORAÇÃO DE ELITE: GHOST SCALPER S5 - BLINDAGEM INSTITUCIONAL
# ============================================================
# - Anti-Rali por Pressão (Trend Gravity de 40s)
# - Botão de Pânico Fundamentalista (Filtro de Manchetes do Fed)
# - Mantida Calibragem Vencedora: Pavios Isolados (RSI 75 / 25)
# - Salvamento assíncrono por fila thread-safe em background
# ============================================================

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple

import os
import time
import json
import logging
import queue
import threading
from collections import deque
from datetime import datetime

from features.news_worker import NewsWorker, ler_sentimento

logger = logging.getLogger("ModuloAlpha")

# Fila assíncrona para não engasgar o loop de envio do navegador
_LOG_QUEUE: queue.Queue = queue.Queue()

def _worker_gravacao_historico():
    log_file = "historico_trades_alpha.json"
    while True:
        dados_trade = _LOG_QUEUE.get()
        if dados_trade is None:
            break
        try:
            historico: list = []
            if os.path.exists(log_file):
                with open(log_file, mode="r", encoding="utf-8") as f:
                    conteudo = f.read()
                    if conteudo.strip():
                        historico = json.loads(conteudo)
            historico.append(dados_trade)
            with open(log_file, mode="w", encoding="utf-8") as f:
                json.dump(historico, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico em background: {e}")
        finally:
            _LOG_QUEUE.task_done()

_thread_gravadora = threading.Thread(target=_worker_gravacao_historico, daemon=True)
_thread_gravadora.start()


class ScreenState(str, Enum):
    IDLE     = "IDLE"
    SCANNING = "SCANNING"
    TRADING  = "TRADING"
    COOLDOWN = "COOLDOWN"
    STOPPED  = "STOPPED"
    UNKNOWN  = "UNKNOWN"


@dataclass
class InferenceResult:
    cycle_id:           str   = "0"
    state:              str   = ScreenState.IDLE
    recommended_action: str   = "WAIT"
    confidence:         float = 0.0
    reason:             str   = ""
    details:            dict  = field(default_factory=dict)


class ComandoDetector:
    def __init__(self):
        self.sup_level = 0.0
        self.res_level = 0.0

    def processar_vela(self, ohlc: Dict):
        open_p = ohlc["open"]
        close_p = ohlc["close"]
        high_p = ohlc["high"]
        low_p = ohlc["low"]

        # Lógica: Vela de Comando de Alta (sem pavio inferior)
        if (open_p <= low_p + 0.00001) and (close_p > open_p):
            self.sup_level = open_p
            
        # Lógica: Vela de Comando de Baixa (sem pavio superior)
        if (open_p >= high_p - 0.00001) and (close_p < open_p):
            self.res_level = open_p
            
    def esta_em_zona_proibida(self, preco: float, direcao: str) -> bool:
        """
        Retorna True se o preço estiver perigosamente perto de uma zona de comando contrária.
        """
        margem = 0.00005 # 5 pips de margem de erro
        
        if direcao == "PUT": # Queremos vender, então checamos se estamos perto de uma resistência de comando
            if self.res_level > 0 and abs(preco - self.res_level) < margem:
                return True
        elif direcao == "CALL": # Queremos comprar, checamos suporte
            if self.sup_level > 0 and abs(preco - self.sup_level) < margem:
                return True
        return False


class RSIEngine:
    def __init__(self, period: int = 14):
        self.period     = period
        self.prices: deque[float] = deque(maxlen=period + 1)
        self.avg_gain:   Optional[float] = None
        self.avg_loss:   Optional[float] = None
        self.current_rsi: Optional[float] = None

    def add_price(self, close_price: float) -> Optional[float]:
        self.prices.append(close_price)
        if len(self.prices) < 2:
            return None

        gain = max(0.0, self.prices[-1] - self.prices[-2])
        loss = max(0.0, self.prices[-2] - self.prices[-1])

        if self.avg_gain is None:
            if len(self.prices) == self.period + 1:
                gains = [max(0.0, self.prices[i] - self.prices[i - 1]) for i in range(1, len(self.prices))]
                losses = [max(0.0, self.prices[i - 1] - self.prices[i]) for i in range(1, len(self.prices))]
                self.avg_gain = sum(gains) / self.period
                self.avg_loss = sum(losses) / self.period
            else:
                return None
        else:
            self.avg_gain = (self.avg_gain * (self.period - 1) + gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + loss) / self.period

        if self.avg_loss == 0:
            self.current_rsi = 100.0
            return 100.0

        rs = self.avg_gain / self.avg_loss
        self.current_rsi = 100.0 - (100.0 / (1.0 + rs))
        return self.current_rsi

    def reset(self) -> None:
        self.prices.clear()
        self.avg_gain    = None
        self.avg_loss    = None
        self.current_rsi = None


class AlphaEngine:
    RSI_CANDLE_COOLDOWN: int = 30  

    def __init__(self, tolerance: float = 0.0002, max_trades_session: int = 999999):
        self._lock            = threading.RLock()
        self.autopilot_ativo  = False
        self.timeframe        = 5            

        self.wins                = 0
        self.losses              = 0
        self.losses_consecutivos = 0

        self.rsi15 = RSIEngine(period=10)
        self.rsi30 = RSIEngine(period=14)
        self.rsi50 = RSIEngine(period=20)

        self.comando_detector = ComandoDetector()

        self.historico_corpos: deque[float] = deque(maxlen=40)
        # Ampliado para 8 velas (40 segundos de análise direcional macro para S5)
        self.historico_direcoes: deque[int] = deque(maxlen=8) 
        
        self.distancia_minima_gatilho = 0.00005   
        self.multiplicador_esticada   = 1.5       

        self.broker_ops              = None
        self._cooldown_until         = 0.0
        self._last_trade_strategy    = None
        self._last_trade_context: dict = {}
        self._trade_entry_price      = 0.0
        self._last_trade_timestamp: Optional[int] = None   
        self._last_trade_direction   = None
        self.ultimo_id_disparado_rsi = 0.0
        self.trade_em_andamento      = False
        self.last_price              = 0.0

        self.trades_count            = 0
        self.max_trades_session      = max_trades_session
        self.max_losses_consecutivos = 3      
        self.min_amount              = 4.0    

        self._warmup_candles       = 0
        self._min_candles_for_rsi  = 25  

        self.target_active_id = 2298
        self._last_processed_candle_id = 0

        self.classifier = type("MockClassifier", (object,), {
            "justiceiro": type("MockJusticeiro", (object,), {"tolerance": tolerance})(),
            "market": type("MockMarket", (object,), {
                "market_structure": type("MockStructure", (object,), {
                    "get_trend_description": lambda: "Lateral"
                })(),
                "breakout_detector": type("MockDetector", (object,), {
                    "is_valid_breakout_signal": lambda x: False
                })(),
            })(),
        })()
        self.manager = self    
        self.risk = type("MockRisk", (object,), {
            "_daily_pnl":               0.0,
            "daily_loss_limit":         100.0,
            "daily_target":             200.0,
            "_consecutive_losses":      0,
            "get_position_size_multiplier": lambda: 1.0,
            "is_daily_stopped":         lambda: False,
        })()

        self.news_worker = NewsWorker(poll_interval=180)
        self.news_worker.iniciar()
        logger.info("📡 [GHOST S5] Inicializado. Filtros Anti-Rali e Fundamentalista Ativos.")

    def ligar_autopilot(self) -> None:
        with self._lock:
            self.rsi15.reset()
            self.rsi30.reset()
            self.rsi50.reset()
            self.historico_corpos.clear()
            self.historico_direcoes.clear()
            self.autopilot_ativo          = True
            self._cooldown_until          = 0.0
            self._last_trade_timestamp    = None
            self._last_processed_candle_id = 0
            self.ultimo_id_disparado_rsi  = 0.0
            self.losses_consecutivos      = 0
            self.trades_count             = 0
            self.wins                     = 0
            self.losses                   = 0
            self._warmup_candles          = 0
            self.trade_em_andamento       = False
        logger.info("🔍 Autopilot S5 pronto e limpo para execução.")

    def _ler_sentimento_macro_completo(self) -> Tuple[float, str]:
        """Lê o JSON diretamente para extrair não apenas o score, mas a manchete principal."""
        try:
            if os.path.exists("noticias_sentimento.json"):
                with open("noticias_sentimento.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    score = float(data.get("score", data.get("sentimento", 0.0)))
                    manchete = str(data.get("top_headline", "")).upper()
                    return score, manchete
        except Exception:
            pass
        return 0.0, ""

    def _validar_sentimento_macro(self, score: float, direcao: str) -> bool:
        if score > 0.25 and direcao == "PUT":
            return False
        if score < -0.25 and direcao == "CALL":
            return False
        return True

    def _pode_operar(self, candle_id: int) -> bool:
        agora = time.time()
        if not self.autopilot_ativo:
            return False
        if self.trades_count >= self.max_trades_session:
            return False
        if agora < self._cooldown_until:
            return False

        if self.trade_em_andamento:
            tempo_decorrido = agora - (self._last_trade_timestamp or 0)
            if tempo_decorrido > 65:  
                self.trade_em_andamento = False
            else:
                return False

        if self._last_trade_timestamp == candle_id:
            return False
        if self._warmup_candles < self._min_candles_for_rsi:
            return False
        if self.losses_consecutivos >= self.max_losses_consecutivos:
            return False

        return True

    def executar_disparo(
        self,
        direcao:       str,
        estrategia:    str,
        candle_id:     int,
        timestamp:     float,
        contexto:      Dict,
    ) -> Optional[str]:
        with self._lock:
            if not self._pode_operar(candle_id):
                return None

            self.trade_em_andamento      = True
            self._last_trade_timestamp   = candle_id
            self._last_trade_direction   = direcao
            self._last_trade_strategy    = estrategia
            self._last_trade_context     = contexto
            self._trade_entry_price      = contexto.get("preco_captura", 0.0)

            contexto["amount"] = self.min_amount

            if self.broker_ops:
                deslocamento = contexto.get("deslocamento_pips", 0.0)
                logger.info(f"🎯 [DISPARO INSTANTÂNEO] {direcao} | Taxa Pavio: {self._trade_entry_price:.6f} | Deslocamento: {deslocamento:.6f}")
                res = self.broker_ops.executar_ordem(direcao)
                if res and res.get("ok"):
                    self.trades_count += 1
                    return direcao
                else:
                    self.trade_em_andamento = False
                    return None
            return None

    def processar_dados(self, ohlc: Dict, timestamp: float) -> Optional[str]:
        with self._lock:
            if not self.autopilot_ativo:
                return None

            close = ohlc.get("close")
            open_price = ohlc.get("open")
            if close is None or open_price is None:
                return None

            self.comando_detector.processar_vela(ohlc)

            self._warmup_candles += 1
            self.last_price = close

            v15 = self.rsi15.add_price(close)
            v30 = self.rsi30.add_price(close)
            v50 = self.rsi50.add_price(close)

            candle_id = int(timestamp // 5) * 5
            deslocamento = close - open_price
            abs_deslocamento = abs(deslocamento)

            self.historico_corpos.append(abs_deslocamento)
            
            direcao_vela = 1 if deslocamento > 0 else (-1 if deslocamento < 0 else 0)
            self.historico_direcoes.append(direcao_vela)

            if len(self.historico_corpos) >= 5:
                media_recentes = sum(list(self.historico_corpos)[:-1]) / (len(self.historico_corpos) - 1)
                alvo_distancia_dinamica = max(self.distancia_minima_gatilho, media_recentes * self.multiplicador_esticada)
            else:
                alvo_distancia_dinamica = self.distancia_minima_gatilho

            if abs_deslocamento < alvo_distancia_dinamica:
                return None

            if v15 is None or v30 is None or v50 is None:
                return None

            # ---------------------------------------------------------
            # FILTRO 1: ANTI-BOMBA FUNDAMENTALISTA (O BOTÃO DO FED)
            # ---------------------------------------------------------
            score_macro, manchete = self._ler_sentimento_macro_completo()
            
            palavras_perigosas = ["FED ", "POWELL", "RATE", "RATES", "INFLATION", "CPI "]
            if any(p in manchete for p in palavras_perigosas):
                if time.time() > self._cooldown_until:
                    logger.warning(f"🚨 [PERIGO INSTITUCIONAL] Notícia do FED/Taxas detectada. Suspendo operações por 3 minutos. Manchete: {manchete[:60]}...")
                    self._cooldown_until = time.time() + 180  # Lockdown de 3 minutos
                return None

            # ---------------------------------------------------------
            # FILTRO 2: ANTI-RALI POR PRESSÃO DIRECIONAL (TREND GRAVITY)
            # ---------------------------------------------------------
            if len(self.historico_direcoes) >= 8:
                pressao_tendencia = sum(list(self.historico_direcoes))
                # Se o saldo das últimas 8 velas for de +5 ou mais (ex: 6 verdes e 1 vermelha)
                if pressao_tendencia >= 5 and deslocamento > 0:
                    return None  # Bloqueia PUT contra uma maré massiva de alta
                # Se o saldo for -5 ou menos (ex: 6 vermelhas e 1 verde)
                if pressao_tendencia <= -5 and deslocamento < 0:
                    return None  # Bloqueia CALL contra um derretimento maciço

            contexto = {
                "rsi10_fast":       round(v15, 2),
                "rsi14_fast":       round(v30, 2),
                "rsi20_fast":       round(v50, 2),
                "sentimento_macro": score_macro,
                "preco_captura":    close,
                "deslocamento_pips": deslocamento,
                "abertura":         open_price,
                "fechamento":       close,
            }

            if deslocamento > 0 and v15 >= 75.0 and v30 >= 68.0:
                if not self._validar_sentimento_macro(score_macro, "PUT"):
                    return None
                if self.comando_detector.esta_em_zona_proibida(close, "PUT"):
                    logger.info("🚫 Bloqueado: Zona de Comando de Baixa detectada.")
                    return None
                if timestamp <= self.ultimo_id_disparado_rsi + self.RSI_CANDLE_COOLDOWN:
                    return None
                self.ultimo_id_disparado_rsi = timestamp
                return self.executar_disparo("PUT", "PAVIO_S5_OVERBOUGHT", candle_id, timestamp, contexto)

            elif deslocamento < 0 and v15 <= 25.0 and v30 <= 32.0:
                if not self._validar_sentimento_macro(score_macro, "CALL"):
                    return None
                if self.comando_detector.esta_em_zona_proibida(close, "CALL"):
                    logger.info("🚫 Bloqueado: Zona de Comando de Alta detectada.")
                    return None
                if timestamp <= self.ultimo_id_disparado_rsi + self.RSI_CANDLE_COOLDOWN:
                    return None
                self.ultimo_id_disparado_rsi = timestamp
                return self.executar_disparo("CALL", "PAVIO_S5_OVERSOLD", candle_id, timestamp, contexto)

            return None

    def processar_payload(self, data: Dict) -> None:
        if not data:
            return
        try:
            nome_evento = data.get("name")
            if nome_evento == "candle-generated":
                msg = data.get("msg", {})
                if int(msg.get("active_id", 0)) != self.target_active_id:
                    return

                timestamp_raw = msg.get("timestamp", time.time())
                candle_id     = int(timestamp_raw // 5) * 5  

                if candle_id <= self._last_processed_candle_id:
                    return

                with self._lock:
                    self._last_processed_candle_id = candle_id

                    candle = {
                        "open":    msg.get("open"),
                        "high":    msg.get("max"),
                        "low":     msg.get("min"),
                        "close":   msg.get("close"),
                        "current": msg.get("close"),
                        "volume":  msg.get("volume", 0),
                    }

                    logger.info(f"⚡ [VELA S5] ID: {candle_id} | Preço: {candle['close']:.6f} | RSI10: {round(self.rsi15.current_rsi, 1) if self.rsi15.current_rsi else 'W'}")
                    self.processar_dados(candle, timestamp_raw)

            elif nome_evento == "order-closed":
                with self._lock:
                    msg_payload    = data.get("msg", {})
                    lucro          = float(msg_payload.get("profit", 0.0))
                    preco_fechamento = float(msg_payload.get("close_price", msg_payload.get("value", 0.0)))

                    if lucro > 0:
                        resultado = "win"
                        self.wins += 1
                        self.losses_consecutivos = 0
                    elif lucro < 0:
                        resultado = "loss"
                        self.losses += 1
                        self.losses_consecutivos += 1
                        # Punição rígida: se tomou loss num S5, o mercado está instável. Descansa 45s.
                        self._cooldown_until = time.time() + 45
                    else:
                        resultado = "draw"

                    dados_trade = {
                        "trade_id":          f"T_{int(time.time())}",
                        "timestamp_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "estrategia_gatilho": self._last_trade_strategy,
                        "direcao":           self._last_trade_direction,
                        "resultado":         resultado.upper(),
                        "lucro_pnl":         lucro,
                        "preco_entrada":     self._trade_entry_price,
                        "preco_saida":       preco_fechamento,
                        "contexto": {
                            **self._last_trade_context,
                            "active_id": self.target_active_id,
                        },
                        "estado_sessao": {
                            "placar":              f"{self.wins}W - {self.losses}L",
                            "losses_consecutivos": self.losses_consecutivos,
                        },
                    }
                    self.trade_em_andamento = False

                    _LOG_QUEUE.put(dados_trade)
                    logger.info(f"📊 [CONTRATO COMPLETO] Resultado: {resultado.upper()} | Mapeado: {self.wins}W - {self.losses}L")

        except Exception as e:
            logger.error(f"Erro no processamento de payload S5: {e}", exc_info=True)

    def processar_ws(self, payload: str) -> None:
        try:
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8", errors="ignore")

            cleaned = payload.strip()
            if cleaned.startswith("42[") or cleaned.startswith("42"):
                cleaned = cleaned[cleaned.index("["):] if "[" in cleaned else cleaned[2:]

            data = json.loads(cleaned)
            if isinstance(data, list) and len(data) >= 2:
                data = {"name": data[0], "msg": data[1]}

            if isinstance(data, dict):
                self.processar_payload(data)
        except Exception as e:
            logger.error(f"Erro no parsing WebSocket S5: {e}")

    def get_status(self) -> Dict:
        with self._lock:
            cooldown = max(0, int(self._cooldown_until - time.time()))
            return {
                "status":             "ACTIVE" if self.autopilot_ativo else "IDLE",
                "cooldown_restante_s": cooldown,
                "trades_realizados":  self.trades_count,
                "placar":             f"{self.wins}W - {self.losses}L",
                "rsi_10":  round(self.rsi15.current_rsi, 2) if self.rsi15.current_rsi is not None else "WARMUP",
                "rsi_14":  round(self.rsi30.current_rsi, 2) if self.rsi30.current_rsi is not None else "WARMUP",
                "rsi_20":  round(self.rsi50.current_rsi, 2) if self.rsi50.current_rsi is not None else "WARMUP",
                "ultimo_preco": self.last_price,
                "warmup_restante": max(0, self._min_candles_for_rsi - self._warmup_candles),
            }

    def perceive_and_act(self) -> Dict:
        return {
            "cycle_id":           "0",
            "state":              "ACTIVE" if self.autopilot_ativo else "IDLE",
            "recommended_action": "WAIT",
            "details":            self.get_status(),
        }

    def attach(self, page) -> None:
        self._active_page = page

    def get_balance(self) -> None:
        return None

    def request_stop(self) -> None:
        with self._lock:
            self.autopilot_ativo = False

    def marcar_conexao_ws(self) -> None:
        logger.info("🔌 Conexão WebSocket registrada em S5.")

alpha_engine = AlphaEngine(tolerance=0.0002, max_trades_session=999999)