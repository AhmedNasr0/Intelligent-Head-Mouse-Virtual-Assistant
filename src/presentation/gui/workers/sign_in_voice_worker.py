from PyQt6.QtCore import QThread, pyqtSignal
from presentation.gui.constants import signinSwitchMsg
import time

class SignInVoiceWorker(QThread):
    signup_command = pyqtSignal()

    def __init__(self, voice_service, parent=None):
        super().__init__(parent)
        self.voice_service = voice_service
        self._running = True
        self.timer = time.time()
        self.first_time = True

    def run(self):
        while self._running:
            if self.first_time:
                self.voice_service.speak(signinSwitchMsg)
                self.first_time = False
            else:
                if time.time() - self.timer > 20:
                    self.voice_service.speak(signinSwitchMsg)
                    self.timer = time.time()
            if not self._running:
                break
            
            audio = self.voice_service.record_audio()
            
            if not self._running:
                break
            if audio is not None:
                text = self.voice_service.transcribe(audio).strip().lower()
                if "sign up" in text or "signup" in text or "create account" in text :
                    self.voice_service.speak("Switching to sign up window.")
                    self.signup_command.emit()

    def stop(self):
        self._running = False 
        self.wait()