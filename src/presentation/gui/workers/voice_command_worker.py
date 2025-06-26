import time
from PyQt6.QtCore import QThread, pyqtSignal
import webbrowser
import pyautogui

class VoiceCommandWorker(QThread):
    command_recognized = pyqtSignal(str)
    command_executed = pyqtSignal(str)
    listening = True  # Class-level flag to pause when RAG is active

    def __init__(self, voice_service, mouse_controller, parent=None):
        super().__init__(parent)
        self.voice_service = voice_service
        self.voice_service.set_interval(0.5)
        self._running = True
        self.mouse_controller = mouse_controller  # Add mouse controller reference

    def run(self):
        while self._running:
            if not VoiceCommandWorker.listening:
                time.sleep(0.1)
                continue
            try:
                audio = self.voice_service.record_audio()
                if audio is not None:
                    text = self.voice_service.transcribe(audio).strip()
                    self.command_recognized.emit(text)
                    self.handle_command(text)
            except Exception as e:
                print(f"VoiceCommandWorker error: {e}")

    def handle_command(self, text):
        text = text.lower()
        if text in ["you","ha","he","ah"]:
            return
        if text.startswith("open "):
            site = text[5:].strip()
            if site == "youtube":
                webbrowser.open("https://youtube.com")
                self.voice_service.speak("Opened YouTube")
                self.command_executed.emit("Opened YouTube")
            elif site == "google":
                webbrowser.open("https://google.com")
                self.voice_service.speak("Opened Google")
                self.command_executed.emit("Opened Google")
            else:
                webbrowser.open(f"https://{site}.com")
                self.voice_service.speak(f"Opened {site}")
                self.command_executed.emit(f"Opened {site}")
        elif text.startswith("type "):
            to_type = text[5:].strip()
            pyautogui.write(to_type)
            self.voice_service.speak(f"Typed: {to_type}")
            self.command_executed.emit(f"Typed: {to_type}")
        elif text.startswith("search in youtube for "):
            query = text.replace("search in youtube for ", "").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
            self.voice_service.speak(f"Searched YouTube for: {query}")
            self.command_executed.emit(f"Searched YouTube for: {query}")
        # --- New: Mouse actions by voice ---
        elif text in ["click", "Click"]:
            if self.mouse_controller:
                self.mouse_controller.action_controller.click()
        elif text in ["right click", "Right click"]:
            if self.mouse_controller:
                self.mouse_controller.action_controller.right_click()
        elif text in ["double click", "Double click"]:
            if self.mouse_controller:
                self.mouse_controller.action_controller.double_click()
        elif text in ["scroll up", "Scroll up"]:
            if self.mouse_controller:
                self.mouse_controller.action_controller.scroll_up()
        elif text in ["scroll down", "Scroll down"]:
            if self.mouse_controller:
                self.mouse_controller.action_controller.scroll_down()
        # --- New: Set action by voice ---
        elif text.startswith("set action to "):
            action = text.replace("set action to ", "").strip().lower()
            if self.mouse_controller:
                valid_actions = ["click", "right click", "double click", "scroll up", "scroll down"]
                action_map = {
                    "click": "click",
                    "right click": "right_click",
                    "double click": "double_click",
                    "scroll up": "scroll_up",
                    "scroll down": "scroll_down"
                }
                if action in action_map:
                    self.mouse_controller.set_action(action_map[action])
                    self.voice_service.speak(f"Action has been set to {action}")
                    self.command_executed.emit(f"Action has been set to {action}")

    def stop(self):
        self._running = False 