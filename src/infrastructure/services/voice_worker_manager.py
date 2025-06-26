from PyQt6.QtCore import QThread, pyqtSignal
from infrastructure.services.voice_service import VoiceService


class VoiceWorkerManager(QThread):
    command_detected = pyqtSignal(str)
    
    
    _instance = None

    def __init__(self):
        super().__init__()
        if VoiceWorkerManager._instance is not None:
            raise Exception("This is a singleton!")
        VoiceWorkerManager._instance = self
        self.voice_service = VoiceService.get_instance(interval=2)
        self._running = True
        self._listening = True
        self.context_commands = {}  # {context: {command: callback}}
        self.active_context = None
        self.current_window = None
        

    @staticmethod
    def get_instance():
        if VoiceWorkerManager._instance is None:
            VoiceWorkerManager()
        return VoiceWorkerManager._instance

    def set_context(self, context):
        self.active_context = context

    def register_command(self, context, commands, callback):
        if context not in self.context_commands:
            self.context_commands[context] = {}
        for command in commands:
            self.context_commands[context][command] = callback

    def pause_listening(self):
        self._listening = False

    def resume_listening(self):
        self._listening = True

    def run(self):
        while self._running:
            if not self._listening:
                self.msleep(100)
                continue
            try:
                audio = self.voice_service.record_audio()
                if audio is not None:
                    text = self.voice_service.transcribe(audio).strip().lower()
                    if self.active_context and self.active_context in self.context_commands:
                        for command, callback in self.context_commands[self.active_context].items():
                            if command in text:
                                callback()
                                self.command_detected.emit(command)
            except Exception as e:
                print(f"VoiceWorkerManager error: {e}")
    def speak(self, text):
        self.voice_service.speak(text)
        
    def stop(self):
        self._running = False 
        
        
    