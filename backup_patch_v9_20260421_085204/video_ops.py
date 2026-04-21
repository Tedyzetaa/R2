# filename: video_ops.py
import os
import json
import tempfile
import subprocess
import gc
import re
import torch

class VideoSurgeon:
    def __init__(self, whisper_model=None):
        # BUG FIX #2: Aceita modelo Whisper externo para evitar duplo carregamento na VRAM.
        # Antes: carregava whisper.load_model("base") aqui E em main2.py → OOM garantido em GPUs de 6GB.
        # Agora: recebe o modelo já carregado via parâmetro. Se None, carrega localmente como fallback.
        self._whisper_model = whisper_model
        print("✂️ [TESOURA NEURAL V5.2]: Córtex Viral Vertical Inicializado (Modo Sniper + Full HD 1080x1920).")

    # ──────────────────────────────────────────────────────────────────
    # UTILIDADE: Converte HH:MM:SS → segundos (float)
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _hms_to_seconds(hms: str) -> float:
        """Converte string HH:MM:SS em segundos totais."""
        try:
            partes = hms.strip().split(':')
            if len(partes) == 3:
                return int(partes[0]) * 3600 + int(partes[1]) * 60 + float(partes[2])
            elif len(partes) == 2:
                return int(partes[0]) * 60 + float(partes[1])
            return float(partes[0])
        except Exception:
            return 0.0

    def processar_video_viral(self, video_path, ai_brain):
        # 1. INTERCEPTADOR DE YOUTUBE
        if video_path.startswith("http://") or video_path.startswith("https://"):
            try:
                import yt_dlp
            except ImportError:
                return "❌ Erro: Biblioteca yt-dlp não instalada. Execute: pip install yt-dlp"
            
            print(f"✂️ [TESOURA NEURAL]: Interceptando link do YouTube...")
            os.makedirs("static/media", exist_ok=True)
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'static/media/temp_yt_%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_path, download=True)
                    video_path = ydl.prepare_filename(info)
                    print(f"✂️ [TESOURA NEURAL]: Download tático concluído -> {video_path}")
            except Exception as e:
                return f"❌ Erro ao baixar vídeo do YouTube: {str(e)}"
                
        elif not os.path.exists(video_path):
            return f"❌ Arquivo não encontrado: {video_path}"

        # 2. VALIDAÇÃO DO WHISPER
        try:
            import whisper
        except ImportError:
            return "❌ Erro: openai-whisper não instalado no sistema."

        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        
        try:
            # 3. Extração Acelerada de Áudio
            cmd_audio = f'ffmpeg -y -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{temp_audio}"'
            subprocess.run(cmd_audio, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 4. Audição (Whisper)
            # BUG FIX #2 (continuação): usa modelo injetado se disponível, evitando dupla alocação de VRAM
            print("✂️ [TESOURA NEURAL]: Transcrevendo áudio alvo...")
            model = self._whisper_model
            modelo_local = False
            if model is None:
                model = whisper.load_model("base")
                modelo_local = True

            result = model.transcribe(temp_audio)
            transcricao = result["text"]
            
            # 5. Limpeza de VRAM Crítica — só descarrega se foi carregado localmente
            if modelo_local:
                del model
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
            # 6. Raciocínio LLM (Córtex Viral) - PROMPT V5.2 (MODO SNIPER + CLICKBAIT EXTREMO)
            print("✂️ [TESOURA NEURAL]: Analisando viés de engajamento para cortes verticais...")
            sys_prompt = (
                "Você é um Editor Sênior de TikTok altamente agressivo. Seu objetivo é achar O OURO do vídeo. "
                "REGRAS INQUEBRÁVEIS: "
                "1. MODO SNIPER: Escolha no MÁXIMO os 3 melhores trechos absolutos. Jamais ultrapasse 3 cortes. Nunca repita temas ou histórias. "
                "2. TÍTULOS CURTOS E EXPLOSIVOS: O 'tema' deve ter no máximo 4 palavras, ser puro clickbait e gerar curiosidade extrema (Ex: VAZOU_O_PLANO, TRETA_NOS_BASTIDORES). É estritamente proibido usar palavras acadêmicas ou títulos descritivos longos. "
                "3. TEMPO: 60 a 120 segundos, mantendo contexto isolado e um gancho (hook) forte nos primeiros 3 segundos. "
                "Retorne EXCLUSIVAMENTE um array JSON contendo 'tema', 'start', 'end' e 'motivo'. O formato de tempo DEVE ser HH:MM:SS."
            )
            prompt = f"<|im_start|>system\n{sys_prompt}\n<|im_end|>\n<|im_start|>user\nTranscrição: {transcricao}\n<|im_end|>\n<|im_start|>assistant\n"
            
            resp = ai_brain(prompt, max_tokens=2048, stop=["<|im_end|>"])
            texto_ia = resp["choices"][0]["text"]
            
            # BUG FIX #9: Regex GULOSA (não-gulosa `*?` parava no primeiro `]` e quebrava arrays aninhados).
            # Antes: r'\[[\s\S]*?\]' → capturava só até o primeiro ] encontrado.
            # Agora: r'\[[\s\S]*\]'  → captura o array completo corretamente.
            match = re.search(r'\[[\s\S]*\]', texto_ia)
            if not match:
                return f"❌ A IA não retornou um padrão JSON válido. Resposta bruta: {texto_ia}"
                
            cortes = json.loads(match.group(0))
            
                    # V9.0: Validar e truncar campos
        cortes_validos = []
        for c in cortes:
            if isinstance(c, dict) and "tema" in c and "start" in c and "end" in c:
                tema = c["tema"]
                if len(tema) > 40:
                    tema = tema[:40]
                c["tema"] = tema
                cortes_validos.append(c)
        cortes = cortes_validos
        # 7. Ataque FFmpeg (Recortes verticais 9:16 + upscale forçado para FULL HD 1080x1920)
            out_dir = "static/media/cortes_virais"
            os.makedirs(out_dir, exist_ok=True)
            
            arquivos_gerados = []
            for i, c in enumerate(cortes):
                tema = re.sub(r'[^\w\-]', '_', c.get('tema', f'corte_viral_{i}'))
                t_start = c.get('start', '00:00:00')
                t_end   = c.get('end',   '00:01:00')
                out_file = os.path.join(out_dir, f"{tema}.mp4")
                
                # BUG FIX #1 (CRÍTICO): Substituição de -to por -t (duração calculada).
                #
                # PROBLEMA ORIGINAL:
                #   ffmpeg -ss {t_start} -i arquivo -to {t_end} ...
                #   Quando -ss vem ANTES de -i (input seek), o FFmpeg reseta os timestamps do output
                #   para zero. Logo, -to {t_end} era interpretado como "pare em t_end segundos desde
                #   o início DO OUTPUT" — ou seja, se start=00:01:30 e end=00:02:30, o corte ficaria
                #   com 2 minutos e 30 segundos em vez de 60 segundos.
                #
                # CORREÇÃO:
                #   Calcular a DURAÇÃO (end - start) e usar -t, que é sempre relativo ao output.
                #   Resultado: corte exato do intervalo solicitado pela IA.
                duracao_seg = self._hms_to_seconds(t_end) - self._hms_to_seconds(t_start)
                if duracao_seg <= 0:
                    print(f"⚠️ [TESOURA] Corte '{tema}' ignorado: duração inválida ({t_start} → {t_end})")
                    continue

                # V5.2: Crop vertical centralizado (9:16) + upscale forçado para 1080x1920 (Full HD TikTok)
                # - crop=floor(ih*9/16/2)*2:ih  → largura proporcional a 9/16 da altura, garantindo par
                # - mantém altura original, centralizado automaticamente (x padrão = (in_w-out_w)/2)
                # - scale=1080:1920 → redimensiona para resolução máxima do TikTok (Full HD vertical)
                # - re-encode com libx264 (preset superfast para velocidade)
                # - áudio copiado sem alterações (-c:a copy)
                cmd_cut = (
                    f'ffmpeg -y -ss {t_start} -i "{video_path}" '
                    f'-t {duracao_seg:.3f} '
                    f'-vf "crop=floor(ih*9/16/2)*2:ih,scale=1080:1920" -c:v libx264 -preset superfast -c:a copy "{out_file}"'
                )
                subprocess.run(cmd_cut, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                    arquivos_gerados.append(out_file)
                else:
                    print(f"⚠️ [TESOURA] Falha ao gerar corte: {out_file}")
                
            if not arquivos_gerados:
                return "❌ Nenhum corte foi gerado com sucesso. Verifique os timestamps da IA."

            return arquivos_gerados
            
        except Exception as e:
            return f"❌ Erro Crítico na Tesoura Neural: {str(e)}"
        finally:
            if os.path.exists(temp_audio):
                try:
                    os.unlink(temp_audio)
                except Exception:
                    pass
            # V9.0: Remover arquivo temporário do YouTube
            if video_path and video_path.startswith("static/media/temp_yt_"):
                try:
                    os.unlink(video_path)
                except Exception:
                    pass