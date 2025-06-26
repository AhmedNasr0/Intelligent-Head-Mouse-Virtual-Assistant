from PyQt6.QtCore import QThread, pyqtSignal
from infrastructure.services.ml.NER_username import NERUsernameService
from presentation.gui.constants import welcome_msg
class SignUpVoiceWorker(QThread):
    # Signals for communication with the main thread
    username_detected = pyqtSignal(str)  # Emits detected username
    listening_started = pyqtSignal()  # Emits when listening starts
    listening_stopped = pyqtSignal()  # Emits when listening stops
    error_occurred = pyqtSignal(str)  # Emits error messages
    live_transcription = pyqtSignal(str)  # Emits live transcription text
    accumulated_text = pyqtSignal(str)  # Emits accumulated text
    proceed_to_next = pyqtSignal()  # Signal to move to next page
    capture_image = pyqtSignal()  # Signal to trigger image capture
    image_captured = pyqtSignal()  # Signal when image is captured
    registration_complete = pyqtSignal()  # Signal when registration is complete
    signin_command = pyqtSignal()  # New signal for switching to sign in
    computer_speech = pyqtSignal(str)  # Emits computer speech text
    try_again_requested = pyqtSignal()  # Signal to request clearing the last captured image

    def __init__(self, voice_service, transcription_interval=2):
        super().__init__()
        
        print(f"Initializing VoiceWorker with interval={transcription_interval}")
        self.voice_service = voice_service
        self.ner_service = NERUsernameService()
        self.is_running = False
        self.current_text = ""
        self.state = "WELCOME"  # Current state of the interaction
        self.detected_username = None
        self.image_count = 0
        self.max_images = 2

    def is_skip_words(self,text):
        skip_words = ["you", "your", "uh", "um", "ah"]
        return text in skip_words
    
    
    def run(self):
        """Main thread loop"""
        try:
            print(f"[DEBUG] VoiceWorker (thread id: {int(self.currentThreadId())}) starting...")
            self.is_running = True
            self.listening_started.emit()
            while self.is_running:
                if self.state == "WELCOME":
                    self.handle_welcome_state()
                elif self.state == "LISTENING_USERNAME":
                    self.handle_username_state()
                elif self.state == "USERNAME_CONFIRMATION":
                    self.handle_username_confirmation()
                elif self.state == "IMAGE_CAPTURE":
                    self.handle_image_capture()
                elif self.state == "IMAGE_CONFIRMATION":
                    self.handle_image_confirmation()
                elif self.state == "COMPLETE":
                    self.handle_completion()
                    break
                QThread.msleep(50)
        except Exception as e:
            print(f"[DEBUG] Error in VoiceWorker: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(f"Error in voice worker: {str(e)}")
        finally:
            self.is_running = False
            self.listening_stopped.emit()
            print(f"[DEBUG] VoiceWorker (thread id: {int(self.currentThreadId())}) stopped.")

    def handle_welcome_state(self):
        """Handle welcome state"""
        self.computer_speech.emit(welcome_msg)
        self.voice_service.speak(welcome_msg)
        while self.is_running and self.state == "WELCOME":
            if not self.check_if_running():
                break
            audio = self.voice_service.record_audio()
            if not self.check_if_running():
                break
            if audio is not None:
                text = self.voice_service.transcribe(audio).strip().lower()
                text = text.replace('.', '')
                
                if self.is_skip_words(text):
                    continue
                print(f"Text: {text}")
                self.live_transcription.emit(text)
                if "sign in" in text or "signin" in text or "login" in text or "log in" in text:
                    self.signin_command.emit()
                    self.is_running = False
                    break
                if "start" in text:
                    self.state = "LISTENING_USERNAME"
                    username_prompt = "Please say your username"
                    self.computer_speech.emit(username_prompt)
                    self.voice_service.speak(username_prompt)
                    break

    def handle_username_state(self):
        """Handle username listening state"""
        self.current_text = ""
        
        while self.is_running and self.state == "LISTENING_USERNAME":
            if not self.check_if_running():
                break
            audio = self.voice_service.record_audio()
            if not self.check_if_running():
                break
            if audio is not None:
                text = self.voice_service.transcribe(audio).strip().lower()
                # Remove dots from text
                text = text.replace('.', '')
                
                if self.is_skip_words(text):
                    continue
                self.live_transcription.emit(text)  # Emit current transcription
                self.current_text += " " + text
                self.accumulated_text.emit(self.current_text.strip())  # Emit accumulated text
                print(f"Current text: {self.current_text}")
                print(f"Text: {text}")
                username = self.ner_service.extract_username(text)
                print(f"Username: {username}")
                if username:
                    self.detected_username = username
                    self.username_detected.emit(username)
                    self.voice_service.speak(f"I detected the username: {username}. Is this correct ?")
                    self.state = "USERNAME_CONFIRMATION"
                    break

    def handle_username_confirmation(self):
        """Handle username confirmation state"""
        while self.is_running and self.state == "USERNAME_CONFIRMATION":
            if not self.check_if_running():
                break
            audio = self.voice_service.record_audio()
            if not self.check_if_running():
                break
            if audio is not None:
                text = self.voice_service.transcribe(audio).strip().lower()
                text = text.replace('.', '')
                
                if self.is_skip_words(text):
                    continue
                self.live_transcription.emit(text)
                
                if "yes" in text or "correct" in text:
                    self.voice_service.speak("Great  Lets move on to capturing your photos.")
                    self.computer_speech.emit("Great , Let's move on to capturing your photos.")
                    self.state = "IMAGE_CAPTURE"
                    self.proceed_to_next.emit()
                    break
                elif "no" in text or "try" in text or "again" in text:
                    self.computer_speech.emit("Okay , Let's try again. Please say your username.")
                    self.voice_service.speak("Okay , Let's try again. Please say your username.") 
                    self.state = "LISTENING_USERNAME"
                    break

    def handle_image_capture(self):
        """Handle image capture state"""
        self.computer_speech.emit("Say 'take it' when you're ready for the photo.")
        self.voice_service.speak("Say 'take it' when you're ready for the photo.")
        while self.is_running and self.state == "IMAGE_CAPTURE":
            if not self.check_if_running():
                break
            audio = self.voice_service.record_audio()
            if not self.check_if_running():
                break
            if audio is not None:
                text = self.voice_service.transcribe(audio).strip().lower()
                text = text.replace('.', '')
                
                if self.is_skip_words(text):
                    continue
                self.live_transcription.emit(text)
                
                if "take" in text or "ready" in text:
                    self.voice_service.speak("Taking photo in 3 , , 2 , , 1")
                    self.capture_image.emit()
                    self.image_count += 1
                    
                    self.state = "IMAGE_CONFIRMATION"
                    break

    def handle_image_confirmation(self):
        """Handle image confirmation state"""
        self.computer_speech.emit("How's the photo? Say 'try again' to retake or 'save' to keep it.")
        self.voice_service.speak("How's the photo? Say 'try again' to retake or 'save' to keep it.")
        while self.is_running and self.state == "IMAGE_CONFIRMATION":
            if not self.check_if_running():
                break
            audio = self.voice_service.record_audio()
            if not self.check_if_running():
                break
            if audio is not None:
                text = self.voice_service.transcribe(audio).strip().lower()
                text = text.replace('.', '')
                
                if self.is_skip_words(text):
                    continue
                self.live_transcription.emit(text)
                
                if "try" in text or "again" in text:
                    self.try_again_requested.emit()
                    self.state = "IMAGE_CAPTURE"
                    break
                elif "save" in text or "keep" in text:
                    if self.image_count >= self.max_images:
                        self.state = "COMPLETE"
                    else:
                        self.computer_speech.emit("Great , Let's take one more photo")
                        self.voice_service.speak("Great  Lets take one more photo")
                        self.state = "IMAGE_CAPTURE"
                    break
    
    def check_if_running(self):
        if not self.is_running or self.isInterruptionRequested():
            return False
        return True
    
    def handle_completion(self):
        """Handle completion state"""
        self.computer_speech.emit("Perfect , Your email account has been created successfully. You can now login.")
        self.voice_service.speak("Perfect  Your email account has been created successfully. You can now login.")
        self.registration_complete.emit()

    
    
    def stop(self):
        """Stop the worker thread"""
        print(f"[DEBUG] Stopping VoiceWorker (thread id: {int(self.currentThreadId())}) ...")
        self.is_running = False
        self.wait(1000)
        self.terminate()
        self.wait()
        
        if not self.wait(2000):  # wait max 2 sec
            print("Thread did not stop in time, forcing termination...")
            self.requestInterruption()
            self.wait()
