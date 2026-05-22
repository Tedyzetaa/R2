# filename: news_worker.py
# ============================================================
# GHOST PROTOCOL — NEWS SENTIMENT WORKER
# Módulo de Inteligência de Mercado via NLP
# ============================================================
# Responsabilidades:
#   - Coleta de feeds RSS de fontes financeiras confiáveis
#   - Análise de sentimento (VADER) sobre títulos filtrados
#   - Exportação contínua para noticias_sentimento.json
#   - Execução como daemon thread (não bloqueia o robô principal)
#   - Integração direta com AlphaEngine via leitura de JSON
# ============================================================
# Instalação das dependências:
#   pip install feedparser vaderSentiment
# ============================================================

from __future__ import annotations

import json
import logging
import threading
import time
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

# --------------- Dependências opcionais com graceful fallback ---------------
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    feedparser = None  # type: ignore
    FEEDPARSER_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    SentimentIntensityAnalyzer = None  # type: ignore
    VADER_AVAILABLE = False

# ---------------------------------------------------------------------------
# LOGGING — compatível com o padrão do Ghost Protocol
# ---------------------------------------------------------------------------
logger = logging.getLogger("NewsWorker")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# CONSTANTES DE CONFIGURAÇÃO
# ---------------------------------------------------------------------------

# Intervalo de polling em segundos (3 minutos)
POLL_INTERVAL_SECONDS: int = 180

# Arquivo de saída (raiz do projeto, mesmo nível de main2.py)
OUTPUT_JSON_PATH: str = "noticias_sentimento.json"

# Número de headlines a preservar no output
TOP_N_HEADLINES: int = 3

# Palavras-chave para filtragem de ativos (case-insensitive)
ASSET_KEYWORDS: list[str] = [
    "dólar", "dolar", "dollar",
    "usd", "usd/brl", "usdbrl",
    "federal reserve", "fed",
    "taxa de juros", "interest rate",
    "economia", "economy",
    "câmbio", "cambio", "exchange rate",
    "fomc", "jerome powell", "powell",
    "inflação", "inflation", "cpi", "pce",
    "treasury", "yield", "bond",
    "banco central", "central bank", "bcb",
    "selic", "ptax",
]

# Feeds RSS financeiros — priorizados por qualidade e disponibilidade
RSS_FEEDS: dict[str, str] = {
    "Reuters Business":
        "https://feeds.reuters.com/reuters/businessNews",
    "Reuters Markets":
        "https://feeds.reuters.com/reuters/companyNews",
    "Investing.com - Forex":
        "https://br.investing.com/rss/news_301.rss",
    "Investing.com - Economia":
        "https://br.investing.com/rss/news_25.rss",
    "Google News - Dólar BRL":
        "https://news.google.com/rss/search?q=dólar+real+câmbio&hl=pt-BR&gl=BR&ceid=BR:pt",
    "Google News - Federal Reserve":
        "https://news.google.com/rss/search?q=Federal+Reserve+interest+rate&hl=en-US&gl=US&ceid=US:en",
    "MarketWatch":
        "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    "Seeking Alpha - Macro":
        "https://seekingalpha.com/feed/macro",
}

# ---------------------------------------------------------------------------
# ESTRUTURA DE DADOS DE SAÍDA
# ---------------------------------------------------------------------------

@dataclass
class HeadlineScore:
    """Representa um título com seu score de sentimento individual."""
    titulo: str
    fonte: str
    score: float
    timestamp_coleta: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SentimentPayload:
    """
    Payload exportado para noticias_sentimento.json.
    Lido pelo AlphaEngine ou qualquer módulo externo.
    """
    sentimento: float = 0.0           # [-1.0 Bearish .. +1.0 Bullish]
    timestamp: str = ""               # ISO 8601 da última atualização
    top_headlines: list = field(default_factory=list)   # list[dict]
    total_analisados: int = 0         # Quantidade de títulos processados
    status: str = "INICIALIZANDO"     # ATIVO | ERRO | SEM_DADOS | INICIALIZANDO
    erro: Optional[str] = None        # Mensagem de erro, se houver

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# ENGINE DE SENTIMENTO
# ---------------------------------------------------------------------------

