from TTS.api import TTS
import os
import numpy as np

class RealisticTTS:
    # model_name = "tts_models/en/ljspeech/tacotron2-DDC"
    model_name="tts_models/en/ljspeech/fast_pitch"
    def __init__(self, model_name=model_name):
        self.model_name = model_name
        self._ensure_model_downloaded()
        self.tts = TTS(model_name=self.model_name, progress_bar=False , gpu=True)


    def _ensure_model_downloaded(self):
        home_dir = os.path.expanduser("~")
        cache_dir = os.path.join(home_dir, ".local", "share", "tts", self.model_name.replace("/", "--"))
        if not os.path.exists(cache_dir):
            print(f"[INFO] Downloading TTS model: {self.model_name}")
            _ = TTS(model_name=self.model_name, progress_bar=True)

    def speak(self, text: str):
        wav = self.tts.tts(text)
        import sounddevice as sd
        sd.play(wav, self.tts.synthesizer.output_sample_rate)
        sd.wait()

    def cleanup(self):
        # No resources to cleanup, but method added to avoid AttributeError
        pass
