import os
import time
import json
import re
import cv2
import yt_dlp
import whisper
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, AudioFileClip
)
from moviepy.config import change_settings

# ⚠️ SEU CAMINHO DO IMAGEMAGICK (AMBIENTE OFFLINE)
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

# ══════════════════════════════════════════════════════════════════
# CONSTANTES TÁTICAS
# ══════════════════════════════════════════════════════════════════
CORTE_MIN_SEG     = 8    # Corte mínimo em segundos (abaixo disso é lixo)
CORTE_MAX_SEG     = 90   # Corte máximo em segundos (acima disso perde atenção)
CORTES_MIN        = 3    # Mínimo de cortes que a IA DEVE retornar
CORTES_MAX        = 7    # Máximo de cortes para não estourar a RAM
LIMITE_TRANSCRIPT = 8000 # Limite de chars para o LLM não explodir
TEMPERATURA_IA    = 0.1  # Protocolo de Disciplina: temperatura baixa = JSON estável


class VideoSurgeon:
    def __init__(self):
        print("✂️ [TESOURA NEURAL V3]: Inicializando Córtex de Costura Viral...")
        self.whisper_model = whisper.load_model("base")
        self.temp_dir = "temp_video"
        self.out_dir  = "static/media"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.out_dir,  exist_ok=True)

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 1: OLHO DE ÁGUIA V3 — RADAR VISUAL DE ROSTO
    # ══════════════════════════════════════════════════════════════
    def detectar_rosto_x(self, video_path, tempo_inicio, tempo_fim):
        """
        Varre 6 frames distintos dentro do corte.
        Retorna o centro X do maior rosto encontrado, ou None.
        Detecta também face de perfil como fallback do frontal.
        """
        try:
            cap          = cv2.VideoCapture(video_path)
            frontal      = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            perfil       = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
            duracao      = max(tempo_fim - tempo_inicio, 0.1)
            passo        = duracao / 7  # 6 pontos de varredura dentro do corte

            melhor_x     = None
            maior_area   = 0

            for i in range(1, 7):
                tempo_teste = tempo_inicio + (passo * i)
                cap.set(cv2.CAP_PROP_POS_MSEC, tempo_teste * 1000)
                ret, frame = cap.read()
                if not ret:
                    continue

                gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Equalização de histograma para iluminação ruim
                gray  = cv2.equalizeHist(gray)

                # Tenta frontal primeiro; se não achar, tenta perfil
                faces = frontal.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
                if len(faces) == 0:
                    faces = perfil.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(40, 40))

                for (x, y, w, h) in faces:
                    area = w * h
                    if area > maior_area:
                        maior_area = area
                        melhor_x   = x + (w / 2)

            cap.release()
            return melhor_x  # None se nenhum rosto for detectado

        except Exception as e:
            print(f"⚠️ [RADAR VISUAL]: {e}")
            return None

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 2: PROTOCOLO DE DISCIPLINA — ANÁLISE IA + RAG
    # ══════════════════════════════════════════════════════════════
    def analisar_com_llama(self, transcricao_str, ai_brain, rag_context=None):
        """
        Envia a transcrição + RAG para o LLM e retorna lista de cortes validada.
        Protocolo de Disciplina:
          - temperatura 0.1 (JSON estável)
          - mínimo CORTES_MIN cortes obrigatórios
          - fallback divisor se JSON inválido
        """
        print("🧠 [CÉREBRO]: Mapeando momentos virais com Sabedoria Tática (RAG)...")

        # Injeta o RAG apenas se houver conteúdo útil
        bloco_rag = ""
        if rag_context and len(rag_context.strip()) > 20:
            bloco_rag = f"""
[TÁTICAS DE RETENÇÃO (RAG — USE ESTES GATILHOS)]:
{rag_context.strip()}
"""

        prompt = f"""<|im_start|>system
Você é um Diretor Sênior de Conteúdo Viral especializado em TikTok e Reels.
Sua missão: analisar a transcrição e extrair entre {CORTES_MIN} e {CORTES_MAX} cortes de ALTO IMPACTO.
{bloco_rag}
REGRAS ABSOLUTAS DE CORTE VIRAL:
1. HOOK (obrigatório): Um corte nos primeiros 90s com afirmação chocante, pergunta ou controvérsia que interrompe o scroll.
2. CLIMAX: O momento de maior tensão, revelação ou pico emocional do vídeo.
3. VALOR: Insight prático e imediato que o espectador leva para a vida.
4. Cada corte deve ter entre {CORTE_MIN_SEG}s e {CORTE_MAX_SEG}s de duração.
5. Não repita os mesmos timestamps — os cortes NÃO podem se sobrepor.
6. NUNCA retorne apenas 1 corte. Mínimo: {CORTES_MIN} cortes.

Campo "position" (0–100): posição vertical da legenda.
  20 = base (padrão), 50 = centro, 80 = topo.
  Escolha baseado em onde o rosto aparece mais (rosto no centro → legenda na base).

Responda APENAS com JSON válido, sem texto extra. Formato exato:
{{"cortes": [{{"start": 10, "end": 55}}, {{"start": 120, "end": 175}}, {{"start": 300, "end": 360}}], "position": 20}}<|im_end|>
<|im_start|>user
TRANSCRIÇÃO COMPLETA:
{transcricao_str}<|im_end|>
<|im_start|>assistant
"""

        try:
            stream   = ai_brain(
                prompt,
                max_tokens=400,
                stop=["<|im_end|>"],
                temperature=TEMPERATURA_IA  # Protocolo de Disciplina: 0.1
            )
            resposta = stream["choices"][0]["text"].strip()
            print(f"🔎 [DEBUG IA RAW]: {resposta[:300]}")

            # ── Extração robusta de JSON (tolera lixo antes/depois) ──
            match = re.search(r'\{[\s\S]*\}', resposta)
            if match:
                dados = json.loads(match.group(0))
                cortes     = dados.get("cortes", [])
                pos_y      = int(dados.get("position", 20))

                # Valida e sanitiza cada corte
                cortes_validos = self._validar_cortes(cortes)

                if len(cortes_validos) >= CORTES_MIN:
                    print(f"✅ [IA]: {len(cortes_validos)} cortes validados. Posição Y: {pos_y}%")
                    return cortes_validos, pos_y
                else:
                    print(f"⚠️ [PROTOCOLO]: IA retornou {len(cortes_validos)} cortes (< {CORTES_MIN}). Ativando fallback...")

        except json.JSONDecodeError as e:
            print(f"⚠️ [PROTOCOLO]: JSON corrompido — {e}. Ativando fallback divisor...")
        except Exception as e:
            print(f"⚠️ [PROTOCOLO]: Falha inesperada — {e}. Ativando fallback divisor...")

        # ── FALLBACK DIVISOR: Corta o vídeo em blocos fixos se IA falhar ──
        return self._fallback_divisor(transcricao_str), 20

    def _validar_cortes(self, cortes_raw):
        """
        Sanitiza a lista de cortes:
        - Remove cortes com duração inválida
        - Remove sobreposições
        - Garante ordem cronológica
        """
        cortes = []
        ultimo_end = -1

        for c in cortes_raw:
            try:
                st = float(c["start"])
                nd = float(c["end"])
            except (KeyError, TypeError, ValueError):
                continue

            duracao = nd - st
            if duracao < CORTE_MIN_SEG or duracao > CORTE_MAX_SEG:
                continue  # Descarta cortes fora do range tático
            if st < ultimo_end:
                continue  # Descarta sobreposições
            if st < 0:
                continue

            cortes.append({"start": st, "end": nd})
            ultimo_end = nd

        return cortes

    def _fallback_divisor(self, transcricao_str):
        """
        Quando a IA falha, extrai timestamps da própria transcrição
        e divide o conteúdo em blocos uniformes.
        """
        print("🔧 [FALLBACK DIVISOR]: Mapeando timestamps da transcrição...")
        timestamps = re.findall(r'\[(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\]', transcricao_str)

        if not timestamps:
            return [{"start": 10.0, "end": 70.0},
                    {"start": 80.0, "end": 140.0},
                    {"start": 150.0, "end": 210.0}]

        inicio  = float(timestamps[0][0])
        fim     = float(timestamps[-1][1])
        duracao = fim - inicio

        # Divide em 3 blocos de atenção: gancho, desenvolvimento, conclusão
        bloco   = duracao / 3
        return [
            {"start": inicio,          "end": inicio + bloco * 0.7},
            {"start": inicio + bloco,  "end": inicio + bloco * 1.7},
            {"start": inicio + bloco * 2, "end": fim},
        ]

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 3: FÁBRICA DE LEGENDAS VIRAIS (ESTILO TIKTOK)
    # ══════════════════════════════════════════════════════════════
    def _criar_legendas_virais(self, segmentos_whisper, st_corte, nd_corte,
                                subclip_duration, y_pixels, subclip_w,
                                tamanho, cor_texto, cor_fundo):
        """
        Cria legendas no estilo TikTok:
        - Agrupa frases em blocos de 4–5 palavras para leitura rápida
        - Cada bloco aparece sincronizado com o áudio
        - CrossFade suave entre blocos
        """
        clips_legenda = []
        PALAVRAS_POR_BLOCO = 5  # Ideal para mobile: 4–5 palavras por tela

        for seg in segmentos_whisper:
            seg_start = seg["start"]
            seg_end   = seg["end"]

            # Só processa segmentos que estão dentro deste corte
            if seg_end <= st_corte or seg_start >= nd_corte:
                continue

            # Ajusta os tempos para o referencial do subclip
            clip_start = max(0.0, seg_start - st_corte)
            clip_end   = min(subclip_duration, seg_end - st_corte)
            dur_seg    = clip_end - clip_start
            if dur_seg <= 0:
                continue

            palavras = seg["text"].strip().upper().split()
            if not palavras:
                continue

            # Divide as palavras em blocos e distribui o tempo proporcionalmente
            blocos     = [palavras[i:i + PALAVRAS_POR_BLOCO]
                          for i in range(0, len(palavras), PALAVRAS_POR_BLOCO)]
            tempo_bloco = dur_seg / max(len(blocos), 1)

            for idx_bloco, bloco in enumerate(blocos):
                texto   = " ".join(bloco)
                b_start = clip_start + idx_bloco * tempo_bloco
                b_end   = b_start + tempo_bloco

                # Garante que não ultrapasse o clipe
                b_end = min(b_end, clip_end)
                if b_end - b_start < 0.2:
                    continue

                try:
                    txt = (
                        TextClip(
                            texto,
                            fontsize=tamanho,
                            color=cor_texto,
                            bg_color=cor_fundo,
                            font="Arial-Bold",
                            method="caption",
                            size=(int(subclip_w * 0.88), None),
                            stroke_color="black" if cor_fundo == "transparent" else None,
                            stroke_width=2       if cor_fundo == "transparent" else 0,
                        )
                        .set_position(("center", y_pixels))
                        .set_start(b_start)
                        .set_end(b_end)
                        .crossfadein(0.1)
                        .crossfadeout(0.1)
                    )
                    clips_legenda.append(txt)
                except Exception as e:
                    print(f"⚠️ [LEGENDA]: Falha no bloco '{texto}': {e}")

        return clips_legenda

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 4: MOTOR PRINCIPAL — PROCESSAR ALVO
    # ══════════════════════════════════════════════════════════════
    def processar_alvo(self, config, ai_brain=None, callback=None, rag_context=None):
        def log(msg):
            print(msg)
            if callback:
                try:
                    callback(msg)
                except Exception:
                    pass

        url         = config.get("url")
        cor         = config.get("color", "#ffffff")
        tamanho     = int(config.get("size", 24)) * 2
        estilo      = config.get("style", "outline")
        sub_enabled = config.get("active", True)
        auto_pos    = config.get("autoPos", True)

        # ── FASE 1: DOWNLOAD ──────────────────────────────────────
        log("📥 <b>[Fase 1/5] Infiltração:</b> Baixando alvo tático...")
        ydl_opts = {
            "format"    : "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl"   : f"{self.temp_dir}/alvo_%(id)s.%(ext)s",
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info       = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

        duracao_total = VideoFileClip(video_path).duration
        log(f"✅ Download OK — duração total: <b>{duracao_total:.0f}s</b>")

        # ── FASE 2: TRANSCRIÇÃO ───────────────────────────────────
        log("🎧 <b>[Fase 2/5] Interrogatório:</b> Whisper transcrevendo áudio...")
        resultado      = self.whisper_model.transcribe(video_path, fp16=False)
        transcricao_str = ""
        for seg in resultado["segments"]:
            transcricao_str += f"[{seg['start']:.1f} - {seg['end']:.1f}] {seg['text']}\n"

        if len(transcricao_str) > LIMITE_TRANSCRIPT:
            log("⚠️ <b>[BLINDAGEM]:</b> Alvo massivo — fatiando transcrição...")
            transcricao_str = transcricao_str[:LIMITE_TRANSCRIPT] + "\n...[FIM DE LEITURA SEGURA]"

        # ── FASE 3: ANÁLISE IA + RAG ──────────────────────────────
        if ai_brain:
            log("🧠 <b>[Fase 3/5] Decisão:</b> IA calculando cortes virais com RAG...")
            cortes, pos_sugerida = self.analisar_com_llama(
                transcricao_str, ai_brain, rag_context
            )
            # Ajusta timestamps que ultrapassam a duração real do vídeo
            cortes = [
                {"start": min(c["start"], duracao_total - CORTE_MIN_SEG),
                 "end"  : min(c["end"],   duracao_total)}
                for c in cortes
                if c["start"] < duracao_total - CORTE_MIN_SEG
            ]
            y_final = pos_sugerida if auto_pos else int(config.get("pos", 20))
            resumo  = " | ".join([f"{c['start']:.0f}s–{c['end']:.0f}s" for c in cortes])
            log(f"✅ <b>[IA]:</b> {len(cortes)} cortes virais selecionados → {resumo}")
            log(f"📐 Posição legenda: <b>{y_final}%</b> {'(automático)' if auto_pos else '(manual)'}")
        else:
            cortes  = [{"start": 10.0, "end": 70.0},
                       {"start": 80.0, "end": 140.0},
                       {"start": 150.0, "end": 210.0}]
            y_final = int(config.get("pos", 20))
            log("⚠️ <b>IA offline:</b> Usando cortes padrão de fallback.")

        # ── FASE 4: CORTE, ENQUADRAMENTO E LEGENDAS ──────────────
        log(f"🎯 <b>[Fase 4/5] Cirurgia:</b> Processando {len(cortes)} cortes...")
        video_original = VideoFileClip(video_path)

        # Define cores com base no estilo escolhido
        cor_fundo = "black"       if estilo == "box"    else "transparent"
        cor_texto = "yellow"      if estilo == "yellow" else cor

        clipes_finais = []

        for idx, corte in enumerate(cortes):
            st = float(corte["start"])
            nd = float(corte["end"])

            log(f"✂️ <b>Corte {idx + 1}/{len(cortes)}:</b> [{st:.1f}s → {nd:.1f}s] ({nd - st:.0f}s)")

            # ── RECORTE DO SUBCLIP ──
            subclip = video_original.subclip(st, nd)
            w, h    = subclip.size

            # ── AUTO-FRAMING: Centraliza no maior rosto ──
            target_w = int(h * 9 / 16)  # Proporção TikTok/Reels
            rosto_x  = self.detectar_rosto_x(video_path, st, nd)
            x_center = rosto_x if rosto_x else (w / 2)

            # Garante que o crop não ultrapasse as bordas do frame
            x_center = max(target_w / 2, min(x_center, w - target_w / 2))
            subclip  = subclip.crop(
                x1=x_center - target_w / 2,
                y1=0,
                x2=x_center + target_w / 2,
                y2=h
            )

            log(f"   👁️ Rosto {'detectado' if rosto_x else 'não detectado (centralizando)'} → X={x_center:.0f}")

            # ── POSIÇÃO Y DA LEGENDA (em pixels a partir do topo) ──
            y_pixels = subclip.h - (subclip.h * (y_final / 100))

            # ── LEGENDAS VIRAIS ──
            clips_legenda = []
            if sub_enabled:
                clips_legenda = self._criar_legendas_virais(
                    segmentos_whisper=resultado["segments"],
                    st_corte=st,
                    nd_corte=nd,
                    subclip_duration=subclip.duration,
                    y_pixels=y_pixels,
                    subclip_w=subclip.w,
                    tamanho=tamanho,
                    cor_texto=cor_texto,
                    cor_fundo=cor_fundo,
                )
                log(f"   💬 {len(clips_legenda)} blocos de legenda gerados.")

            # ── COMPOSIÇÃO DO CORTE ──
            if clips_legenda:
                clipes_finais.append(CompositeVideoClip([subclip] + clips_legenda))
            else:
                clipes_finais.append(subclip)

        if not clipes_finais:
            log("❌ <b>[ERRO]:</b> Nenhum corte válido gerado.")
            video_original.close()
            return None

        # ── FASE 5: FUSÃO FINAL ───────────────────────────────────
        log(f"🔥 <b>[Fase 5/5] Fusão:</b> Costurando {len(clipes_finais)} cortes no arquivo final...")
        nome_saida    = f"corte_viral_{int(time.time())}.mp4"
        caminho_final = os.path.join(self.out_dir, nome_saida)

        final_video = None
        try:
            final_video = concatenate_videoclips(clipes_finais, method="compose")
            final_video.write_videofile(
                caminho_final,
                codec="libx264",
                audio_codec="aac",
                fps=30,
                preset="ultrafast",
                ffmpeg_params=["-crf", "23"],  # Qualidade visual estável
                logger=None,
            )
            log(f"✅ <b>[MISSÃO CUMPRIDA]:</b> Clipe de <b>{final_video.duration:.1f}s</b> forjado e pronto para decolar! 🚀")
            return f"/static/media/{nome_saida}"

        except Exception as e:
            log(f"❌ <b>[RENDERIZAÇÃO FALHOU]:</b> {e}")
            return None

        finally:
            # Limpeza de recursos — sempre executa
            for recurso in [video_original, final_video] + clipes_finais:
                try:
                    if recurso:
                        recurso.close()
                except Exception:
                    pass
            if os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except Exception:
                    pass