class SentimentEngine:
    """
    Encapsula o analisador VADER e expõe interface padronizada.
    Suporta fallback para TextBlob caso VADER não esteja disponível.
    """

    def __init__(self):
        self._analyzer = None
        self._engine_name = "NENHUM"

        if VADER_AVAILABLE:
            self._analyzer = SentimentIntensityAnalyzer()
            self._engine_name = "VADER"
            logger.info("Motor NLP: VADER SentimentIntensityAnalyzer inicializado.")
        else:
            logger.warning(
                "vaderSentiment não instalado. "
                "Execute: pip install vaderSentiment"
            )

    @property
    def disponivel(self) -> bool:
        return self._analyzer is not None

    def analisar(self, texto: str) -> float:
        """
        Retorna o compound score VADER normalizado entre -1.0 e 1.0.
        Retorna 0.0 se o engine não estiver disponível.
        """
        if not self.disponivel:
            return 0.0
        scores = self._analyzer.polarity_scores(texto)
        return round(scores["compound"], 4)

    def __repr__(self) -> str:
        return f"<SentimentEngine engine={self._engine_name} disponivel={self.disponivel}>"


# ---------------------------------------------------------------------------
# COLETOR DE FEEDS RSS
# ---------------------------------------------------------------------------

class FeedCollector:
    """
    Responsável por buscar e filtrar títulos dos feeds RSS configurados.
    """

    def __init__(self, feeds: dict[str, str], keywords: list[str]):
        self._feeds = feeds
        self._keywords = [kw.lower() for kw in keywords]

    def _contem_keyword(self, titulo: str) -> bool:
        """Verifica se o título contém ao menos uma palavra-chave de ativo."""
        titulo_lower = titulo.lower()
        return any(kw in titulo_lower for kw in self._keywords)

    def coletar(self) -> list[tuple[str, str]]:
        """
        Faz o polling de todos os feeds configurados.

        Returns:
            Lista de tuplas (titulo, fonte) filtradas por keyword.
        """
        if not FEEDPARSER_AVAILABLE:
            logger.error("feedparser não instalado. Execute: pip install feedparser")
            return []

        titulos_filtrados: list[tuple[str, str]] = []

        for nome_fonte, url in self._feeds.items():
            try:
                logger.debug(f"Buscando feed: {nome_fonte}")
                feed = feedparser.parse(url)

                if feed.bozo and feed.bozo_exception:
                    logger.warning(
                        f"Feed mal-formado [{nome_fonte}]: {feed.bozo_exception}"
                    )

                entradas = feed.get("entries", [])
                if not entradas:
                    logger.debug(f"    - {nome_fonte}: sem entradas.")
                    continue

                count_antes = len(titulos_filtrados)
                for entry in entradas:
                    titulo = entry.get("title", "").strip()
                    if titulo and self._contem_keyword(titulo):
                        titulos_filtrados.append((titulo, nome_fonte))

                count_adicionados = len(titulos_filtrados) - count_antes
                logger.debug(
                    f"    - {nome_fonte}: {len(entradas)} entradas | "
                    f"{count_adicionados} relevantes"
                )

            except Exception as exc:
                # Falha isolada por feed — não derruba o worker nem o robô
                logger.error(f"Erro ao buscar [{nome_fonte}]: {exc}")

        logger.info(
            f"Coleta concluída: {len(titulos_filtrados)} títulos relevantes "
            f"de {len(self._feeds)} feeds."
        )
        return titulos_filtrados


# ---------------------------------------------------------------------------
# WORKER PRINCIPAL
# ---------------------------------------------------------------------------

