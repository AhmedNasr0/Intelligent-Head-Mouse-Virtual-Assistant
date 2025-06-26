import time
from PyQt6.QtCore import QThread, pyqtSignal
from .voice_command_worker import VoiceCommandWorker

class RAGVoiceWorker(QThread):
    user_message = pyqtSignal(str)
    rag_response = pyqtSignal(str)
    speaking_started = pyqtSignal()
    speaking_finished = pyqtSignal()

    def __init__(self , rag_service ,parent=None):
        super().__init__(parent)
        self._running = True
        self.rag_service = rag_service
        self.rag_service.initialize()

    def run(self):
        VoiceCommandWorker.listening = False
        self.speaking_started.emit()
        try:
            # Use the project's voice service for live transcription with silence detection
            text = self.rag_service.voice_service.transcribe_live()
            self.user_message.emit(text)
            response = self.rag_service.answer_question(text ,speak=False)
            self.rag_response.emit(response)
            self.rag_service.voice_service.speak(response)
        except Exception as e:
            self.user_message.emit(f"[Error: {e}]")
            self.rag_response.emit("")
        self.speaking_finished.emit()
        VoiceCommandWorker.listening = True
        self._running = False

    def stop(self):
        self._running = False 