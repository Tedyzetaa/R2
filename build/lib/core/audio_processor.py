"""
Audio processing and text-to-speech system
"""

import queue
import threading
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import tempfile
import os

class TTSProvider(Enum):
    PYTTSX3 = "pyttsx3"
    GTTS = "gtts"
    ELEVENLABS = "elevenlabs"
    SYSTEM = "system"

@dataclass
class VoiceProfile:
    """Voice profile configuration"""
    name: str
    rate: int = 150
    volume: float = 1.0
    pitch: int = 50
    language: str = "pt-BR"
    gender: str = "female"

class AudioProcessor:
    """
    Text-to-speech and audio processing system
    """
    
    def __init__(self, config):
        self.config = config
        self.tts_engine = None
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.playback_thread = None
        self.current_voice = None
        
        # Initialize TTS engine
        self._initialize_tts()
        
        # Sound effects
        self.sound_effects = {}
        self._load_sound_effects()
        
        # Statistics
        self.stats = {
            'total_speech': 0,
            'total_chars': 0,
            'avg_speech_time': 0.0,
            'errors': 0
        }
    
    def _initialize_tts(self):
        """Initialize the TTS engine based on configuration"""
        try:
            if self.config.VOICE_TYPE == "offline":
                self._initialize_pyttsx3()
            else:
                self._initialize_gtts()
            
            print(f"✅ TTS engine initialized ({self.config.VOICE_TYPE})")
            
        except Exception as e:
            print(f"❌ Failed to initialize TTS engine: {e}")
            self.tts_engine = None
    
    def _initialize_pyttsx3(self):
        """Initialize pyttsx3 for offline TTS"""
        try:
            import pyttsx3
            
            self.tts_engine = pyttsx3.init()
            
            # Configure voice properties
            self.tts_engine.setProperty('rate', self.config.VOICE_RATE)
            self.tts_engine.setProperty('volume', self.config.VOICE_VOLUME)
            
            # Try to set pitch if supported (not on Windows)
            try:
                if hasattr(self.tts_engine, 'setProperty'):
                    # Some engines might support pitch
                    self.tts_engine.setProperty('pitch', self.config.VOICE_PITCH / 100)
            except:
                pass
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            
            # Try to find Portuguese voice
            for voice in voices:
                if 'portuguese' in voice.name.lower() or 'pt' in voice.id.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    self.current_voice = VoiceProfile(
                        name=voice.name,
                        language=self.config.LANGUAGE,
                        gender='female' if 'female' in voice.name.lower() else 'male'
                    )
                    break
            
            if not self.current_voice and voices:
                # Use first available voice
                voice = voices[0]
                self.tts_engine.setProperty('voice', voice.id)
                self.current_voice = VoiceProfile(
                    name=voice.name,
                    language='en-US',
                    gender='female' if 'female' in voice.name.lower() else 'male'
                )
            
            print(f"🎙️ TTS Voice: {self.current_voice.name if self.current_voice else 'Default'}")
            
        except ImportError as e:
            print(f"❌ pyttsx3 not installed: {e}")
            raise
    
    def _initialize_gtts(self):
        """Initialize gTTS for online TTS"""
        try:
            from gtts import gTTS
            import pygame
            
            self.tts_engine = gTTS
            pygame.mixer.init()
            
            self.current_voice = VoiceProfile(
                name="Google TTS",
                language=self.config.LANGUAGE,
                gender="female"  # gTTS default
            )
            
            print("🎙️ Using Google TTS (online)")
            
        except ImportError as e:
            print(f"❌ gTTS or pygame not installed: {e}")
            raise
    
    def _load_sound_effects(self):
        """Load sound effects from assets directory"""
        sound_dir = self.config.SOUNDS_DIR
        
        if not sound_dir.exists():
            print(f"⚠️ Sound directory not found: {sound_dir}")
            return
        
        sound_files = {
            'alert_critical': 'alert_critical.wav',
            'alert_warning': 'alert_warning.wav',
            'alert_info': 'alert_info.wav',
            'activation': 'activation.wav',
            'success': 'success.wav',
            'error': 'error.wav',
            'notification': 'notification.wav'
        }
        
        try:
            import pygame
            
            for name, filename in sound_files.items():
                filepath = sound_dir / filename
                if filepath.exists():
                    self.sound_effects[name] = pygame.mixer.Sound(str(filepath))
                    print(f"🔊 Loaded sound effect: {name}")
                else:
                    print(f"⚠️ Sound file not found: {filename}")
                    
        except ImportError:
            print("⚠️ pygame not installed, sound effects disabled")
        except Exception as e:
            print(f"⚠️ Error loading sound effects: {e}")
    
    def text_to_speech(self, text: str, blocking: bool = False) -> bool:
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.tts_engine:
            print("❌ TTS engine not available")
            return False
        
        if not text or not text.strip():
            return False
        
        try:
            self.stats['total_speech'] += 1
            self.stats['total_chars'] += len(text)
            
            start_time = time.time()
            
            if isinstance(self.tts_engine, type) and self.tts_engine.__name__ == 'gTTS':
                # Online TTS with gTTS
                success = self._speak_gtts(text, blocking)
            else:
                # Offline TTS with pyttsx3
                success = self._speak_pyttsx3(text, blocking)
            
            speech_time = time.time() - start_time
            self.stats['avg_speech_time'] = (
                (self.stats['avg_speech_time'] * (self.stats['total_speech'] - 1) + speech_time)
                / self.stats['total_speech']
            )
            
            return success
            
        except Exception as e:
            print(f"❌ Error in text-to-speech: {e}")
            self.stats['errors'] += 1
            return False
    
    def _speak_pyttsx3(self, text: str, blocking: bool) -> bool:
        """Speak using pyttsx3"""
        try:
            if blocking:
                # Run in main thread
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                # Run in background thread
                def speak_thread():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                
                thread = threading.Thread(target=speak_thread, daemon=True)
                thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ pyttsx3 error: {e}")
            return False
    
    def _speak_gtts(self, text: str, blocking: bool) -> bool:
        """Speak using gTTS"""
        try:
            import pygame
            import tempfile
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_file = f.name
            
            # Generate speech
            tts = self.tts_engine(text=text, lang=self.config.LANGUAGE)
            tts.save(temp_file)
            
            # Play audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            if blocking:
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            
            # Clean up
            try:
                os.unlink(temp_file)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ gTTS error: {e}")
            return False
    
    def play_sound(self, sound_name: str, volume: float = 1.0) -> bool:
        """
        Play a sound effect
        
        Args:
            sound_name: Name of the sound effect
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        if sound_name not in self.sound_effects:
            print(f"❌ Sound effect not found: {sound_name}")
            return False
        
        try:
            sound = self.sound_effects[sound_name]
            sound.set_volume(volume)
            sound.play()
            return True
        except Exception as e:
            print(f"❌ Error playing sound: {e}")
            return False
    
    def stop_all_audio(self):
        """Stop all audio playback"""
        try:
            if self.tts_engine and hasattr(self.tts_engine, 'stop'):
                self.tts_engine.stop()
            
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                for sound in self.sound_effects.values():
                    sound.stop()
                    
        except Exception as e:
            print(f"⚠️ Error stopping audio: {e}")
    
    def set_voice_properties(self, rate: Optional[int] = None, 
                            volume: Optional[float] = None,
                            pitch: Optional[int] = None):
        """Set voice properties"""
        if not self.tts_engine:
            return
        
        try:
            if rate is not None and hasattr(self.tts_engine, 'setProperty'):
                self.tts_engine.setProperty('rate', rate)
            
            if volume is not None and hasattr(self.tts_engine, 'setProperty'):
                self.tts_engine.setProperty('volume', volume)
            
            # Note: pitch might not be supported by all engines
            
        except Exception as e:
            print(f"❌ Error setting voice properties: {e}")
    
    def list_available_voices(self) -> List[VoiceProfile]:
        """List available voices"""
        if not self.tts_engine or not hasattr(self.tts_engine, 'getProperty'):
            return []
        
        try:
            voices = self.tts_engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_list.append(VoiceProfile(
                    name=voice.name,
                    language=voice.languages[0] if voice.languages else 'en-US',
                    gender='female' if 'female' in voice.name.lower() else 'male'
                ))
            
            return voice_list
            
        except Exception as e:
            print(f"❌ Error listing voices: {e}")
            return []
    
    def set_voice(self, voice_id: str) -> bool:
        """Set specific voice by ID"""
        if not self.tts_engine or not hasattr(self.tts_engine, 'setProperty'):
            return False
        
        try:
            self.tts_engine.setProperty('voice', voice_id)
            
            # Update current voice info
            voices = self.list_available_voices()
            for voice in voices:
                if voice.name == voice_id or voice_id in voice.name:
                    self.current_voice = voice
                    break
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting voice: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audio processor statistics"""
        return {
            **self.stats,
            'current_voice': self.current_voice.__dict__ if self.current_voice else None,
            'sound_effects_loaded': len(self.sound_effects),
            'tts_engine': 'pyttsx3' if not isinstance(self.tts_engine, type) else 'gTTS'
        }
    
    def save_audio_to_file(self, text: str, filename: str) -> bool:
        """Save speech audio to file"""
        if not self.tts_engine:
            return False
        
        try:
            if isinstance(self.tts_engine, type) and self.tts_engine.__name__ == 'gTTS':
                # gTTS
                tts = self.tts_engine(text=text, lang=self.config.LANGUAGE)
                tts.save(filename)
                return True
            else:
                # pyttsx3 - requires different approach
                print("⚠️ Saving to file not supported with pyttsx3")
                return False
                
        except Exception as e:
            print(f"❌ Error saving audio to file: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_all_audio()
        
        if self.tts_engine and hasattr(self.tts_engine, 'stop'):
            self.tts_engine.stop()