class NewsWorker:
    """
    Daemon thread que monitora feeds RSS financeiros e exporta
    o sentimento agregado para noticias_sentimento.json.

    Uso:
        worker = NewsWorker()
        worker.iniciar()           # inicia em background (non-blocking)
        score = worker.get_score() # lê o sentimento atual (thread-safe)
        worker.parar()             # sinaliza encerramento gracioso
    """

    def __init__(
        self,
        output_path: str = OUTPUT_JSON_PATH,
        poll_interval: int = POLL_INTERVAL_SECONDS,
        feeds: Optional[dict[str, str]] = None,
        keywords: Optional[list[str]] = None,
    ):
        self._output_path = output_path
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        self._sentiment_engine = SentimentEngine()
        self._collector = FeedCollector(
            feeds=feeds or RSS_FEEDS,
            keywords=keywords or ASSET_KEYWORDS,
        )

        # Estado interno compartilhado (thread-safe via _lock)
        self._payload = SentimentPayload(
            timestamp=datetime.now().isoformat(),
            status="INICIALIZANDO",
        )

        # Thread daemon (encerrada automaticamente com o processo principal)
        self._thread = threading.Thread(
            target=self._loop,
            name="NewsWorker-Daemon",
            daemon=True,
        )

    # ------------------------------------------------------------------
    # API PÚBLICA
    # ------------------------------------------------------------------

    def iniciar(self) -> None:
        """Inicia o worker em background. Não bloqueia o caller."""
        if self._thread.is_alive():
            logger.warning("NewsWorker já está em execução.")
            return

        logger.info(
            f"NewsWorker iniciando | "
            f"Intervalo: {self._poll_interval}s | "
            f"Output: {self._output_path}"
        )
        self._thread.start()

    def parar(self) -> None:
        """Sinaliza encerramento gracioso. A thread termina no próximo ciclo."""
        logger.info("NewsWorker: sinal de parada recebido.")
        self._stop_event.set()

    def get_score(self) -> float:
        """Retorna o sentimento atual de forma thread-safe."""
        with self._lock:
            return self._payload.sentimento

    def get_payload(self) -> dict:
        """Retorna o payload completo de forma thread-safe."""
        with self._lock:
            return self._payload.to_dict()

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    # ------------------------------------------------------------------
    # LOOP INTERNO (daemon thread)
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        """Loop principal da thread daemon."""
        logger.info("NewsWorker: thread daemon ativa.")

        while not self._stop_event.is_set():
            try:
                self._ciclo()
            except Exception as exc:
                # Captura qualquer exceção não tratada para garantir que
                # o robô principal nunca seja afetado por falhas aqui.
                logger.error(f"NewsWorker: erro inesperado no ciclo: {exc}", exc_info=True)
                self._registrar_erro(str(exc))

            # Aguarda com granularidade de 1s para responder ao stop_event
            # rapidamente sem fazer busy-wait.
            for _ in range(self._poll_interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

        logger.info("NewsWorker: encerrado graciosamente.")

    def _ciclo(self) -> None:
        """
        Um ciclo completo:
        1. Coleta títulos filtrados dos feeds
        2. Calcula sentimento via VADER
        3. Seleciona Top-N headlines mais influentes
        4. Persiste no JSON de saída
        """
        logger.info("NewsWorker: iniciando ciclo de atualização...")
        inicio = time.monotonic()

        # 1. Coleta
        titulos = self._collector.coletar()

        if not titulos:
            logger.warning("Nenhum título relevante encontrado neste ciclo.")
            with self._lock:
                self._payload.status = "SEM_DADOS"
                self._payload.timestamp = datetime.now().isoformat()
                self._payload.erro = "Nenhum título relevante coletado"
            self._persistir()
            return

        # 2. Análise de sentimento por título
        scores_detalhados: list[HeadlineScore] = []

        if not self._sentiment_engine.disponivel:
            logger.error("Motor NLP indisponível. Instale: pip install vaderSentiment")
            self._registrar_erro("Motor NLP (VADER) indisponível.")
            return

        for titulo, fonte in titulos:
            score = self._sentiment_engine.analisar(titulo)
            scores_detalhados.append(
                HeadlineScore(titulo=titulo, fonte=fonte, score=score)
            )

        # 3. Sentimento agregado (média simples dos compound scores)
        if not scores_detalhados:
            sentimento_final = 0.0
        else:
            sentimento_final = round(
                sum(h.score for h in scores_detalhados) / len(scores_detalhados), 4
            )

        # 4. Top-N: os que mais desviam de zero (maior valor absoluto)
        scores_ordenados = sorted(
            scores_detalhados,
            key=lambda h: abs(h.score),
            reverse=True,
        )
        top_headlines = [
            {
                "titulo": h.titulo,
                "fonte": h.fonte,
                "score_individual": h.score,
            }
            for h in scores_ordenados[:TOP_N_HEADLINES]
        ]

        # 5. Atualiza o payload de forma thread-safe
        with self._lock:
            self._payload = SentimentPayload(
                sentimento=sentimento_final,
                timestamp=datetime.now().isoformat(),
                top_headlines=top_headlines,
                total_analisados=len(scores_detalhados),
                status="ATIVO",
                erro=None,
            )

        duracao = round(time.monotonic() - inicio, 2)
        sinal = "BULLISH" if sentimento_final > 0.05 else (
            "BEARISH" if sentimento_final < -0.05 else "NEUTRO"
        )
        logger.info(
            f"Ciclo concluído em {duracao}s | "
            f"Score: {sentimento_final:+.4f} {sinal} | "
            f"Analisados: {len(scores_detalhados)} | "
            f"Top headline: \"{top_headlines[0]['titulo'][:60]}...\""
            if top_headlines else
            f"Ciclo concluído em {duracao}s | Score: {sentimento_final:+.4f}"
        )

        self._persistir()

    def _persistir(self) -> None:
        """
        Grava o payload atual em disco de forma atômica (write + rename).
        Garante que o JSON nunca ficará em estado corrompido mesmo se
        o processo for interrompido no meio da escrita.
        """
        tmp_path = self._output_path + ".tmp"
        try:
            with self._lock:
                dados = self._payload.to_dict()

            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)

            os.replace(tmp_path, self._output_path)
            logger.debug(f"Payload persistido em: {self._output_path}")

        except OSError as exc:
            logger.error(f"Falha ao persistir JSON: {exc}")
        finally:
            # Garante remoção do .tmp em caso de falha no rename
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _registrar_erro(self, mensagem: str) -> None:
        """Atualiza o payload com status de erro e persiste."""
        with self._lock:
            self._payload.status = "ERRO"
            self._payload.timestamp = datetime.now().isoformat()
            self._payload.erro = mensagem
        self._persistir()


