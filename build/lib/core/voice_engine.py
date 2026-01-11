"""
Voice recognition engine using VOSK for offline speech recognition
"""

import json
import queue
import threading
import time
import wave
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

class VoiceState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"

@dataclass
class VoiceResult:
    """Result of voice recognition"""
    text: str
    confidence: float
    timestamp: float
    duration: float
    language: str

class VoiceEngine:
    """
    Voice recognition engine using VOSK for offline speech recognition
    with fallback to online services if available
    """
    
    def __init__(self, config):
        self.config = config
        self.state = VoiceState.IDLE
        self.callback = None
        self.audio_queue = queue.Queue()
        self.processing_thread = None
        self.is_running = False
        
        # Voice activation
        self.activation_phrases = ["r2", "assistente", "hey r2", "ok r2"]
        self.is_activation_mode = False
        
        # Initialize recognizer
        self.recognizer = None
        self.microphone = None
        self._initialize_recognizer()
        
        # Statistics
        self.stats = {
            'total_commands': 0,
            'successful': 0,
            'failed': 0,
            'avg_confidence': 0.0,
            'last_command_time': 0
        }
    
    def _initialize_recognizer(self):
        """Initialize the speech recognizer based on configuration"""
        try:
            if self.config.VOICE_TYPE == "offline":
                self._initialize_vosk()
            else:
                self._initialize_online()
            
            print(f"✅ Voice engine initialized ({self.config.VOICE_TYPE})")
            
        except Exception as e:
            print(f"❌ Failed to initialize voice engine: {e}")
            self.state = VoiceState.ERROR
    
    def _initialize_vosk(self):
        """Initialize VOSK offline recognizer"""
        try:
            from vosk import Model, KaldiRecognizer
            import pyaudio
            
            # Load VOSK model
            if not self.config.VOICE_MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"VOSK model not found at {self.config.VOICE_MODEL_PATH}"
                )
            
            print(f"📁 Loading VOSK model from {self.config.VOICE_MODEL_PATH}")
            self.model = Model(str(self.config.VOICE_MODEL_PATH))
            
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Create recognizer
            self.recognizer = KaldiRecognizer(
                self.model, 
                self.config.SAMPLE_RATE
            )
            
            self.recognizer.SetWords(True)
            self.recognizer.SetPartialWords(True)
            
        except ImportError as e:
            print(f"❌ VOSK or PyAudio not installed: {e}")
            raise
        except Exception as e:
            print(f"❌ Error initializing VOSK: {e}")
            raise
    
    def _initialize_online(self):
        """Initialize online speech recognition"""
        try:
            import speech_recognition as sr
            
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
        except ImportError as e:
            print(f"❌ SpeechRecognition not installed: {e}")
            raise
        except Exception as e:
            print(f"❌ Error initializing online recognizer: {e}")
            raise
    
    def start_listening(self, callback: Callable[[str], None], 
                       activation_mode: bool = False):
        """
        Start listening for voice commands
        
        Args:
            callback: Function to call when command is recognized
            activation_mode: If True, only listen for activation phrases
        """
        if self.state == VoiceState.ERROR:
            print("⚠️ Cannot start listening: Voice engine in error state")
            return
        
        if self.state == VoiceState.LISTENING:
            print("⚠️ Already listening")
            return
        
        self.callback = callback
        self.is_activation_mode = activation_mode
        self.state = VoiceState.LISTENING
        self.is_running = True
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_audio_stream,
            daemon=True
        )
        self.processing_thread.start()
        
        print("🎤 Voice listening started" + 
              (" (activation mode)" if activation_mode else ""))
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.is_running = False
        self.state = VoiceState.IDLE
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        
        print("🛑 Voice listening stopped")
    
    def _process_audio_stream(self):
        """Main audio processing loop"""
        try:
            if self.config.VOICE_TYPE == "offline":
                self._process_vosk_stream()
            else:
                self._process_online_stream()
                
        except Exception as e:
            print(f"❌ Error in audio processing: {e}")
            self.state = VoiceState.ERROR
    
    def _process_vosk_stream(self):
        """Process audio stream using VOSK"""
        import pyaudio
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=4096
        )
        stream.start_stream()
        
        print("🔊 Audio stream opened")
        
        while self.is_running and self.state == VoiceState.LISTENING:
            try:
                data = stream.read(4096, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip().lower()
                    
                    if text:
                        self._handle_recognized_text(text, result)
                
                # Also check partial results for real-time feedback
                partial = json.loads(self.recognizer.PartialResult())
                partial_text = partial.get('partial', '').strip()
                
                if partial_text:
                    self._handle_partial_text(partial_text)
                    
            except Exception as e:
                print(f"❌ Error processing audio chunk: {e}")
                time.sleep(0.1)
        
        stream.stop_stream()
        stream.close()
        print("🔇 Audio stream closed")
    
    def _process_online_stream(self):
        """Process audio stream using online recognition"""
        import speech_recognition as sr
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            
            while self.is_running and self.state == VoiceState.LISTENING:
                try:
                    print("👂 Listening for speech...")
                    audio = self.recognizer.listen(
                        source, 
                        timeout=5,
                        phrase_time_limit=self.config.MAX_VOICE_PHRASE_TIME
                    )
                    
                    self.state = VoiceState.PROCESSING
                    
                    # Recognize using Google Web Speech API
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=self.config.LANGUAGE
                    )
                    
                    if text:
                        result = VoiceResult(
                            text=text.lower(),
                            confidence=0.9,  # Online doesn't provide confidence
                            timestamp=time.time(),
                            duration=len(audio.frame_data) / 16000,
                            language=self.config.LANGUAGE
                        )
                        self._handle_voice_result(result)
                    
                    self.state = VoiceState.LISTENING
                    
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    print("❓ Could not understand audio")
                except sr.RequestError as e:
                    print(f"🌐 Recognition service error: {e}")
                except Exception as e:
                    print(f"❌ Error in online recognition: {e}")
                    time.sleep(1)
    
    def _handle_recognized_text(self, text: str, raw_result: Dict[str, Any]):
        """Handle text recognized by VOSK"""
        confidence = self._calculate_confidence(raw_result)
        
        result = VoiceResult(
            text=text,
            confidence=confidence,
            timestamp=time.time(),
            duration=0.0,  # VOSK doesn't provide duration easily
            language=self.config.LANGUAGE
        )
        
        self._handle_voice_result(result)
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score from VOSK result"""
        if 'result' not in result:
            return 0.5
        
        words = result.get('result', [])
        if not words:
            return 0.5
        
        # Average confidence of all words
        confidences = [word.get('conf', 0.5) for word in words]
        return sum(confidences) / len(confidences)
    
    def _handle_partial_text(self, text: str):
        """Handle partial recognition results (for real-time feedback)"""
        # Could be used for real-time display of what's being recognized
        pass
    
    def _handle_voice_result(self, result: VoiceResult):
        """Handle a complete voice recognition result"""
        # Update statistics
        self.stats['total_commands'] += 1
        self.stats['successful'] += 1
        self.stats['avg_confidence'] = (
            (self.stats['avg_confidence'] * (self.stats['successful'] - 1) + result.confidence) 
            / self.stats['successful']
        )
        self.stats['last_command_time'] = result.timestamp
        
        print(f"🎤 Recognized: '{result.text}' (confidence: {result.confidence:.2f})")
        
        # Check for activation phrases
        if self.is_activation_mode:
            if any(phrase in result.text for phrase in self.activation_phrases):
                print("🔑 Activation phrase detected!")
                if self.callback:
                    self.callback(result.text)
        else:
            # Direct command
            if self.callback:
                self.callback(result.text)
    
    def listen_once(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for a single command with timeout
        
        Returns:
            Recognized text or None if timeout/error
        """
        result_queue = queue.Queue()
        
        def temp_callback(text):
            result_queue.put(text)
        
        self.start_listening(temp_callback)
        
        try:
            return result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            self.stop_listening()
    
    def save_audio_sample(self, audio_data: bytes, filename: str):
        """Save audio sample to file for debugging/training"""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.config.SAMPLE_RATE)
                wf.writeframes(audio_data)
            print(f"💾 Audio sample saved: {filename}")
        except Exception as e:
            print(f"❌ Error saving audio sample: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get voice engine statistics"""
        return {
            **self.stats,
            'state': self.state.value,
            'engine_type': self.config.VOICE_TYPE,
            'activation_mode': self.is_activation_mode,
            'uptime': time.time() - (self.stats.get('start_time', time.time()))
        }
    
    def set_activation_phrases(self, phrases: List[str]):
        """Set custom activation phrases"""
        self.activation_phrases = [p.lower() for p in phrases]
        print(f"📝 Activation phrases updated: {phrases}")
    
    def calibrate_microphone(self, duration: int = 3):
        """Calibrate microphone for ambient noise"""
        if self.config.VOICE_TYPE == "online" and self.recognizer and self.microphone:
            try:
                with self.microphone as source:
                    print("🔧 Calibrating microphone...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                    print("✅ Microphone calibrated")
            except Exception as e:
                print(f"❌ Microphone calibration failed: {e}")
        else:
            print("⚠️ Microphone calibration only available in online mode")