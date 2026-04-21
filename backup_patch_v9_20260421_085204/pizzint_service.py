"""
PizzaINTService — Módulo de Inteligência Geopolítica / Nível DEFCON
Versão: 3.0 TACTICAL
Correções: mapeamento DEFCON 1-5 real, fallback multi-fonte, scraping robusto
Expansões: RSS feeds de agências primárias, sistema de peso por categoria,
           sumário narrativo de ameaças, histórico de variação, links diretos
"""

import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

# ─── Constantes ───────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Pesos por categoria de ameaça ─────────────────────────────────────────────
# Cada palavra-chave encontrada no texto soma seu peso ao score bruto
CATEGORIAS_AMEACA = {
    "nuclear": {
        "palavras": ["nuclear", "nuke", "warhead", "icbm", "plutonium", "uranium",
                     "atomic", "radiation leak", "dirty bomb", "silo"],
        "peso": 15,
    },
    "guerra_direta": {
        "palavras": ["war declared", "invasion", "troops crossed", "airstrike",
                     "bombing", "attack launched", "military offensive", "shelling"],
        "peso": 12,
    },
    "escalada_militar": {
        "palavras": ["defcon", "mobilization", "troops deployed", "pentagon",
                     "nato activated", "military buildup", "alert level", "escalation",
                     "armed forces", "carrier strike group"],
        "peso": 8,
    },
    "crise_diplomatica": {
        "palavras": ["sanctions", "ambassador recalled", "expelled", "ultimatum",
                     "crisis talks", "emergency session", "ceasefire collapsed",
                     "summit cancelled", "treaty violated"],
        "peso": 5,
    },
    "tensao_regional": {
        "palavras": ["conflict", "tension", "skirmish", "border dispute",
                     "protest", "coup", "unrest", "civil war", "rebel",
                     "hostage", "threat", "alert", "crisis", "war", "attack"],
        "peso": 2,
    },
    "monitoramento": {
        "palavras": ["missile test", "drill", "exercise", "surveillance",
                     "intelligence", "cyber attack", "hacker", "espionage",
                     "pizza meter", "defcon meter"],
        "peso": 3,
    },
}

# ── Mapeamento score → DEFCON ─────────────────────────────────────────────────
# DEFCON 5 = paz / DEFCON 1 = guerra nuclear iminente
DEFCON_THRESHOLDS = [
    (80, 1, "🔴 DEFCON 1", "GUERRA NUCLEAR IMINENTE",   "#ff0000"),
    (50, 2, "🔴 DEFCON 2", "FORÇAS ARMADAS EM ALERTA",  "#ff4400"),
    (25, 3, "🟠 DEFCON 3", "FORÇAS AÉREAS EM PRONTIDÃO","#ff8800"),
    (10, 4, "🟡 DEFCON 4", "TENSÃO ELEVADA",             "#ffcc00"),
    (0,  5, "✅ DEFCON 5", "CONDIÇÃO DE PAZ",            "#00ff88"),
]

# ── Fontes de notícias (RSS) ──────────────────────────────────────────────────
RSS_FEEDS = [
    {
        "nome": "Reuters World",
        "url": "https://feeds.reuters.com/reuters/worldNews",
        "prioridade": 1,
    },
    {
        "nome": "AP News Top",
        "url": "https://feeds.apnews.com/rss/apf-topnews",
        "prioridade": 1,
    },
    {
        "nome": "BBC World",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "prioridade": 2,
    },
    {
        "nome": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "prioridade": 2,
    },
    {
        "nome": "Defense News",
        "url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
        "prioridade": 1,
    },
    {
        "nome": "The Drive (War Zone)",
        "url": "https://www.thedrive.com/feed",
        "prioridade": 2,
    },
]


