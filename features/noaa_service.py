"""
NOAAService — Módulo de Inteligência de Clima Espacial
Versão: 3.0 TACTICAL
Correções: shell=True bug (FFmpeg silencioso no Linux/Colab), retry logic, size checks
Expansões: GOES X-Ray, Kp Index, Solar Wind, Alertas Textuais, SDO multi-banda,
           SOHO C2, Proton Flux, Relatório Consolidado get_full_intel()
"""

import os
import json
import time
import shutil
import subprocess
import requests

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    _FFMPEG = get_ffmpeg_exe()
except Exception:
    _FFMPEG = "ffmpeg"

# ─── Constantes ───────────────────────────────────────────────────────────────
NOAA_BASE   = "https://services.swpc.noaa.gov"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─── Utilitários internos ─────────────────────────────────────────────────────

def _get(url: str, timeout: int = 20, stream: bool = False, retries: int = 3):
    """GET com retry automático e headers padrão."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout, stream=stream)
            if r.status_code == 200:
                return r
        except Exception as e:
            if attempt == retries - 1:
                print(f"⚠️  [NOAA] Falha após {retries} tentativas em {url}: {e}")
    return None


def _salvar_binario(res, path: str) -> bool:
    """Salva conteúdo binário de uma resposta requests em disco."""
    try:
        with open(path, "wb") as f:
            if hasattr(res, "iter_content"):
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            else:
                f.write(res.content)
        return os.path.getsize(path) > 500
    except Exception:
        return False


def _ffmpeg_run(cmd: list) -> bool:
    """
    Executa FFmpeg corretamente.
    BUG CORRIGIDO: shell=True com lista quebrava silenciosamente no Linux/Colab.
    Correção: shell=False (padrão) ao passar lista de argumentos.
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,   # Captura erro para debug
            shell=False               # ← CORREÇÃO CRÍTICA
        )
        if result.returncode != 0:
            print(f"⚠️  [FFmpeg] Código de saída {result.returncode}: {result.stderr[-200:]}")
        return result.returncode == 0
    except FileNotFoundError:
        print(f"❌ [FFmpeg] Binário não encontrado: {_FFMPEG}")
        return False
    except Exception as e:
        print(f"❌ [FFmpeg] Erro: {e}")
        return False


def _gif_para_mp4(gif_path: str, mp4_path: str) -> bool:
    """Converte GIF em MP4 H.264 compatível com browsers."""
    if not os.path.exists(gif_path) or os.path.getsize(gif_path) < 1000:
        return False
    cmd = [
        _FFMPEG, "-y", "-i", gif_path,
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2,format=yuv420p",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "faststart", mp4_path
    ]
    ok = _ffmpeg_run(cmd)
    if os.path.exists(gif_path):
        os.remove(gif_path)
    return ok and os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 1000


