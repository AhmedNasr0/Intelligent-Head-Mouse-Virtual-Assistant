import pyaudio
import numpy as np
import torch
from scipy.signal import resample
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from pathlib import Path
from infrastructure.services.voice.coqui_tts_service import RealisticTTS
import time
import threading



class VoiceService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls(*args, **kwargs)
        return cls._instance

    def __init__(self, model_name="openai/whisper-small", device="cuda"):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.device = device
        self.interval = 5  # interval of recording in seconds 
        self.tts = RealisticTTS()
        # Create models directory if it doesn't exist
        models_dir = Path(__file__).resolve().parent.parent / "models" / "whisper"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Set model path
        model_path = models_dir / "models--openai--whisper-small" / "snapshots" / "973afd24965f72e36ca33b3055d56a652f456b4d"
        
        
        print(f"[INFO] Loading model from {model_path}...")
        try:
            # Try to load from local path first
            if model_path.exists():
                self.processor = WhisperProcessor.from_pretrained(model_path)
                self.model = WhisperForConditionalGeneration.from_pretrained(model_path).to(device)
            else:
                # Download and save model if not found locally
                print(f"[INFO] Model not found locally. Downloading {model_name}...")
                self.processor = WhisperProcessor.from_pretrained(model_name)
                self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(device)
                
                # Save model locally
                print(f"[INFO] Saving model to {model_path}...")
                self.processor.save_pretrained(model_path)
                self.model.save_pretrained(model_path)
            
            self.model.eval()
            for p in self.model.parameters():
                p.requires_grad = False
                
            print("[INFO] Model loaded successfully.")
            
        except Exception as e:
            print(f"[ERROR] Failed to load model: {str(e)}")
            raise

        self.p = pyaudio.PyAudio()
        self.is_listening = False
        self.silence_threshold = 0.01
        self.silence_duration = 2  # seconds of silence to consider speech ended
        self.min_speech_duration = 1  # minimum seconds of speech to consider valid

    def list_devices(self):
        return [self.p.get_device_info_by_index(i)['name'] for i in range(self.p.get_device_count())]

    def set_interval(self, interval):
        self.interval = interval
        print(f"[INFO] Interval set to {self.interval} seconds")
            
    def get_interval(self):
        return self.interval

    def record_audio(self, input_device_index=1):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1

        try:
            device_info = self.p.get_device_info_by_index(input_device_index)
            if not device_info['maxInputChannels'] > 0:
                raise ValueError(f"Device {input_device_index} is not an input device")

            RATE = int(device_info['defaultSampleRate'])
            WHISPER_RATE = 16000

            print(f"[INFO] Recording from device {input_device_index} ({device_info['name']}) for {self.interval} seconds...")
            stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                    input=True, input_device_index=input_device_index, frames_per_buffer=1024)

            audio = stream.read(int(RATE * self.interval), exception_on_overflow=False)
            stream.stop_stream()
            stream.close()
            print("[INFO] Audio recorded successfully")

            audio_np = np.frombuffer(audio, np.int16).astype(np.float32) / 32768.0

            audio_resampled = resample(audio_np, int(len(audio_np) * WHISPER_RATE / RATE))
            return audio_resampled

        except Exception as e:
            print(f"[ERROR] Failed to record audio: {str(e)}")
            return None

    def transcribe(self, audio_chunk, language="English", task="transcribe"):
        input_features = self.processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
        with torch.no_grad():
            predicted_ids = self.model.generate(input_features.to(self.device), language=language, task=task)
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)
        return transcription[0]

    def is_silent(self, audio_np, threshold=None):
        """Check if the audio is silent"""
        if threshold is None:
            threshold = self.silence_threshold
        return np.max(np.abs(audio_np)) < threshold

    def transcribe_live(self, device_index=1, language="English"):
        """Transcribe live audio until silence is detected"""
        try:
            all_text = []
            speech_started = False
            silence_count = 0
            speech_duration = 0
            
            print("[INFO] Starting live transcription...")
            
            while True:
                audio = self.record_audio(device_index)
                if audio is None:
                    continue
                
                if not self.is_silent(audio):
                    if not speech_started:
                        print("[INFO] Speech detected")
                        speech_started = True
                        silence_count = 0
                    
                    text = self.transcribe(audio, language=language).strip()
                    if text == "you":
                        continue
                    if text:
                        print(f"[INFO] Transcribed: {text}")
                        all_text.append(text)
                        speech_duration += self.interval
                    
                elif speech_started:
                    silence_count += 1
                    if silence_count >= (self.silence_duration / self.interval):
                        if speech_duration >= self.min_speech_duration:
                            print("[INFO] Speech ended")
                            break
                        else:
                            print("[INFO] Speech too short, continuing...")
                            speech_started = False
                            silence_count = 0
                            speech_duration = 0
                            all_text = []
                
                if speech_duration > 30:  # Maximum 30 seconds of speech
                    print("[INFO] Maximum speech duration reached")
                    break
            
            final_text = " ".join(all_text)
            print(f"[INFO] Final transcription: {final_text}")
            return final_text
            
        except KeyboardInterrupt:
            print("[INFO] Transcription stopped by user")
            return " ".join(all_text) if all_text else None
        except Exception as e:
            print(f"[ERROR] Error in transcribe_live: {str(e)}")
            return None

    def speak(self, text):
        """Speak the given text"""
        self.tts.speak(text)

    def cleanup(self):
        """Clean up resources"""
        self.p.terminate()
        if hasattr(self, 'tts'):
            self.tts.cleanup()