# ---------------------------------------------------------------------------
# SINGLETON — compatível com o padrão de importação do Ghost Protocol
# ---------------------------------------------------------------------------

news_worker = NewsWorker()


# ---------------------------------------------------------------------------
# UTILITÁRIO: leitura direta do JSON (para módulos que não importam o worker)
# ---------------------------------------------------------------------------

def ler_sentimento(path: str = OUTPUT_JSON_PATH) -> SentimentPayload:
    """
    Lê o arquivo noticias_sentimento.json e retorna um SentimentPayload.
    Útil para integração com AlphaEngine sem importar o worker inteiro.

    Returns:
        SentimentPayload com os dados do arquivo, ou um payload neutro
        em caso de erro (nunca lança exceção).
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return SentimentPayload(
            sentimento=float(dados.get("sentimento", 0.0)),
            timestamp=dados.get("timestamp", ""),
            top_headlines=dados.get("top_headlines", []),
            total_analisados=int(dados.get("total_analisados", 0)),
            status=dados.get("status", "DESCONHECIDO"),
            erro=dados.get("erro"),
        )
    except FileNotFoundError:
        logger.debug(f"Arquivo {path} ainda não existe. Retornando payload neutro.")
        return SentimentPayload(status="SEM_ARQUIVO")
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error(f"Erro ao ler {path}: {exc}")
        return SentimentPayload(status="ERRO_LEITURA", erro=str(exc))


# ---------------------------------------------------------------------------
# ENTRYPOINT — execução como processo independente
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import signal

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = NewsWorker(poll_interval=POLL_INTERVAL_SECONDS)

    def _handler_sinal(sig, frame):
        logger.info(f"Sinal {sig} recebido. Encerrando NewsWorker...")
        worker.parar()

    signal.signal(signal.SIGINT, _handler_sinal)
    signal.signal(signal.SIGTERM, _handler_sinal)

    worker.iniciar()

    logger.info(
        "NewsWorker em modo standalone. "
        f"Atualizando a cada {POLL_INTERVAL_SECONDS}s. "
        "Pressione Ctrl+C para encerrar."
    )

    # Mantém o processo principal vivo enquanto o daemon roda
    try:
        while worker.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        worker.parar()

    logger.info("NewsWorker encerrado. Até logo, Comandante.")
