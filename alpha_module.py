# filename: alpha_module.py
# ============================================================
# REFATORAÇÃO FINAL - GHOST PROTOCOL S5
# - Foco exclusivo em velas de 5 segundos (S5)
# - RSI Fast (período 10) com níveis 30/70
# - Suporte/Resistência simples (últimos níveis por mínimo/máximo)
# - Persistência assíncrona em historico_trades_alpha.json
# - Sem variáveis globais soltas, escopo totalmente encapsulado
# - Interface com broker_operator.py via AlphaEngine
# ============================================================
# --- ADIÇÕES PARA COMPATIBILIDADE COM MAIN2.PY ---
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
# ============================================================

import os
import time
import json
import logging
import asyncio
import threading
from collections import deque
from datetime import datetime

try:
    import aiofiles
except ImportError:
    aiofiles = None
    logging.warning("aiofiles não instalado. Persistência assíncrona será simulada com escrita síncrona.")

logger = logging.getLogger("ModuloAlpha")

# ==================================================================
# CLASSES DE COMPATIBILIDADE (exigidas pelo main2.py)
# ==================================================================
class ScreenState(str, Enum):
    """Estados da máquina de estados do Alpha (compatibilidade)."""
    IDLE = "IDLE"
    SCANNING = "SCANNING"
    TRADING = "TRADING"
    COOLDOWN = "COOLDOWN"
    STOPPED = "STOPPED"
    UNKNOWN = "UNKNOWN"

@dataclass
class InferenceResult:
    """Resultado de inferência para integração com main2.py."""
    cycle_id: str = "0"
    state: str = ScreenState.IDLE
    recommended_action: str = "WAIT"
    confidence: float = 0.0
    reason: str = ""
    details: dict = field(default_factory=dict)