# ══════════════════════════════════════════════════════════════════════════════
class NOAAService:
    """
    Serviço de Inteligência de Clima Espacial e Atividade Solar.
    Fontes: NASA SOHO/SDO, NOAA SWPC, ACE Solar Wind.
    """

    def __init__(self):
        # ── Vídeo / Animações ──────────────────────────────────────────────
        self.url_cme_gif    = "https://soho.nascom.nasa.gov/data/LATEST/current_c3.gif"
        self.url_cme_c2_gif = "https://soho.nascom.nasa.gov/data/LATEST/current_c2.gif"
        self.url_sdo_mp4    = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0193.mp4"
        self.url_enlil_json = f"{NOAA_BASE}/products/animations/enlil.json"

        # ── Imagens estáticas SDO (multi-banda) ────────────────────────────
        self.sdo_bandas = {
            "SDO_0193_Extremo_UV": "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0193.jpg",
            "SDO_0304_Corona":     "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0304.jpg",
            "SDO_0171_Loops":      "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0171.jpg",
            "SDO_0131_Flares":     "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0131.jpg",
            "SDO_HMI_Magnetico":   "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIBC.jpg",
        }

        # ── Dados JSON / Textuais (NOAA SWPC) ─────────────────────────────
        self.url_drap         = f"{NOAA_BASE}/images/animations/d-rap/global/d-rap/latest.png"
        self.url_goes_xray    = f"{NOAA_BASE}/json/goes/primary/xrays-6-hour.json"
        self.url_kp_index     = f"{NOAA_BASE}/products/noaa-planetary-k-index.json"
        self.url_solar_wind   = f"{NOAA_BASE}/products/solar-wind/plasma-6-hour.json"
        self.url_mag_field    = f"{NOAA_BASE}/products/solar-wind/mag-6-hour.json"
        self.url_proton_flux  = f"{NOAA_BASE}/json/goes/primary/integral-protons-6-hour.json"
        self.url_alertas      = f"{NOAA_BASE}/products/alerts.json"
        self.url_previsao_txt = f"{NOAA_BASE}/text/3-day-forecast.txt"
        self.url_report_txt   = f"{NOAA_BASE}/text/solar-region-summary.txt"

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 1 — VÍDEOS E ANIMAÇÕES
    # ══════════════════════════════════════════════════════════════════════════

    def get_cme_video(self, banda: str = "C3") -> tuple:
        """Baixa GIF SOHO LASCO C2 ou C3 e converte para MP4."""
        url = self.url_cme_c2_gif if banda == "C2" else self.url_cme_gif
        gif_path = f"temp_cme_{banda.lower()}.gif"
        mp4_path = f"intel_cme_{banda.lower()}.mp4"
        print(f"⏳ [CME {banda}] Baixando coronógrafo SOHO LASCO...")
        res = _get(url, timeout=30)
        if not res:
            return None, None
        if not _salvar_binario(res, gif_path):
            return None, None
        if _gif_para_mp4(gif_path, mp4_path):
            print(f"✅ [CME {banda}] Vídeo renderizado.")
            return mp4_path, "video"
        return None, None

    def get_sdo_video(self) -> tuple:
        """Baixa vídeo SDO AIA 193Å (corona extrema UV)."""
        path = "intel_sdo.mp4"
        print("⏳ [SDO] Baixando vídeo solar AIA 193...")
        res = _get(self.url_sdo_mp4, timeout=90, stream=True)
        if not res:
            return None, None
        if _salvar_binario(res, path) and os.path.getsize(path) > 50_000:
            print("✅ [SDO] Vídeo baixado.")
            return path, "video"
        return None, None

    def get_enlil_video(self) -> tuple:
        """Reconstrói animação WSA-ENLIL a partir de todos os frames disponíveis."""
        mp4_path = "intel_enlil.mp4"
        temp_dir = "temp_enlil_frames"
        print("⏳ [ENLIL] Acessando simulação de vento solar...")

        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

            res = _get(self.url_enlil_json, timeout=20)
            if not res:
                return self._fallback_enlil_static()

            frames = res.json()
            total  = len(frames)
            print(f"📥 [ENLIL] {total} frames detectados. Iniciando download...")

            ok = 0
            for i, frame in enumerate(frames):
                img_url   = NOAA_BASE + frame["url"]
                save_path = os.path.join(temp_dir, f"frame_{i:04d}.jpg")
                r = _get(img_url, timeout=8, retries=2)
                if r and _salvar_binario(r, save_path):
                    ok += 1
                if i % 25 == 0:
                    print(f"   ↳ {i}/{total} frames ({ok} OK)...")

            if ok < 10:
                print("❌ [ENLIL] Frames insuficientes — ativando fallback estático.")
                shutil.rmtree(temp_dir)
                return self._fallback_enlil_static()

            print(f"⚙️  [ENLIL] Renderizando {ok} frames...")
            cmd = [
                _FFMPEG, "-y",
                "-framerate", "18",
                "-i", os.path.join(temp_dir, "frame_%04d.jpg"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "faststart", mp4_path
            ]
            _ffmpeg_run(cmd)
            shutil.rmtree(temp_dir)

            if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 1000:
                print("✅ [ENLIL] Animação completa pronta.")
                return mp4_path, "video"
            return self._fallback_enlil_static()

        except Exception as e:
            print(f"❌ [ENLIL] Erro: {e}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return self._fallback_enlil_static()

    def _fallback_enlil_static(self) -> tuple:
        print("⚠️  [ENLIL] Ativando imagem estática de backup.")
        path = "intel_enlil_static.jpg"
        r = _get(f"{NOAA_BASE}/images/animations/enlil/latest.jpg", timeout=15)
        if r and _salvar_binario(r, path):
            return path, "foto"
        return None, None

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 2 — IMAGENS ESTÁTICAS
    # ══════════════════════════════════════════════════════════════════════════

    def get_drap_map(self) -> tuple:
        """Mapa D-RAP de absorção de ondas de rádio (blackout HF)."""
        path = "intel_drap.png"
        print("⏳ [D-RAP] Baixando mapa de absorção...")
        r = _get(self.url_drap, timeout=30)
        if r and _salvar_binario(r, path):
            return path, "foto"
        return None, None

    def get_sdo_imagens(self) -> dict:
        """Baixa SDO em múltiplos comprimentos de onda. Retorna {nome: (path, 'foto')}."""
        resultado = {}
        for nome, url in self.sdo_bandas.items():
            path = f"intel_{nome.lower()}.jpg"
            print(f"⏳ [SDO] Banda {nome}...")
            r = _get(url, timeout=20)
            if r and _salvar_binario(r, path):
                resultado[nome] = (path, "foto")
                print(f"✅ [{nome}] OK")
            else:
                resultado[nome] = (None, None)
        return resultado

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 3 — TELEMETRIA JSON (DADOS NUMÉRICOS)
    # ══════════════════════════════════════════════════════════════════════════

    def get_goes_xray(self) -> dict:
        """
        Fluxo de raios-X GOES (6h). Detecta flares solares.
        Classes: A < B < C < M < X (X é o mais severo).
        """
        print("⏳ [GOES X-Ray] Lendo fluxo de raios-X...")
        r = _get(self.url_goes_xray, timeout=15)
        if not r:
            return {"erro": "indisponível", "classe_flare": "N/A", "fluxo_atual": None}

        try:
            dados = r.json()
            # Última leitura válida
            ultimo = dados[-1] if dados else {}
            fluxo  = float(ultimo.get("flux", 0))

            # Classificação de flare
            if   fluxo >= 1e-4: classe = "X"
            elif fluxo >= 1e-5: classe = "M"
            elif fluxo >= 1e-6: classe = "C"
            elif fluxo >= 1e-7: classe = "B"
            else:               classe = "A"

            # Pico nas últimas 6h
            fluxos  = [float(d.get("flux", 0)) for d in dados if d.get("flux")]
            pico    = max(fluxos) if fluxos else 0
            ts_ult  = ultimo.get("time_tag", "N/A")

            print(f"✅ [GOES X-Ray] Fluxo atual: {fluxo:.2e} W/m² | Classe: {classe}")
            return {
                "fluxo_atual_Wm2": fluxo,
                "classe_flare":    classe,
                "pico_6h_Wm2":     pico,
                "timestamp":       ts_ult,
                "amostras":        len(dados),
                "alerta": classe in ("M", "X"),
            }
        except Exception as e:
            return {"erro": str(e), "classe_flare": "N/A"}

    def get_kp_index(self) -> dict:
        """
        Índice Kp planetário — mede atividade geomagnética.
        0-3: Quieto | 4: Ativo | 5: G1 | 6: G2 | 7: G3 | 8: G4 | 9: G5 (extremo)
        """
        print("⏳ [Kp Index] Lendo índice geomagnético...")
        r = _get(self.url_kp_index, timeout=15)
        if not r:
            return {"erro": "indisponível", "kp_atual": None}

        try:
            dados = r.json()
            # Formato: [[timestamp, kp, status], ...]
            ultimos = [row for row in dados if len(row) >= 2]
            if not ultimos:
                return {"erro": "sem dados"}

            ultimo = ultimos[-1]
            kp     = float(ultimo[1]) if ultimo[1] not in ("", None) else 0
            ts     = ultimo[0]

            # Mapeamento para tempestade geomagnética
            if   kp >= 9: nivel = "G5 — EXTREMO 🔴"
            elif kp >= 8: nivel = "G4 — SEVERO 🔴"
            elif kp >= 7: nivel = "G3 — FORTE 🟠"
            elif kp >= 6: nivel = "G2 — MODERADO 🟡"
            elif kp >= 5: nivel = "G1 — MENOR 🟡"
            elif kp >= 4: nivel = "ATIVO ⚪"
            else:         nivel = "QUIETO ✅"

            # Pico nas últimas leituras
            kps  = [float(r[1]) for r in ultimos if r[1] not in ("", None)]
            pico = max(kps) if kps else 0

            print(f"✅ [Kp Index] Kp={kp} | {nivel}")
            return {
                "kp_atual":     kp,
                "nivel":        nivel,
                "pico_recente": pico,
                "timestamp":    ts,
                "tempestade":   kp >= 5,
                "amostras":     len(kps),
            }
        except Exception as e:
            return {"erro": str(e), "kp_atual": None}

    def get_solar_wind(self) -> dict:
        """
        Dados ACE do vento solar: velocidade (km/s) e densidade (p/cm³).
        Alta velocidade (>600 km/s) + alta densidade = risco de tempestade.
        """
        print("⏳ [Vento Solar] Lendo plasma ACE...")
        r_plasma = _get(self.url_solar_wind, timeout=15)
        r_mag    = _get(self.url_mag_field,  timeout=15)

        resultado = {
            "velocidade_km_s": None,
            "densidade_p_cm3": None,
            "temperatura_K":   None,
            "campo_Bz_nT":     None,
            "alerta":          False,
        }

        try:
            if r_plasma:
                dados = r_plasma.json()
                ult   = dados[-1] if dados else {}
                resultado["velocidade_km_s"] = float(ult.get("speed",       0))
                resultado["densidade_p_cm3"] = float(ult.get("density",     0))
                resultado["temperatura_K"]   = float(ult.get("temperature", 0))
                resultado["timestamp"]       = ult.get("time_tag", "N/A")

            if r_mag:
                dados_mag = r_mag.json()
                ult_mag   = dados_mag[-1] if dados_mag else {}
                bz = float(ult_mag.get("bz_gsm", 0))
                resultado["campo_Bz_nT"] = bz
                # Bz fortemente negativo + vento rápido = tempestade iminente
                if bz < -10 and (resultado["velocidade_km_s"] or 0) > 500:
                    resultado["alerta"] = True

            v = resultado["velocidade_km_s"] or 0
            print(f"✅ [Vento Solar] v={v:.0f} km/s | Bz={resultado['campo_Bz_nT']} nT")
        except Exception as e:
            resultado["erro"] = str(e)

        return resultado

    def get_proton_flux(self) -> dict:
        """
        Fluxo de prótons energéticos GOES (partículas/cm²/s/sr).
        Limiar de evento: > 10 p.f.u a 10 MeV (S1+).
        """
        print("⏳ [Prótons] Lendo fluxo de partículas...")
        r = _get(self.url_proton_flux, timeout=15)
        if not r:
            return {"erro": "indisponível"}

        try:
            dados = r.json()
            ult   = dados[-1] if dados else {}
            flux  = float(ult.get("flux", 0))

            if   flux >= 1000: nivel = "S5 — EXTREMO 🔴"
            elif flux >= 100:  nivel = "S3 — FORTE 🟠"
            elif flux >= 10:   nivel = "S1 — MENOR 🟡"
            else:              nivel = "Normal ✅"

            print(f"✅ [Prótons] Fluxo: {flux:.1f} pfu | {nivel}")
            return {
                "fluxo_pfu":  flux,
                "nivel":      nivel,
                "timestamp":  ult.get("time_tag", "N/A"),
                "evento":     flux >= 10,
            }
        except Exception as e:
            return {"erro": str(e)}

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 4 — ALERTAS E PREVISÕES TEXTUAIS
    # ══════════════════════════════════════════════════════════════════════════

    def get_alertas_ativos(self) -> list:
        """Retorna lista de alertas/avisos ativos emitidos pelo NOAA SWPC."""
        print("⏳ [Alertas] Verificando alertas SWPC ativos...")
        r = _get(self.url_alertas, timeout=15)
        if not r:
            return []

        try:
            dados = r.json()
            alertas = []
            for item in dados[:10]:  # Últimos 10
                alertas.append({
                    "produto":    item.get("product_id",   "N/A"),
                    "emissao":    item.get("issue_datetime","N/A"),
                    "mensagem":   item.get("message", "")[:500],
                })
            print(f"✅ [Alertas] {len(alertas)} alertas ativos.")
            return alertas
        except Exception as e:
            print(f"❌ [Alertas] Erro: {e}")
            return []

    def get_previsao_3dias(self) -> str:
        """Texto de previsão do clima espacial para os próximos 3 dias."""
        print("⏳ [Previsão] Baixando previsão de 3 dias...")
        r = _get(self.url_previsao_txt, timeout=15)
        if r:
            texto = r.text.strip()
            print(f"✅ [Previsão] {len(texto)} caracteres recebidos.")
            return texto
        return "Previsão indisponível."

    def get_solar_region_summary(self) -> str:
        """Resumo das regiões ativas solares (manchas solares produtoras de flares)."""
        print("⏳ [Regiões Solares] Baixando sumário...")
        r = _get(self.url_report_txt, timeout=15)
        if r:
            return r.text.strip()
        return "Relatório de regiões solares indisponível."

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 5 — RELATÓRIO CONSOLIDADO (MÉTODO PRINCIPAL)
    # ══════════════════════════════════════════════════════════════════════════

    def get_full_intel(self) -> dict:
        """
        Executa TODOS os módulos e retorna um pacote de inteligência completo.
        Usado pelo WebSocket para montar o relatório HTML do painel NOAA.
        """
        print("\n" + "═"*55)
        print("🛰️  [NOAA FULL INTEL] Iniciando varredura completa...")
        print("═"*55)
        inicio = time.time()

        intel = {
            # Telemetria numérica
            "goes_xray":    self.get_goes_xray(),
            "kp_index":     self.get_kp_index(),
            "solar_wind":   self.get_solar_wind(),
            "proton_flux":  self.get_proton_flux(),
            # Alertas textuais
            "alertas":      self.get_alertas_ativos(),
            "previsao_3d":  self.get_previsao_3dias(),
            "solar_region": self.get_solar_region_summary(),
            # Mídias (paths locais)
            "media": {
                "drap":         self.get_drap_map(),
                "sdo_imagens":  self.get_sdo_imagens(),
                # Vídeos são pesados — coletados sob demanda
                # "cme_c3":    self.get_cme_video("C3"),
                # "enlil":     self.get_enlil_video(),
            },
            # Metadados
            "timestamp_coleta": time.strftime("%d/%m/%Y %H:%M:%S UTC"),
            "duracao_s": round(time.time() - inicio, 1),
        }

        # ── Score de Alerta Consolidado ────────────────────────────────────
        score = 0
        if intel["goes_xray"].get("alerta"):          score += 2
        if intel["kp_index"].get("tempestade"):        score += 2
        if intel["proton_flux"].get("evento"):         score += 2
        if intel["solar_wind"].get("alerta"):          score += 3
        if intel["alertas"]:                           score += len(intel["alertas"])

        if   score >= 8: estado = "🔴 CRÍTICO"
        elif score >= 5: estado = "🟠 ELEVADO"
        elif score >= 2: estado = "🟡 MODERADO"
        else:            estado = "✅ NOMINAL"

        intel["score_alerta"] = score
        intel["estado_geral"] = estado

        print(f"\n✅ [NOAA FULL INTEL] Concluído em {intel['duracao_s']}s | Estado: {estado}")
        return intel

    def gerar_html_painel(self, intel: dict = None) -> str:
        """
        Gera HTML formatado para injeção no WebSocket do R2.
        Chame get_full_intel() antes, ou deixe este método coletar os dados.
        """
        if intel is None:
            intel = self.get_full_intel()

        xray  = intel.get("goes_xray",   {})
        kp    = intel.get("kp_index",    {})
        wind  = intel.get("solar_wind",  {})
        proto = intel.get("proton_flux", {})

        # ── BLINDAGEM TÁTICA CONTRA DADOS VAZIOS (NoneType) ──
        flux_x  = xray.get('fluxo_atual_Wm2') or 0
        pico_x  = xray.get('pico_6h_Wm2') or 0
        v_vento = wind.get('velocidade_km_s') or 0
        d_vento = wind.get('densidade_p_cm3') or 0
        f_proto = proto.get('fluxo_pfu') or 0

        html = f"""
<div style="font-family:'Share Tech Mono',monospace;font-size:12px;line-height:1.7;color:#00ff88;">
<b>🛰️ NOAA SPACE WEATHER INTEL — {intel.get('timestamp_coleta','N/A')}</b><br>
<b>Estado Geral: {intel.get('estado_geral','N/A')} | Score: {intel.get('score_alerta',0)}</b>
<hr style="border-color:#333;"/>
<b>☀️ GOES X-Ray (Flares Solares)</b><br>
&nbsp;• Classe: <b>{xray.get('classe_flare','N/A')}</b> | Fluxo: {flux_x:.2e} W/m²<br>
&nbsp;• Pico 6h: {pico_x:.2e} | Alerta: {'⚠️ SIM' if xray.get('alerta') else '✅ NÃO'}<br>
<br><b>🌍 Índice Kp (Tempestade Geomagnética)</b><br>
&nbsp;• Kp Atual: <b>{kp.get('kp_atual','N/A')}</b> | {kp.get('nivel','N/A')}<br>
&nbsp;• Pico recente: {kp.get('pico_recente','N/A')} | Tempestade: {'⚠️ SIM' if kp.get('tempestade') else '✅ NÃO'}<br>
<br><b>💨 Vento Solar (ACE)</b><br>
&nbsp;• Velocidade: {v_vento:.0f} km/s | Densidade: {d_vento:.1f} p/cm³<br>
&nbsp;• Campo Bz: {wind.get('campo_Bz_nT','N/A')} nT | Alerta: {'⚠️ SIM' if wind.get('alerta') else '✅ NÃO'}<br>
<br><b>⚡ Fluxo de Prótons</b><br>
&nbsp;• Fluxo: {f_proto:.1f} pfu | {proto.get('nivel','N/A')}<br>
<br><b>📋 Alertas SWPC Ativos: {len(intel.get('alertas',[]))}</b><br>
{"".join(f'&nbsp;• [{a["produto"]}] {a["emissao"]}<br>' for a in intel.get('alertas',[])[:5])}
</div>
"""
        return html
