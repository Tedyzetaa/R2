# filename: audio_engine.py
"""
Motor de Produção Musical Assíncrono – Voice-to-Voice e Mixagem
Integrado com FastAPI, WebSocket Soundwave e Monitoramento de Recursos

NOTA: O módulo RVC (conversão de voz) está DESATIVADO nesta versão
devido a incompatibilidades com a estrutura atual do RVC instalado.
A mixagem musical (MusicProductionEngine) funciona normalmente.
"""

import os
import sys
import logging
import tempfile
import asyncio
import time
from pathlib import Path
from typing import Tuple, Dict, Optional, Callable
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass

import numpy as np
from pydub import AudioSegment

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

logger = logging.getLogger("r2")

if not LIBROSA_AVAILABLE:
    logger.warning("⚠️ librosa não disponível – funcionalidade de timbre reduzida.")

if not TORCH_AVAILABLE:
    logger.warning("⚠️ torch não disponível – RVC desabilitado.")


@dataclass
class MusicRenderConfig:
    """Configuração para renderização de música."""
    tempo: int = 120
    genre: str = "pop"
    mood: str = "energetic"
    vocal_reference_path: Optional[str] = None
    output_format: str = "mp3"


class MusicProductionEngine:
    """
    Engine assíncrona para clonagem de timbre e mixagem de áudio.
    Integrada com FastAPI lifespan, WebSocket callbacks e monitoramento de recursos.
    Singleton em app.state para evitar múltiplas instâncias.
    """

    _instance = None
    SUPPORTED_FORMATS = {"mp3", "wav", "ogg", "m4a"}
    OUTPUT_DIR = Path("static/output/audio")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self._initialized = True

        # Callbacks para WebSocket
        self._on_start_callback: Optional[Callable] = None
        self._on_end_callback: Optional[Callable] = None
        self._on_progress_callback: Optional[Callable] = None

        # Monitoramento de processos
        self._current_process_id: Optional[int] = None
        self._start_time: Optional[float] = None

        # Estado
        self._is_processing = False

        logger.info("🎧 MusicProductionEngine inicializado (singleton)")

    def set_websocket_callbacks(
        self,
        on_start: Optional[Callable] = None,
        on_end: Optional[Callable] = None,
        on_progress: Optional[Callable] = None
    ) -> None:
        if on_start:
            self._on_start_callback = on_start
        if on_end:
            self._on_end_callback = on_end
        if on_progress:
            self._on_progress_callback = on_progress
        logger.debug("WebSocket callbacks registrados")

    async def _emit_event(self, event_type: str, data: Dict) -> None:
        if event_type == "start" and self._on_start_callback:
            try:
                if asyncio.iscoroutinefunction(self._on_start_callback):
                    await self._on_start_callback(data)
                else:
                    self._on_start_callback(data)
            except Exception as e:
                logger.warning(f"Erro em on_start callback: {e}")

        elif event_type == "end" and self._on_end_callback:
            try:
                if asyncio.iscoroutinefunction(self._on_end_callback):
                    await self._on_end_callback(data)
                else:
                    self._on_end_callback(data)
            except Exception as e:
                logger.warning(f"Erro em on_end callback: {e}")

        elif event_type == "progress" and self._on_progress_callback:
            try:
                if asyncio.iscoroutinefunction(self._on_progress_callback):
                    await self._on_progress_callback(data)
                else:
                    self._on_progress_callback(data)
            except Exception as e:
                logger.warning(f"Erro em on_progress callback: {e}")

    def _check_resource_limits(self) -> bool:
        if not PSUTIL_AVAILABLE:
            return True

        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            cpu_percent = process.cpu_percent(interval=0.1)

            if memory_percent > 80 or cpu_percent > 90:
                logger.warning(f"Recursos altos: RAM={memory_percent:.1f}%, CPU={cpu_percent:.1f}%")
                self._cleanup_zombie_processes()
                return True

            logger.debug(f"Recursos: RAM={memory_percent:.1f}%, CPU={cpu_percent:.1f}%")
            return True
        except Exception as e:
            logger.warning(f"Erro ao verificar recursos: {e}")
            return True

    def _cleanup_zombie_processes(self) -> None:
        if not PSUTIL_AVAILABLE or not self._current_process_id:
            return

        try:
            parent = psutil.Process(self._current_process_id)
            for child in parent.children(recursive=True):
                try:
                    if child.status() == psutil.STATUS_ZOMBIE:
                        logger.info(f"Limpando processo zumbi: {child.pid}")
                        os.waitpid(child.pid, os.WNOHANG)
                except (psutil.NoSuchProcess, ProcessLookupError):
                    pass
        except Exception as e:
            logger.warning(f"Erro ao limpar zumbis: {e}")

    async def process_music(
        self,
        vocal_path: str,
        instrumental_path: str,
        reference_path: str,
        output_format: str = "mp3"
    ) -> Tuple[bool, str]:
        self._is_processing = True
        self._start_time = time.time()
        self._current_process_id = os.getpid()

        try:
            await self._emit_event("start", {"type": "soundwave_start"})

            loop = asyncio.get_running_loop()
            success, result = await loop.run_in_executor(
                None,
                self._process_sync,
                vocal_path,
                instrumental_path,
                reference_path,
                output_format
            )

            elapsed = time.time() - self._start_time
            await self._emit_event("end", {
                "type": "soundwave_end",
                "success": success,
                "elapsed": f"{elapsed:.1f}s",
                "url": result if success else None
            })

            return success, result

        except Exception as e:
            logger.exception("Erro em process_music")
            await self._emit_event("end", {"type": "soundwave_end", "success": False})
            return False, f"Erro: {str(e)}"

        finally:
            self._is_processing = False

    def _process_sync(
        self,
        vocal_path: str,
        instrumental_path: str,
        reference_path: str,
        output_format: str = "mp3"
    ) -> Tuple[bool, str]:
        try:
            output_format = output_format.lower()
            if output_format not in self.SUPPORTED_FORMATS:
                return False, f"Formato inválido: {output_format}. Suportados: {', '.join(self.SUPPORTED_FORMATS)}"

            for path in [vocal_path, instrumental_path, reference_path]:
                if not os.path.exists(path):
                    return False, f"Arquivo não encontrado: {path}"

            self._check_resource_limits()

            logger.info(f"📁 Carregando áudios...")
            vocal = AudioSegment.from_file(vocal_path)
            instrumental = AudioSegment.from_file(instrumental_path)
            reference = AudioSegment.from_file(reference_path)

            logger.info(f"📊 Vocal: {len(vocal)/1000:.1f}s, Instrumental: {len(instrumental)/1000:.1f}s")

            logger.info(f"🎙️ Aplicando timbre...")
            transformed_vocal = self._apply_timbre(vocal, reference)

            logger.info(f"🔊 Normalizando loudness...")
            transformed_vocal = self._normalize_loudness(transformed_vocal, target_db=-14)
            instrumental = self._normalize_loudness(instrumental, target_db=-14)

            logger.info(f"🎛️ Mixando áudios...")
            if len(instrumental) >= len(transformed_vocal):
                mix = instrumental.overlay(transformed_vocal, position=0)
            else:
                mix = transformed_vocal.overlay(instrumental, position=0)

            logger.info(f"⏱️ Ajustando duração...")
            mix = self._fix_duration(mix, vocal, instrumental)

            logger.info(f"💾 Exportando resultado...")
            vocal_stem = Path(vocal_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"mixed_{vocal_stem}_{timestamp}_{uuid4().hex[:6]}.{output_format}"
            output_path = self.OUTPUT_DIR / output_filename
            mix.export(output_path, format=output_format)

            url = f"/static/output/audio/{output_filename}"
            logger.info(f"✅ Mixagem concluída: {url}")
            return True, url

        except Exception as e:
            logger.exception("❌ Falha no processamento musical síncrono")
            return False, f"Erro interno: {str(e)}"

    def _apply_timbre(self, vocal: AudioSegment, reference: AudioSegment) -> AudioSegment:
        if not LIBROSA_AVAILABLE:
            logger.warning("⚠️ librosa não disponível – retornando vocal original.")
            return vocal

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_vocal:
            vocal.export(tmp_vocal.name, format="wav")
            tmp_vocal_path = tmp_vocal.name

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_ref:
            reference.export(tmp_ref.name, format="wav")
            tmp_ref_path = tmp_ref.name

        try:
            y_vocal, sr_vocal = librosa.load(tmp_vocal_path, sr=None)
            y_ref, sr_ref = librosa.load(tmp_ref_path, sr=None)

            f0_ref, _, _ = librosa.pyin(y_ref, fmin=80, fmax=450, sr=sr_ref)
            f0_ref = f0_ref[~np.isnan(f0_ref)]
            if len(f0_ref) == 0:
                pitch_ratio = 1.0
            else:
                median_ref = np.median(f0_ref)
                f0_vocal, _, _ = librosa.pyin(y_vocal, fmin=80, fmax=450, sr=sr_vocal)
                f0_vocal = f0_vocal[~np.isnan(f0_vocal)]
                median_vocal = np.median(f0_vocal) if len(f0_vocal) > 0 else median_ref
                pitch_ratio = median_ref / median_vocal
                pitch_ratio = np.clip(pitch_ratio, 0.7, 1.4)

            logger.debug(f"Pitch shift: {pitch_ratio:.2f}")
            y_shifted = librosa.effects.pitch_shift(y_vocal, sr=sr_vocal, n_steps=12 * np.log2(pitch_ratio))

            tmp_out_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_out:
                    tmp_out_path = tmp_out.name
                    sf.write(tmp_out_path, y_shifted, sr_vocal)
                transformed = AudioSegment.from_wav(tmp_out_path)
            finally:
                if tmp_out_path:
                    try:
                        os.unlink(tmp_out_path)
                    except Exception as e:
                        logger.warning(f"Falha ao limpar {tmp_out_path}: {e}")

            return transformed

        finally:
            for p in (tmp_vocal_path, tmp_ref_path):
                try:
                    os.unlink(p)
                except Exception as e:
                    logger.warning(f"Falha ao limpar {p}: {e}")

    @staticmethod
    def _normalize_loudness(audio: AudioSegment, target_db: float = -14) -> AudioSegment:
        rms = audio.rms
        if rms == 0:
            return audio

        max_amplitude = float(1 << (audio.sample_width * 8 - 1))
        change_db = target_db - 20 * np.log10(rms / max_amplitude)
        return audio.apply_gain(change_db)

    @staticmethod
    def _fix_duration(mix: AudioSegment, vocal: AudioSegment, instrumental: AudioSegment) -> AudioSegment:
        max_dur = max(len(vocal), len(instrumental))
        if len(mix) < max_dur:
            silence = AudioSegment.silent(duration=max_dur - len(mix))
            mix = mix + silence
        elif len(mix) > max_dur:
            mix = mix[:max_dur]
        if len(mix) > 2000:
            mix = mix.fade_out(2000)
        return mix

    async def process_from_config(self, config: MusicRenderConfig, vocal_path: str, instr_path: str) -> Tuple[bool, str]:
        logger.info(f"🎵 Processando música com config: tempo={config.tempo}, genre={config.genre}, mood={config.mood}")

        if not config.vocal_reference_path or not os.path.exists(config.vocal_reference_path):
            return False, "Caminho de referência de voz inválido"

        return await self.process_music(
            vocal_path,
            instr_path,
            config.vocal_reference_path,
            config.output_format
        )


@dataclass
class VoiceChangeConfig:
    """Configuração para conversão de voz via RVC (desativada)."""
    input_file: str
    model_name: str
    f0_up_key: int = 0
    index_rate: float = 0.6
    resample_sr: int = 0
    rms_mix_rate: float = 0.25
    protect: float = 0.33


class RVC_VoiceEngine:
    """
    Motor de conversão de voz – VERSÃO DESATIVADA (sem RVC).
    Mantido apenas para compatibilidade com o código existente.
    """

    _instance = None
    OUTPUT_DIR = Path("static/output/audio")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        self._is_converting = False
        self.RVC_available = False

        logger.info("🎙️ RVC_VoiceEngine inicializado (DESATIVADO - sem integração RVC)")
        print("⚠️ [AVISO] Motor RVC desativado. Use apenas a mixagem musical básica.")

    def set_websocket_callbacks(self, on_start=None, on_end=None, on_progress=None):
        pass

    async def _emit_event(self, event_type, data):
        pass

    def load_voice_model(self, model_name: str) -> Tuple[bool, str]:
        return False, "RVC desativado nesta versão"

    async def convert_voice(self, config: VoiceChangeConfig) -> Tuple[bool, str]:
        return False, "RVC desativado – use apenas a mixagem musical"

    def _convert_sync(self, config):
        return False, "RVC desativado"

    def cleanup(self):
        pass