# ══════════════════════════════════════════════════════════════════════════════
def _get_safe(url: str, timeout: int = 12) -> requests.Response | None:
    """GET seguro com timeout e headers."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None


def _calcular_score_e_hits(texto: str) -> tuple[int, dict]:
    """
    Varre o texto e calcula o score bruto de ameaça.
    Retorna (score_total, {categoria: {palavra: contagem}})
    """
    texto_lower = texto.lower()
    score = 0
    hits  = {}

    for cat, dados in CATEGORIAS_AMEACA.items():
        hits[cat] = {}
        for palavra in dados["palavras"]:
            count = texto_lower.count(palavra)
            if count:
                hits[cat][palavra] = count
                score += count * dados["peso"]

    return score, hits


def _score_para_defcon(score: int) -> dict:
    """Mapeia score numérico para nível DEFCON estruturado."""
    for threshold, nivel, label, descricao, cor in DEFCON_THRESHOLDS:
        if score >= threshold:
            return {
                "nivel":     nivel,
                "label":     label,
                "descricao": descricao,
                "cor_hex":   cor,
                "score":     score,
            }
    # Fallback seguro
    return {
        "nivel": 5, "label": "✅ DEFCON 5",
        "descricao": "CONDIÇÃO DE PAZ", "cor_hex": "#00ff88", "score": score,
    }


def _parse_rss(url: str, limite: int = 5) -> list[dict]:
    """
    Parseia feed RSS e extrai título, link e data.
    Funciona com feeds Atom e RSS 2.0.
    """
    noticias = []
    r = _get_safe(url, timeout=10)
    if not r:
        return noticias

    try:
        root = ET.fromstring(r.content)
        ns   = {"atom": "http://www.w3.org/2005/Atom"}

        # ── RSS 2.0 ──
        items = root.findall(".//item")
        for item in items[:limite]:
            titulo = item.findtext("title", "").strip()
            link   = item.findtext("link", "").strip()
            data   = item.findtext("pubDate", "").strip()
            desc   = item.findtext("description", "").strip()
            if titulo and link:
                noticias.append({
                    "titulo": titulo,
                    "url":    link,
                    "data":   data,
                    "desc":   BeautifulSoup(desc, "html.parser").get_text()[:200] if desc else "",
                })

        # ── Atom ──
        if not noticias:
            entries = root.findall(".//atom:entry", ns) or root.findall(".//entry")
            for entry in entries[:limite]:
                titulo = (
                    entry.findtext("atom:title", "", ns) or
                    entry.findtext("title", "")
                ).strip()
                link_el = entry.find("atom:link", ns) or entry.find("link")
                link    = (link_el.get("href", "") if link_el is not None else "").strip()
                data    = (
                    entry.findtext("atom:updated", "", ns) or
                    entry.findtext("updated", "")
                ).strip()
                if titulo and link:
                    noticias.append({"titulo": titulo, "url": link, "data": data, "desc": ""})

    except ET.ParseError:
        pass

    return noticias


# ══════════════════════════════════════════════════════════════════════════════
class PizzaINTService:
    """
    Serviço de Inteligência Geopolítica com cálculo de DEFCON.
    Fontes: PizzINT.watch + RSS de agências internacionais.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.url_primario = "https://www.pizzint.watch/"
        self._historico_scores: list[int] = []   # Rastreia variação no tempo

    # ══════════════════════════════════════════════════════════════════════════
    # FONTE 1: PizzINT.watch (scraping HTML)
    # ══════════════════════════════════════════════════════════════════════════

    def _scrape_pizzint(self) -> tuple[int, list[dict], str]:
        """
        Raspa o site PizzINT e retorna (score_bruto, noticias, texto_raw).
        """
        print("🍕 [PizzINT] Infiltrando pizzint.watch...")
        r = _get_safe(self.url_primario, timeout=15)
        if not r:
            print("⚠️  [PizzINT] Site primário offline.")
            return 0, [], ""

        soup  = BeautifulSoup(r.text, "html.parser")
        texto = soup.get_text()
        score, _ = _calcular_score_e_hits(texto)

        # ── Extração de links/manchetes ───────────────────────────────────
        noticias = []
        seen = set()
        for tag in soup.find_all(["a", "h1", "h2", "h3", "p"]):
            if tag.name == "a" and tag.get("href"):
                titulo = tag.get_text(strip=True)
                href   = tag["href"]
                if (len(titulo) > 25 and "http" not in titulo
                        and titulo not in seen):
                    url_completa = urllib.parse.urljoin(self.url_primario, href)
                    noticias.append({
                        "titulo": titulo,
                        "url":    url_completa,
                        "fonte":  "PizzINT",
                        "data":   "",
                        "desc":   "",
                    })
                    seen.add(titulo)
                    if len(noticias) >= 6:
                        break

        print(f"✅ [PizzINT] Score bruto: {score} | {len(noticias)} notícias capturadas.")
        return score, noticias, texto

    # ══════════════════════════════════════════════════════════════════════════
    # FONTE 2: RSS de agências primárias
    # ══════════════════════════════════════════════════════════════════════════

    def _coletar_rss(self, limite_por_feed: int = 4) -> tuple[int, list[dict]]:
        """
        Coleta notícias de todos os RSS feeds e calcula score de ameaça.
        Retorna (score_total_rss, lista_noticias).
        """
        print("📡 [RSS] Varrendo feeds de agências internacionais...")
        todas_noticias = []
        score_total    = 0

        for feed in RSS_FEEDS:
            print(f"   ↳ {feed['nome']}...")
            items = _parse_rss(feed["url"], limite=limite_por_feed)
            for item in items:
                # Calcula score individual da manchete + descrição
                texto_item  = f"{item['titulo']} {item['desc']}"
                score_item, hits = _calcular_score_e_hits(texto_item)
                score_total += score_item

                # Adiciona categoria detectada
                categorias_hit = [c for c, h in hits.items() if h]
                todas_noticias.append({
                    **item,
                    "fonte":       feed["nome"],
                    "score_item":  score_item,
                    "categorias":  categorias_hit,
                })

        # Ordena por relevância (score_item desc)
        todas_noticias.sort(key=lambda x: x["score_item"], reverse=True)

        print(f"✅ [RSS] {len(todas_noticias)} manchetes | Score RSS: {score_total}")
        return score_total, todas_noticias

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════

    def get_status(self) -> dict:
        """
        Executa coleta completa e retorna pacote de inteligência DEFCON.
        Compatível com o WebSocket do R2 (chave 'level' preservada).
        """
        print("\n" + "═"*55)
        print("🍕 [PizzINT FULL INTEL] Iniciando varredura geopolítica...")
        print("═"*55)
        inicio = time.time()

        # ── 1. PizzINT scraping ───────────────────────────────────────────
        score_pizzint, noticias_pizzint, texto_raw = self._scrape_pizzint()

        # ── 2. RSS feeds ──────────────────────────────────────────────────
        score_rss, noticias_rss = self._coletar_rss(limite_por_feed=5)

        # ── 3. Score consolidado ──────────────────────────────────────────
        # Peso: PizzINT 40% + RSS 60% (normalizado a 0-100)
        score_bruto = score_pizzint + score_rss
        # Normaliza para 0-100 (teto em 150 pontos brutos = 100%)
        score_normalizado = min(100, int((score_bruto / 150) * 100))

        # ── 4. DEFCON ─────────────────────────────────────────────────────
        defcon = _score_para_defcon(score_normalizado)

        # ── 5. Histórico e variação ───────────────────────────────────────
        self._historico_scores.append(score_normalizado)
        if len(self._historico_scores) > 10:
            self._historico_scores.pop(0)

        if len(self._historico_scores) >= 2:
            variacao = score_normalizado - self._historico_scores[-2]
            tendencia = "↑ ESCALANDO" if variacao > 5 else ("↓ DEESCALANDO" if variacao < -5 else "→ ESTÁVEL")
        else:
            variacao, tendencia = 0, "→ ESTÁVEL"

        # ── 6. Noticias unificadas e deduplicadas ─────────────────────────
        todas_noticias = []
        titulos_vistos = set()
        # Prioriza notícias com score alto do RSS
        for n in noticias_rss + noticias_pizzint:
            titulo_key = n["titulo"][:60].lower()
            if titulo_key not in titulos_vistos:
                titulos_vistos.add(titulo_key)
                todas_noticias.append(n)
            if len(todas_noticias) >= 15:
                break

        # ── 7. Análise de categorias dominantes ───────────────────────────
        score_cats, hits_total = _calcular_score_e_hits(
            " ".join(n["titulo"] for n in todas_noticias)
        )
        cats_ativas = sorted(
            [(c, sum(hits_total[c].values()) if hits_total.get(c) else 0)
             for c in hits_total],
            key=lambda x: x[1], reverse=True
        )
        cats_texto = " | ".join(
            f"{c.upper()}: {v}" for c, v in cats_ativas if v > 0
        ) or "Nenhuma ameaça detectada"

        resultado = {
            # ── Compatibilidade com WebSocket legado ──────────────────────
            "level":   score_normalizado,     # ← preservado para main2.py
            "news":    [                       # ← preservado (formato antigo)
                {"titulo": n["titulo"], "url": n["url"]}
                for n in todas_noticias[:4]
            ],

            # ── Dados expandidos ──────────────────────────────────────────
            "defcon":          defcon,
            "score_bruto":     score_bruto,
            "score_normalizado": score_normalizado,
            "tendencia":       tendencia,
            "variacao":        variacao,
            "historico":       list(self._historico_scores),
            "categorias":      cats_texto,
            "noticias_completas": todas_noticias,
            "fontes_ativas":   [f["nome"] for f in RSS_FEEDS] + ["PizzINT.watch"],
            "timestamp":       time.strftime("%d/%m/%Y %H:%M:%S"),
            "duracao_s":       round(time.time() - inicio, 1),
        }

        print(
            f"\n🍕 [PizzINT] Concluído em {resultado['duracao_s']}s | "
            f"{defcon['label']} | Score: {score_normalizado}/100 | {tendencia}"
        )
        return resultado

    # ══════════════════════════════════════════════════════════════════════════
    # HTML para injeção no WebSocket R2
    # ══════════════════════════════════════════════════════════════════════════

    def gerar_html_painel(self, status: dict = None) -> str:
        """
        Gera HTML tático para o painel do R2.
        Chame get_status() antes, ou deixe gerar automaticamente.
        """
        if status is None:
            status = self.get_status()

        defcon = status.get("defcon", {})
        cor    = defcon.get("cor_hex", "#00ff88")
        nots   = status.get("noticias_completas", [])[:8]

        noticias_html = "".join(
            f'&nbsp;• <a href="{n["url"]}" target="_blank" '
            f'style="color:#88aaff;text-decoration:none;">'
            f'[{n.get("fonte","?")}] {n["titulo"][:80]}</a>'
            f'{(" — " + n["desc"][:80]) if n.get("desc") else ""}<br>'
            for n in nots
        )

        html = f"""
<div style="font-family:'Share Tech Mono',monospace;font-size:12px;line-height:1.8;color:#ccc;">
<b style="color:{cor};font-size:15px;">
  🍕 {defcon.get('label','N/A')} — {defcon.get('descricao','N/A')}
</b><br>
<span style="color:#aaa;">
  Score: {status.get('score_normalizado',0)}/100 | 
  Bruto: {status.get('score_bruto',0)} pts | 
  Tendência: {status.get('tendencia','?')}
</span>
<hr style="border-color:#333;"/>
<b>🗂️ Categorias de Ameaça Detectadas:</b><br>
&nbsp;{status.get('categorias','Nenhuma')}<br>
<br><b>📰 Inteligência de Fontes ({len(status.get('fontes_ativas',[]))} feeds):</b><br>
{noticias_html if noticias_html else "&nbsp;Nenhuma manchete crítica detectada."}
<hr style="border-color:#333;"/>
<span style="color:#555;">
  Coleta: {status.get('timestamp','?')} | 
  Duração: {status.get('duracao_s','?')}s
</span>
</div>
"""
        return html
