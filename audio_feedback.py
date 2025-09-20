"""
pyttsx3-based audio feedback engine with non-blocking speech.
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
    """High-level audio feedback with pyttsx3 and non-blocking playback."""
    
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

        # Configuration state
        self._rate_value: float = float(AUDIO_SETTINGS.get('voice_rate', 150))
        self._volume_value: float = float(AUDIO_SETTINGS.get('voice_volume', 0.9))

        # Start worker thread
        self._start_worker()

    def speak(self, text: str, priority: bool = False) -> None:
        """Queue text for speech - NON-BLOCKING."""
        if not text or not text.strip():
            return
        
        text = text.strip()
        logging.info(f"=== SPEAK REQUEST (NON-BLOCKING) ===")
        logging.info(f"Text: {text[:100]}...")
        logging.info(f"Priority: {priority}")
        logging.info(f"Thread: {threading.current_thread().name}")
        logging.info(f"Worker running: {self._running}")
        logging.info(f"Worker alive: {self._worker.is_alive() if self._worker else False}")
        
        # Ensure worker thread is running
        if not self._running or not self._worker or not self._worker.is_alive():
            logging.warning("Worker thread not running, restarting...")
            self._start_worker()
        
        try:
            if priority:
                # Clear queue and add priority message
                self._clear_queue()
                self._queue.put(text, block=False)
                logging.info("Added priority speech to queue")
            else:
                # Add to queue (non-blocking)
                self._queue.put(text, block=False)
                logging.info("Added speech to queue")
            
            # Log queue status
            logging.info(f"Queue size after adding: {self._queue.qsize()}")
            
        except queue.Full:
            logging.warning("Speech queue full, skipping message")
        except Exception as e:
            logging.error(f"Error queueing speech: {e}")

    def _create_fresh_engine(self):
        """Create a completely fresh TTS engine for each speech request."""
        try:
            if pyttsx3 is None:
                logging.error("pyttsx3 not available")
                return None
            
            logging.info("Creating fresh TTS engine...")
            
            # Initialize COM for Windows (each thread needs its own COM initialization)
            try:
                import sys as _sys
                if _sys.platform.startswith('win'):
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                        logging.info("COM initialized for worker thread")
                    except Exception as e:
                        logging.warning(f"COM initialization failed: {e}")
            except Exception:
                pass
            
            # Create fresh engine
            engine = None
            try:
                import sys as _sys
                if _sys.platform.startswith('win'):
                    engine = pyttsx3.init(driverName='sapi5')
                else:
                    engine = pyttsx3.init()
                logging.info("Fresh pyttsx3 engine created")
            except Exception as e:
                logging.error(f"Engine creation failed: {e}")
                try:
                    engine = pyttsx3.init()
                    logging.info("Fallback engine created")
                except Exception as e2:
                    logging.error(f"Fallback engine creation failed: {e2}")
                    return None
            
            if engine is None:
                logging.error("Engine is None after creation")
                return None
            
            # Configure engine - PRIORITY: SELECT FEMALE VOICE
            try:
                voices = engine.getProperty('voices')
                if voices:
                    logging.info(f"Available voices: {[getattr(v, 'name', 'Unknown') for v in voices]}")
                    selected = None
                    
                    # Priority order for female voices
                    preferred_female_voices = ['zira', 'aria', 'jenny', 'eva', 'female']
                    
                    for preference in preferred_female_voices:
                        for v in voices:
                            name = getattr(v, 'name', '').lower()
                            if preference in name:
                                selected = v
                                logging.info(f"Selected preferred female voice: {getattr(v, 'name', 'Unknown')}")
                                break
                        if selected:
                            break
                    
                    # Windows-specific fallback to Zira if available
                    if selected is None:
                        for v in voices:
                            vid = getattr(v, 'id', '')
                            if isinstance(vid, str) and 'TTS_MS_EN-US_ZIRA_11.0' in vid:
                                selected = v
                                logging.info(f"Selected Windows Zira voice: {getattr(v, 'name', 'Unknown')}")
                                break
                    
                    # Last resort - use first available voice
                    if selected is None and voices:
                        selected = voices[0]
                        logging.warning(f"Using first available voice: {getattr(selected, 'name', 'Unknown')}")
                    
                    if selected is not None:
                        engine.setProperty('voice', selected.id)
                        logging.info(f"FINAL VOICE SELECTION: {getattr(selected, 'name', 'Unknown')}")
                    else:
                        logging.error("No voices available")
                else:
                    logging.warning("No voices available on system")
            except Exception as e:
                logging.error(f"Error selecting voice: {e}")
            
            # Set rate and volume
            try:
                engine.setProperty('rate', int(self._rate_value))
                engine.setProperty('volume', self._volume_value)
                logging.info(f"Voice configured: rate={self._rate_value}, volume={self._volume_value}")
            except Exception as e:
                logging.warning(f"Engine configuration failed: {e}")
            
            return engine
            
        except Exception as e:
            logging.error(f"Fresh engine creation failed: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None

    def set_volume(self, value: float) -> None:
        try:
            self._volume_value = max(0.0, min(1.0, float(value)))
            logging.info(f"Volume set to: {self._volume_value}")
        except Exception as e:
            logging.error(f"Error setting volume: {e}")

    def set_rate(self, value: float) -> None:
        try:
            self._rate_value = max(50.0, min(300.0, float(value)))
            logging.info(f"Rate set to: {self._rate_value}")
        except Exception as e:
            logging.error(f"Error setting rate: {e}")

    def shutdown(self) -> None:
        logging.info("Shutting down AudioFeedback...")
        self._running = False
        try:
            if self._worker and self._worker.is_alive():
                self._queue.put("__QUIT__")
                self._worker.join(timeout=3.0)
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")

    def _start_worker(self) -> None:
        """Start the background worker thread."""
        try:
            # Stop any existing worker
            if self._worker and self._worker.is_alive():
                logging.info("Stopping existing worker thread")
                old_running = self._running
                self._running = False
                try:
                    self._queue.put("__QUIT__")
                    self._worker.join(timeout=2.0)
                except Exception as e:
                    logging.error(f"Error stopping old worker: {e}")
                self._running = old_running
            
            # Start new worker
            self._running = True
            self._worker = threading.Thread(target=self._worker_loop, daemon=True, name="AudioWorker")
            self._worker.start()
            logging.info("Audio worker thread started")
            
            # Give worker thread time to initialize
            time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"Error starting worker thread: {e}")

    def _clear_queue(self) -> None:
        try:
            cleared_count = 0
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    cleared_count += 1
                except queue.Empty:
                    break
            if cleared_count > 0:
                logging.info(f"Cleared {cleared_count} messages from queue")
        except Exception as e:
            logging.error(f"Error clearing queue: {e}")

    def _worker_loop(self) -> None:
        """Worker thread loop - handles all speech in background."""
        logging.info("TTS worker thread started")
        
        processed_count = 0

        while self._running:
            try:
                # Get text from queue (blocking with timeout)
                try:
                    text = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                if text == "__QUIT__":
                    logging.info("Worker: Received quit signal")
                    break
                
                # Create a fresh engine for each speech request
                logging.info(f"Worker: Processing message #{processed_count + 1}: {text[:50]}...")
                engine = self._create_fresh_engine()
                
                if engine is None:
                    logging.error("Worker: Failed to create engine, skipping message")
                    continue
                
                # Speak the text with fresh engine
                try:
                    logging.info(f"Worker: Speaking with fresh engine...")
                    engine.say(text)
                    engine.runAndWait()
                    
                    processed_count += 1
                    logging.info(f"Worker: Speech #{processed_count} completed successfully")
                    
                except Exception as e:
                    logging.error(f"Worker: Speech error: {e}")
                    import traceback
                    logging.error(f"Worker: Speech traceback: {traceback.format_exc()}")
                
                # Clean up engine immediately after use
                try:
                    engine.stop()
                    del engine
                    logging.info("Worker: Engine cleaned up")
                except Exception as e:
                    logging.warning(f"Worker: Engine cleanup warning: {e}")
                
                # Clean up COM for this iteration (Windows)
                try:
                    import sys as _sys
                    if _sys.platform.startswith('win'):
                        try:
                            import pythoncom
                            pythoncom.CoUninitialize()
                            logging.info("Worker: COM cleaned up")
                        except Exception:
                            pass
                except Exception:
                    pass
                    
            except Exception as e:
                logging.error(f"Worker loop error: {e}")
                import traceback
                logging.error(f"Worker loop traceback: {traceback.format_exc()}")
                time.sleep(0.1)
                continue
        
        logging.info(f"TTS worker thread stopped (processed {processed_count} messages)")