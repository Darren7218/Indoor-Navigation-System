"""
pyttsx3-based audio feedback engine with background queue playback.
Integrates via speak(text, priority=False), set_volume, set_rate, shutdown.
"""

import logging
import threading
import queue
import time
from typing import Optional

from config import AUDIO_SETTINGS

try:
    import pyttsx3
except Exception as e:  # pragma: no cover
    pyttsx3 = None  # type: ignore
    logging.warning(f"pyttsx3 not available: {e}")


class AudioFeedback:
    """High-level audio feedback with pyttsx3 and queued playback."""
    
    # Singleton instance
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._running = False
        self.engine = None
        self.is_initialized = False

        # Configuration state
        self._rate_value: float = float(AUDIO_SETTINGS.get('voice_rate', 150))
        self._volume_value: float = float(AUDIO_SETTINGS.get('voice_volume', 0.9))

        # Start worker thread; the engine will be initialized inside the worker thread
        self._start_worker()

    # Public API
    def speak(self, text: str, priority: bool = False) -> None:
        if not text:
            return
        # Allow queuing even before initialization; worker will speak once ready
        if priority:
            if self.engine is not None:
                self._stop_current()
            self._clear_queue()
        try:
            logging.info(f"Queueing speech (priority={priority}): {text}")
        except Exception:
            pass
        
        # Add a small delay for priority messages to ensure they're processed
        if priority:
            time.sleep(0.1)
        
        self._queue.put(text)

    def set_volume(self, value: float) -> None:
        try:
            value = max(0.0, min(1.0, float(value)))
            self._volume_value = value
            if self.engine is not None:
                self.engine.setProperty('volume', self._volume_value)  # type: ignore
        except Exception:
            pass

    def set_rate(self, value: float) -> None:
        try:
            self._rate_value = max(50.0, min(300.0, float(value)))
            if self.engine is not None:
                self.engine.setProperty('rate', int(self._rate_value))  # type: ignore
        except Exception:
            pass

    def shutdown(self) -> None:
        self._running = False
        try:
            if self._worker and self._worker.is_alive():
                self._queue.put("__QUIT__")
                self._worker.join(timeout=2.0)
        except Exception:
            pass
        self._stop_current()

    # Internal
    def _init_tts(self) -> None:
        try:
            if pyttsx3 is None:
                logging.error("pyttsx3 not installed. Please install pyttsx3.")
                return
            # Explicitly select SAPI5 on Windows for reliability
            try:
                import sys as _sys
                if _sys.platform.startswith('win'):
                    logging.info("Initializing SAPI5 TTS engine...")
                    self.engine = pyttsx3.init(driverName='sapi5')
                else:
                    logging.info("Initializing default TTS engine...")
                    self.engine = pyttsx3.init()
            except Exception as e:
                # Fallback to default init
                logging.info(f"SAPI5 failed, trying default TTS engine... Error: {e}")
                self.engine = pyttsx3.init()
            # Choose a soft female-like voice if available
            try:
                voices = self.engine.getProperty('voices')  # type: ignore
                logging.info(f"Found {len(voices)} available voices")
                selected = None
                for v in voices:
                    name = getattr(v, 'name', '')
                    lname = name.lower() if isinstance(name, str) else ''
                    if 'zira' in lname or 'aria' in lname or 'jenny' in lname or 'female' in lname:
                        selected = v
                        break
                # Windows explicit fallbacks
                if selected is None:
                    for v in voices:
                        vid = getattr(v, 'id', '')
                        if isinstance(vid, str) and ('TTS_MS_EN-US_ZIRA_11.0' in vid or 'TTS_MS_EN-US_DAVID_11.0' in vid):
                            selected = v
                            break
                if selected is None and voices:
                    selected = voices[0]
                if selected is not None:
                    self.engine.setProperty('voice', selected.id)  # type: ignore
                    logging.info(f"Selected voice: {getattr(selected, 'name', 'Unknown')}")
                else:
                    logging.warning("No voices found")
            except Exception as e:
                logging.error(f"Error setting voice: {e}")
            # Apply volume and rate
            try:
                # Use a clear, slightly slower rate and full volume by default
                self.engine.setProperty('rate', int(self._rate_value))  # type: ignore
                self.engine.setProperty('volume', 1.0)  # force max volume initially
                
                # Try to force the default audio device
                try:
                    import sys as _sys
                    if _sys.platform.startswith('win'):
                        # Force Windows to use the default audio device
                        import ctypes
                        ctypes.windll.winmm.waveOutSetVolume(0, 0xFFFF)  # Set master volume to max
                except Exception:
                    pass
                
                logging.info("Set rate and volume properties")
            except Exception as e:
                logging.error(f"Error setting rate/volume: {e}")

            self.is_initialized = True
            logging.info("pyttsx3 TTS initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize pyttsx3 TTS: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            self.is_initialized = False

    def _start_worker(self) -> None:
        self._running = True
        self._worker = threading.Thread(target=self._worker_loop, name="TTSWorker", daemon=True)
        self._worker.start()

    def _clear_queue(self) -> None:
        try:
            while not self._queue.empty():
                self._queue.get_nowait()
        except Exception:
            pass

    def _stop_current(self) -> None:
        try:
            if self.engine is not None:
                self.engine.stop()  # type: ignore
        except Exception:
            pass

    def _worker_loop(self) -> None:
        # On Windows, ensure COM is initialized in this thread for SAPI5
        try:
            import sys as _sys
            if _sys.platform.startswith('win'):
                try:
                    import pythoncom  # type: ignore
                    pythoncom.CoInitialize()
                except Exception:
                    pass
        except Exception:
            pass

        while self._running:
            # Ensure engine is initialized in this worker thread
            if self.engine is None and not self.is_initialized:
                self._init_tts()
                # The flag should be set by _init_tts, but let's make sure
                if self.engine is not None:
                    self.is_initialized = True
                    logging.info("Worker thread: TTS engine ready")
                if not self.is_initialized:
                    time.sleep(0.1)
                    continue
            try:
                text = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if text == "__QUIT__":
                break
            try:
                if self.engine is None:
                    # Engine still not ready; requeue text and retry later
                    self._queue.put(text)
                    time.sleep(0.05)
                    continue
                try:
                    logging.info(f"Speaking now: {text}")
                except Exception:
                    pass
                
                # Add a small delay before speaking to ensure engine is ready
                time.sleep(0.05)
                
                self.engine.say(text)  # type: ignore
                self.engine.runAndWait()  # type: ignore
                time.sleep(0.02)
            except Exception as e:
                logging.error(f"Audio playback error: {e}")
                # If we get a "run loop already started" error, try to stop and restart
                if "run loop already started" in str(e):
                    try:
                        self.engine.stop()  # type: ignore
                        time.sleep(0.1)
                        self.engine.say(text)  # type: ignore
                        self.engine.runAndWait()  # type: ignore
                    except Exception as retry_e:
                        logging.error(f"Retry failed: {retry_e}")
                continue