# ==================================================================
# FUNÇÃO DE PERSISTÊNCIA ASSÍNCRONA (JSON raiz)
# ==================================================================
async def salvar_trade_json_raiz(dados_trade: dict):
    """Grava o resultado do trade de forma assíncrona em historico_trades_alpha.json."""
    log_file = "historico_trades_alpha.json"
    if "timestamp_registro" not in dados_trade:
        dados_trade["timestamp_registro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        historico = []
        if os.path.exists(log_file):
            if aiofiles:
                async with aiofiles.open(log_file, mode='r', encoding='utf-8') as f:
                    conteudo = await f.read()
                    if conteudo.strip():
                        historico = json.loads(conteudo)
            else:
                with open(log_file, mode='r', encoding='utf-8') as f:
                    conteudo = f.read()
                    if conteudo.strip():
                        historico = json.loads(conteudo)
        historico.append(dados_trade)
        if aiofiles:
            async with aiofiles.open(log_file, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(historico, indent=4, ensure_ascii=False))
        else:
            with open(log_file, mode='w', encoding='utf-8') as f:
                json.dump(historico, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erro ao salvar log do trade: {e}")

# ==================================================================
# RSI ENGINE (Relative Strength Index) – período 10, Wilder Smoothing
# ==================================================================
class RSIEngine:
    def __init__(self, period: int = 10, oversold: float = 30.0, overbought: float = 70.0):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.prices = deque(maxlen=period + 1)
        self.avg_gain = None
        self.avg_loss = None
        self.current_rsi = None   # valor mais recente do RSI

    def add_price(self, close_price: float) -> Optional[float]:
        """Adiciona um novo preço de fechamento e retorna o RSI atual (ou None se ainda não pronto)."""
        self.prices.append(close_price)
        if len(self.prices) < 2:
            self.current_rsi = None
            return None

        gain = max(0.0, self.prices[-1] - self.prices[-2])
        loss = max(0.0, self.prices[-2] - self.prices[-1])

        if self.avg_gain is None:
            if len(self.prices) == self.period + 1:
                gains = [max(0.0, self.prices[i] - self.prices[i-1]) for i in range(1, len(self.prices))]
                losses = [max(0.0, self.prices[i-1] - self.prices[i]) for i in range(1, len(self.prices))]
                self.avg_gain = sum(gains) / self.period
                self.avg_loss = sum(losses) / self.period
            else:
                self.current_rsi = None
                return None
        else:
            self.avg_gain = (self.avg_gain * (self.period - 1) + gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + loss) / self.period

        if self.avg_loss == 0:
            self.current_rsi = 100.0
            return 100.0

        rs = self.avg_gain / self.avg_loss
        rsi_val = 100.0 - (100.0 / (1.0 + rs))
        self.current_rsi = rsi_val
        return rsi_val

    def reset(self):
        self.prices.clear()
        self.avg_gain = None
        self.avg_loss = None
        self.current_rsi = None

# ==================================================================
# SUPORTE / RESISTÊNCIA SIMPLES (últimos níveis por mínimo/máximo)
# ==================================================================
class SimpleSR:
    def __init__(self, lookback: int = 10, tolerance: float = 0.0002):
        self.lookback = lookback
        self.tolerance = tolerance
        self.candles_data = deque(maxlen=lookback + 2) # Buffer para garantir histórico consolidado
        self.current_support = None
        self.current_resistance = None
        self.last_support_touch_time = 0.0
        self.last_resistance_touch_time = 0.0

    def add_candle_ohlc(self, candle_ohlc: Dict):
        """Atualiza níveis usando histórico, excluindo a vela atual para evitar que o suporte siga o preço."""
        self.candles_data.append(candle_ohlc)
        if len(self.candles_data) >= self.lookback + 1:
            history = list(self.candles_data)[:-1]  # Ignora a vela atual (em processamento)
            self.current_support = min(c['low'] for c in history[-self.lookback:])
            self.current_resistance = max(c['high'] for c in history[-self.lookback:])
            logger.debug(f"[SR] Níveis Consolidados (S5): S={self.current_support:.5f} R={self.current_resistance:.5f}")

    def check_touch(self, current_price: float) -> Optional[str]:
        """Verifica se o preço atual tocou o suporte ou resistência.
           Retorna 'CALL' se tocar suporte, 'PUT' se tocar resistência, None caso contrário."""
        agora = time.time()
        # Verifica toque no suporte
        if self.current_support is not None and current_price <= self.current_support + self.tolerance and agora - self.last_support_touch_time > 1.0:
            self.last_support_touch_time = agora
            logger.info(f"[SR] Toque em SUPORTE {self.current_support:.5f} -> CALL")
            return "CALL"
        # Verifica toque na resistência
        if self.current_resistance is not None and current_price >= self.current_resistance - self.tolerance and agora - self.last_resistance_touch_time > 1.0:
            self.last_resistance_touch_time = agora
            logger.info(f"[SR] Toque em RESISTÊNCIA {self.current_resistance:.5f} -> PUT")
            return "PUT"
        return None

# ==================================================================
# ALPHA ENGINE (orquestrador principal S5)
# ==================================================================
class AlphaEngine:
    def __init__(self, tolerance: float = 0.0002, max_trades_session: int = 999999):
        self.autopilot_ativo = False # ✨ CORREÇÃO: Inicialização antecipada
        self.timeframe = 60  # <-- AQUI ESTÁ O QUE ESTÁ FALTANDO
        self.wins = 0 # ✨ CORREÇÃO: Inicialização antecipada
        self.losses = 0 # ✨ CORREÇÃO: Inicialização antecipada
        self.losses_consecutivos = 0 # ✨ CORREÇÃO: Inicialização antecipada
        self._lock = threading.RLock() # ✨ CORREÇÃO: Inicialização antecipada
        # Motores simplificados
        self.rsi = RSIEngine(period=10, oversold=30.0, overbought=70.0)
        self.sr = SimpleSR(lookback=10, tolerance=tolerance)

        # Estado interno (sem variáveis globais)
        self.broker_ops = None
        self.autopilot_ativo = False
        self._cooldown_until = 0.0
        self._last_trade_strategy = None
        self._last_trade_context = {}
        self._trade_entry_price = 0.0

        # Gerenciamento simples de risco
        self.losses_consecutivos = 0
        self.max_losses_consecutivos = 2
        self.cooldown_apos_loss = 15          # segundos

        # Estatísticas
        self.wins = 0
        self.losses = 0
        self.trades_count = 0
        self.max_trades_session = max_trades_session

        # Controle de warmup do RSI (apenas para não gerar sinais antes do período completo)
        self._warmup_candles = 0
        self._min_candles_for_rsi = 5         # período do RSI (M1)

        # Último preço conhecido (para status)
        self.last_price = 0.0

        # Ativo alvo (caso a plataforma use múltiplos ativos)
        self.target_active_id = 2298

        # GERENCIAMENTO DE RISCO E FILTROS RÍGIDOS
        self.tp_percent = 0.012  # 1.2% Take Profit
        self.sl_percent = 0.03   # 3.0% Stop Loss
        self.min_amount = 4.0    # Valor mínimo de operação em dólares
        self._last_processed_candle_id = 0  # Debounce de ciclo S5
        self.trade_em_andamento = False      # Flag de bloqueio de ordem ativa
        self.ultimo_id_disparado_rsi = 0     # Cooldown de velas para RSI
        # MEL-01: constante extraída para evitar recálculo a cada candle e tornar
        # a intenção explícita (3 velas S5 = 15 segundos de cooldown pós-RSI).
        self.RSI_CANDLE_COOLDOWN = 3 * 5    # 15 segundos
        self.historico_direcao = deque(maxlen=10) # Histórico para filtro de tendência forte
        self.historico_precos = deque(maxlen=5) # Guarda os últimos 5 fechamentos

        # MOCKS DE COMPATIBILIDADE PARA O MAIN2.PY
        # Isso evita o AttributeError e permite que o sistema acesse estruturas legadas
        self.classifier = type('MockClassifier', (object,), {
            'justiceiro': type('MockJusticeiro', (object,), {'tolerance': tolerance})(),
            'market': type('MockMarket', (object,), {
                'market_structure': type('MockStructure', (object,), {'get_trend_description': lambda: "Lateral"})(),
                'breakout_detector': type('MockDetector', (object,), {'is_valid_breakout_signal': lambda x: False})()
            })()
        })()

        self.manager = self # Mapeia alpha_engine.manager.wins/losses para as estatísticas atuais

        self.risk = type('MockRisk', (object,), {
            '_daily_pnl': 0.0,
            'daily_loss_limit': 100.0,
            'daily_target': 200.0,
            '_consecutive_losses': 0,
            'get_position_size_multiplier': lambda: 1.0,
            'is_daily_stopped': lambda: False
        })()

    def ligar_autopilot(self):
        """Ativa o robô e reseta todos os estados internos."""
        with self._lock:
            self.rsi.reset()
            self.sr = SimpleSR(lookback=10, tolerance=self.sr.tolerance)
            self.autopilot_ativo = True
            self._cooldown_until = 0.0
            self._last_trade_timestamp = None
            self._last_processed_candle_id = 0
            self.historico_direcao.clear()
            self.historico_precos.clear()
            self.losses_consecutivos = 0
            self.trades_count = 0
            self.wins = 0
            self.losses = 0
            self._warmup_candles = 0
            # BUG-CRIT-04 FIX: ligar_autopilot não resetava trade_em_andamento nem
            # ultimo_id_disparado_rsi. Se o autopilot fosse reiniciado enquanto uma
            # ordem estava ativa, a nova sessão começava travada por 70s.
            self.trade_em_andamento = False
            self.ultimo_id_disparado_rsi = 0
            logger.info(
                f"🔍 Autopilot ativado. Aguardando warmup do RSI "
                f"({self._min_candles_for_rsi} candles M1 | active_id={self.target_active_id})."
            )

    def _pode_operar(self, timestamp_vela: float) -> bool:
        """Verifica condições gerais para permitir uma nova operação."""
        agora = time.time()
        if not self.autopilot_ativo:
            return False
        if self.trades_count >= self.max_trades_session:
            logger.info(f"Limite de {self.max_trades_session} trades atingido.")
            return False
        if agora < self._cooldown_until:
            logger.debug(f"Cooldown ativo: {self._cooldown_until - agora:.1f}s")
            return False

        # --- LÓGICA DE DESTRAVAMENTO AUTOMÁTICO (TIMEOUT) ---
        if self.trade_em_andamento:
            # Verifica se a ordem ficou presa (mais de 70 segundos sem fechar via WS)
            tempo_decorrido = agora - (self._last_trade_timestamp or 0)
            if tempo_decorrido > 45:
                logger.warning("⏱️ [TIMEOUT] Ordem anterior não retornou fechamento via WS (Limite 45s). Forçando destravamento!")
                self.trade_em_andamento = False 
            else:
                logger.warning("⚠️ Operação em andamento no Broker. Ignorando novo sinal.")
                return False

        if self._last_trade_timestamp == timestamp_vela:
            logger.info(f"🔒 Candle lock: já operou na vela {timestamp_vela}")
            return False
        if self.last_price <= 0:
            logger.warning("Preço inválido para operação.")
            return False
        if self._warmup_candles < self._min_candles_for_rsi:
            logger.info(f"🔄 Warmup RSI (S5): {self._warmup_candles}/{self._min_candles_for_rsi} candles recebidos")
            return False
        if self.losses_consecutivos >= self.max_losses_consecutivos:
            logger.info(f"Stop consecutivo: {self.losses_consecutivos} losses seguidos.")
            return False
        return True

    def _aplicar_cooldown_apos_trade(self, resultado: str):
        """Define o cooldown baseado no resultado."""
        if resultado.lower() == 'loss':
            self.losses_consecutivos += 1
            self._cooldown_until = time.time() + self.cooldown_apos_loss
        else:
            self.losses_consecutivos = 0
            self._cooldown_until = time.time() + 1.0   # cooldown mínimo

    def executar_disparo(self, direcao: str, estrategia: str, timestamp_vela: float, contexto: Dict) -> Optional[str]:
        """Valida e executa a ordem via broker_operator."""
        with self._lock:
            if not self._pode_operar(timestamp_vela):
                return None

            # Ativa bloqueio de trade
            self.trade_em_andamento = True

            # Atualiza cooldown específico para RSI
            if estrategia.startswith("RSI"):
                self.ultimo_id_disparado_rsi = timestamp_vela

            # Registra intenção de trade
            self._last_trade_timestamp = timestamp_vela
            self._last_trade_direction = direcao
            self._last_trade_strategy = estrategia
            self._last_trade_context = contexto
            self._trade_entry_price = contexto.get("preco_captura", 0.0)
            
            # Injeção de Risco no Contexto para o Broker
            contexto["tp_target"] = self.tp_percent
            contexto["sl_limit"] = self.sl_percent
            contexto["amount"] = self.min_amount

            # Envia ordem para o broker
            if self.broker_ops:
                logger.info(f"🎯 [DISPARO CONFIRMADO] {direcao} | Estratégia: {estrategia} | Valor: ${self.min_amount}")
                res = self.broker_ops.executar_ordem(direcao)
                if res and res.get("ok"):
                    self.trades_count += 1
                    return direcao
                else:
                    # BUG-CRIT-01 FIX: sem esse reset, trade_em_andamento fica True
                    # e o bot trava por 70s a cada falha do broker.
                    self.trade_em_andamento = False
                    logger.error(f"❌ Falha ao enviar ordem: {res}. Flag trade_em_andamento liberada.")
                    return None
            else:
                # BUG-CRIT-01 FIX: mesmo sem broker_ops, a flag deve ser limpa.
                self.trade_em_andamento = False
                logger.warning("⚠️ broker_ops não definido. Ordem não enviada. Flag liberada.")
                return None

    def processar_dados(self, ohlc: Dict, timestamp: float) -> Optional[str]:
        """
        Processa um candle de 5 segundos, avalia RSI e suporte/resistência,
        e retorna a direção da operação (CALL/PUT) ou None.
        """
        with self._lock:
            if not self.autopilot_ativo:
                return None

            # Extrai preços
            # BUG-CRIT-03: ohlc.get('high', 0) retorna None (não 0) quando a chave existe
            # mas com valor None (caso típico quando msg.get("max") é ausente no payload WS).
            # Usamos `or 0` para forçar fallback numérico seguro.
            close = ohlc.get('close')
            high  = ohlc.get('high') or 0.0
            low   = ohlc.get('low')  or 0.0

            if close is None:
                return None

            # Atualiza histórico de preços para o filtro de tendência imediata
            self.historico_precos.append(close)
            tendencia_baixa_5 = False
            if len(self.historico_precos) == 5:
                # Verifica se a tendência imediata é de baixa (preço caindo consistentemente nas últimas 5 velas)
                tendencia_baixa_5 = all(self.historico_precos[i] > self.historico_precos[i+1] for i in range(4))

            # --- 1. Armazenar a direção dos últimos candles ---
            if self.last_price > 0:
                self.historico_direcao.append(1 if close > self.last_price else -1)

            self.last_price = close
            self._warmup_candles += 1

            # --- 2. Lógica de Filtro de Tendência (Micro-momentum) ---
            tendencia = "LATERAL"
            if len(self.historico_direcao) >= 3:
                soma = sum(list(self.historico_direcao)[-3:])
                if soma == 3: tendencia = "ALTA"
                elif soma == -3: tendencia = "BAIXA"

            # FILTRO DE ANTI-DOJI / COMPRESSÃO (Volatilidade Mínima)
            # Aplicado APÓS o incremento do warmup para não bloquear a contagem.
            amplitude = high - low
            if amplitude < (close * 0.00005):  # Limiar de 0.005% do preço
                logger.debug(f"⚠️ Candle comprimido (amplitude={amplitude:.6f}). Análise ignorada, warmup contado.")
                # Atualiza RSI/SR mesmo em doji para manter os cálculos aquecidos
                self.rsi.add_price(close)
                self.sr.add_candle_ohlc(ohlc)
                return None

            # Atualiza RSI e Suporte/Resistência
            rsi_val = self.rsi.add_price(close)
            self.sr.add_candle_ohlc(ohlc)

            # Definição de Cooldown de Velas para RSI (usa constante de classe)
            rsi_cooldown_time = self.RSI_CANDLE_COOLDOWN

            segundo_local = int(timestamp) % self.timeframe

            contexto = {
                "rsi": round(rsi_val, 2) if rsi_val is not None else None,
                "preco_captura": close,
                "suporte": self.sr.current_support,
                "resistencia": self.sr.current_resistance,
                "segundo_vela": segundo_local
            }

            # 1. Sinal de Suporte/Resistência (com FILTRO DE EXAUSTÃO RSI)
            sinal_sr = self.sr.check_touch(close)
            if sinal_sr:
                # Filtro de Tendência de Baixa Forte (5 velas consecutivas)
                if tendencia_baixa_5 and sinal_sr == "CALL":
                    logger.info("🚫 FILTRO ATIVADO: Tendência de baixa forte detectada. CALL bloqueado.")
                    return None

                # --- 3. Filtro de Tendência Forte para SR ---
                if tendencia == "ALTA" and sinal_sr == "PUT":
                    logger.info("🚫 [SR BLOQUEADO] Tendência de ALTA forte detectada. Abortando PUT.")
                    return None
                if tendencia == "BAIXA" and sinal_sr == "CALL":
                    logger.info("🚫 [SR BLOQUEADO] Tendência de BAIXA forte detectada. Abortando CALL.")
                    return None

                if rsi_val is None:
                    # BUG-MOD-01 FIX: sinal SR era silenciosamente ignorado sem nenhum log
                    # quando o RSI ainda não estava pronto. Agora o operador vê o sinal potencial.
                    logger.info(f"⏳ [SR POTENCIAL] {sinal_sr} detectado, mas RSI ainda em warmup ({self._warmup_candles}/{self._min_candles_for_rsi}). Aguardando.")
                else:
                    # FILTRO DE EXAUSTÃO: Não compra no topo (RSI>=70) nem vende no fundo (RSI<=30)
                    if sinal_sr == "CALL" and rsi_val >= 70:
                        logger.warning(f"🚫 [SR EXAUSTÃO] Suporte tocado, mas RSI {rsi_val:.1f} indica sobrecompra. Abortando CALL.")
                        return None
                    if sinal_sr == "PUT" and rsi_val <= 30:
                        logger.warning(f"🚫 [SR EXAUSTÃO] Resistência tocada, mas RSI {rsi_val:.1f} indica sobrevenda. Abortando PUT.")
                        return None

                    logger.info(f"[SINAL SR] {sinal_sr} confirmado com RSI {rsi_val:.1f}")
                    return self.executar_disparo(sinal_sr, "SUPORTE_RESISTENCIA", timestamp, contexto)

            # 2. Sinal de RSI (Inversão Pura)
            if rsi_val is not None:
                if rsi_val <= self.rsi.oversold:
                    # Filtro de Tendência de Baixa Forte (5 velas consecutivas)
                    if tendencia_baixa_5:
                        logger.info("🚫 FILTRO ATIVADO: Tendência de baixa forte detectada. CALL bloqueado.")
                        return None

                    if tendencia == "BAIXA":
                        logger.info("⏳ [RSI FILTRADO] Sobrevenda detectada, mas tendência de BAIXA forte continua.")
                        return None

                    if timestamp <= self.ultimo_id_disparado_rsi + rsi_cooldown_time:
                        logger.info("⏳ Aguardando cooldown de velas para RSI (Oversold).")
                        return None
                    return self.executar_disparo("CALL", "RSI_OVERSOLD", timestamp, contexto)
                elif rsi_val >= self.rsi.overbought:
                    if tendencia == "ALTA":
                        logger.info("⏳ [RSI FILTRADO] Sobrecompra detectada, mas tendência de ALTA forte continua.")
                        return None

                    if timestamp <= self.ultimo_id_disparado_rsi + rsi_cooldown_time:
                        logger.info("⏳ Aguardando cooldown de velas para RSI (Overbought).")
                        return None
                    return self.executar_disparo("PUT", "RSI_OVERBOUGHT", timestamp, contexto)

            return None

    def processar_payload(self, data: Dict):
        """
        Processa o payload já convertido em dicionário vindo do Broker.
        """
        if not data:
            return

        try:
            with self._lock:
                nome_evento = data.get("name")

                if nome_evento == "candle-generated":
                    msg = data.get("msg", {})
                    active_id_raw = msg.get("active_id")
                    try:
                        active_id_recv = int(active_id_raw)
                    except (TypeError, ValueError):
                        active_id_recv = active_id_raw

                    # ⚡ DEBOUNCE ATÔMICO: Verifica se é uma nova vela de 5 segundos
                    timestamp_raw = msg.get("timestamp", time.time())
                    candle_id = int(timestamp_raw // 5) * 5
                    
                    if candle_id <= self._last_processed_candle_id:
                        return # Ignora ticks repetidos dentro do mesmo ciclo S5

                    # ⚡ 1. Extração inteligente do intervalo
                    intervalo = msg.get("interval")
                    if not intervalo:
                        intervalo = msg.get("size") or msg.get("period") or msg.get("time") or ""
                    
                    # Converte para string para comparação uniforme
                    intervalo_str = str(intervalo).strip() if intervalo is not None else ""
                    
                    # ⚡ 2. Contingência Ghost M1
                    if active_id_recv == self.target_active_id and not intervalo_str:
                        intervalo_str = "S5"
                    
                    _INTERVAL_S5_VALID = {"S5", "5", 5, "M1", "60", 60}
                    
                    # ⚡ 3. Filtros de validação
                    if active_id_recv != self.target_active_id:
                        return
                    
                    if intervalo_str not in _INTERVAL_S5_VALID:
                        logger.warning(
                            f"⚠️ Candle recebido mas FILTRADO: active_id={active_id_recv} | intervalo='{intervalo_str}'"
                        )
                        return

                    # ✨ CORREÇÃO: Atribuição ÚNICA e segura após passar por todos os filtros de validação
                    self._last_processed_candle_id = candle_id

                    # Monta o candle com os campos esperados
                    candle = {
                        "open": msg.get("open"),
                        "high": msg.get("max"),
                        "low": msg.get("min"),
                        "close": msg.get("close"),
                        "current": msg.get("close"),
                        "volume": msg.get("volume", 0)
                    }
                    
                    # ✨ CORREÇÃO: Mantém o timestamp original/real para evitar o lock falso de sub-segundos
                    timestamp = timestamp_raw 
                    
                    # Feedback visual imediato no terminal
                    logger.info(f"📊 [CICLO S5 FECHADO] Preço: {candle['close']} | ID: {candle_id}")
                    
                    sinal = self.processar_dados(candle, timestamp)
                    if sinal:
                        logger.info(f"[WS] Sinal gerado: {sinal}")

                elif nome_evento == "order-closed":
                    msg_payload = data.get("msg", {})
                    lucro = float(msg_payload.get("profit", 0.0))
                    preco_fechamento = float(msg_payload.get("close_price", msg_payload.get("value", 0.0)))
                    resultado = "win" if lucro > 0 else "loss"

                    if resultado == "win":
                        self.wins += 1
                    else:
                        self.losses += 1

                    self._aplicar_cooldown_apos_trade(resultado)

                    dados_trade = {
                        "trade_id": f"T_{int(time.time())}",
                        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "estrategia_gatilho": self._last_trade_strategy,
                        "direcao": self._last_trade_direction,
                        "resultado": resultado.upper(),
                        "lucro_pnl": lucro,
                        "preco_entrada": self._trade_entry_price,
                        "preco_saida": preco_fechamento,
                        "contexto": {
                            **self._last_trade_context,
                            "active_id": self.target_active_id
                        },
                        "estado_sessao": {
                            "placar": f"{self.wins}W - {self.losses}L",
                            "losses_consecutivos": self.losses_consecutivos
                        }
                    }
                    self.trade_em_andamento = False  # Libera o bot para novas operações
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(salvar_trade_json_raiz(dados_trade))
                    except RuntimeError:
                        # BUG-MOD-03 FIX: asyncio.run() bloqueava a thread do navegador
                        # indefinidamente como fallback. Usando Thread separada para não
                        # interferir com o loop do Playwright.
                        import threading as _th
                        _th.Thread(
                            target=lambda: asyncio.run(salvar_trade_json_raiz(dados_trade)),
                            daemon=True
                        ).start()
                    logger.info(f"📊 Trade {resultado.upper()} registrado. Placar: {self.wins}W/{self.losses}L")

        except Exception as e:
            logger.error(f"Erro no processamento de payload: {e}")

    def processar_ws(self, payload: str):
        """Trata e limpa a string do WebSocket suportando Engine.io/Socket.io antes do parse."""
        try:
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8', errors='ignore')
            
            cleaned = payload.strip()
            
            # Remove os prefixos numéricos comuns do protocolo Socket.io (ex: 42["evento", ...])
            if cleaned.startswith("42["):
                cleaned = cleaned[2:]
            elif cleaned.startswith("42"):
                cleaned = cleaned[2:]
                
            data = json.loads(cleaned)
            
            # Se o Socket.io estruturou como uma lista: ["nome_evento", {conteudo}]
            if isinstance(data, list) and len(data) >= 2:
                data = {"name": data[0], "msg": data[1]}
                
            if isinstance(data, dict):
                self.processar_payload(data)
            else:
                logger.debug(f"Payload ignorado por não ser estruturado: {str(cleaned)[:100]}")
        except Exception as e:
            logger.error(f"Erro no parsing JSON do WebSocket: {e} | Payload bruto inicial: {str(payload)[:150]}")

    def get_status(self) -> Dict:
        """Retorna o estado atual do robô para monitoramento."""
        with self._lock:
            agora = time.time()
            cooldown = max(0, int(self._cooldown_until - agora))
            return {
                "status": "ACTIVE" if self.autopilot_ativo else "IDLE",
                "cooldown_restante_s": cooldown,
                "trades_realizados": self.trades_count,
                "max_trades": self.max_trades_session,
                "placar": f"{self.wins}W - {self.losses}L",
                "losses_consecutivos": self.losses_consecutivos,
                "rsi_atual": round(self.rsi.current_rsi, 2) if self.rsi.current_rsi is not None else "WARMUP",
                "suporte": round(self.sr.current_support, 6) if self.sr.current_support else None,
                "resistencia": round(self.sr.current_resistance, 6) if self.sr.current_resistance else None,
                "ultimo_preco": self.last_price,
                "warmup_restante": max(0, self._min_candles_for_rsi - self._warmup_candles) # S5
            }

    def perceive_and_act(self) -> Dict:
        """Método de compatibilidade com main2.py. Retorna estado básico."""
        return {
            "cycle_id": "0",
            "state": "ACTIVE" if self.autopilot_ativo else "IDLE",
            "recommended_action": "WAIT",
            "details": self.get_status()
        }

    # Métodos auxiliares para compatibilidade com a interface esperada
    def attach(self, page):
        self._active_page = page

    def get_balance(self):
        return None

    def request_stop(self):
        with self._lock:
            self.autopilot_ativo = False

    def marcar_conexao_ws(self):
        """Método de compatibilidade para o sinal de warm-up do WebSocket."""
        logger.info("🔌 Sincronização de conexão WebSocket registrada.")

# Instância global (singleton)
alpha_engine = AlphaEngine(tolerance=0.0002, max_trades_session=999999)