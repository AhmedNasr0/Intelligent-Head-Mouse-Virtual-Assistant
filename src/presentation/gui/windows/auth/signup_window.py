from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
from presentation.gui.workers.sign_up_voice_worker import SignUpVoiceWorker
from presentation.gui.pages.voiceInputPage import VoiceInputPage
from presentation.gui.pages.imageCapturePage import ImageCapturePage
from application.use_cases.auth.sign_up import SignUpCommand, SignUpUseCase
from infrastructure.Repository.UserRepository import UserRepository
from infrastructure.Repository.FaceRepository import FaceRepository
from infrastructure.Repository.UserSettingsRepository import UserSettingsRepository
from infrastructure.utils.image_utils import frame_to_bytes
from PyQt6.QtCore import pyqtSignal

class SignUpWindow(QWidget):
    signup_successful = pyqtSignal()
    signin_requested = pyqtSignal()
    
    def __init__(self, voice_service , video_stream):
        super().__init__()
        self.username = ""
        self.captured_images = []
        self.user_repository = UserRepository()
        self.face_repository = FaceRepository()
        self.user_settings_repo = UserSettingsRepository()
        self.userUseCase = SignUpUseCase(self.user_repository, self.face_repository , settings_repo=self.user_settings_repo)
        self.setWindowTitle("Sign Up")
        self.setFixedSize(1200, 700)
        
        
        
        self.setStyleSheet("background-color: white;")
        
        # Initialize services
        self.stream = video_stream
        self.voice_worker = SignUpVoiceWorker(voice_service, transcription_interval=2)
        
        # Setup UI
        self.setup_ui()
        
        # Connect signals
        self.voice_worker.proceed_to_next.connect(self.show_image_capture_page)
        self.voice_worker.capture_image.connect(self.start_image_capture)
        self.voice_worker.registration_complete.connect(self.handle_registration_complete)
        self.voice_worker.username_detected.connect(self.handle_username_detected)
        self.voice_worker.signin_command.connect(self.handle_signin_command)
        self.voice_worker.computer_speech.connect(self.image_page.update_computer_speech)
        self.voice_worker.try_again_requested.connect(self.handle_try_again)
        
        # Start with voice input page
        self.show_voice_input_page()

    def setup_ui(self):
        self.main_layout = QStackedLayout()
        self.setLayout(self.main_layout)
        self.setStyleSheet("background-color: white;")
        
        # Create pages
        self.voice_page = VoiceInputPage(self.voice_worker)
        self.image_page = ImageCapturePage(self.stream)
        
        # Connect image confirmed signal
        self.image_page.image_confirmed.connect(self.handle_image_confirmed)
        
        # Add pages to main layout
        self.main_layout.addWidget(self.voice_page)
        self.main_layout.addWidget(self.image_page)

    def show_voice_input_page(self):
        self.main_layout.setCurrentWidget(self.voice_page)
        self.voice_page.update_computer_speech("Please say your username. For example, say 'My username is John'.")
        self.voice_worker.start()

    def show_image_capture_page(self):
        self.main_layout.setCurrentWidget(self.image_page)

    def start_image_capture(self):
        self.image_page.start_image_capture()

    def handle_username_detected(self, username):
        """Store the detected username in userData"""
        self.username = username

    def handle_image_confirmed(self, image_data):
        """Store confirmed image in userData"""
        self.captured_images.append(image_data)

    def handle_registration_complete(self):
        try:
            # Ensure userData has the required fields
            if not self.username:
                raise ValueError("Username is required")
            if not self.captured_images:
                raise ValueError("At least one image is required")

            signup_command = SignUpCommand(
                username=self.username,
                images=self.captured_images
            )
            
            # Execute signup with collected data
            user = self.userUseCase.execute(signup_command)
            if user.get('success', False):
                self.signup_successful.emit()
                self.cleanup_resources()
            else:
                error_msg = user.get('error', 'Unknown error occurred')
                raise Exception(error_msg)
            
        except Exception as e:
            print("Error", f"Failed to create user: {str(e)}")
            self.cleanup_resources()
            

    def cleanup_resources(self):
        try:
            print("[DEBUG] Cleaning up SignUpWindow resources...")
            if hasattr(self, 'voice_worker') and self.voice_worker is not None:
                print("[DEBUG] Stopping voice_worker...")
                self.voice_worker.stop()
                print(f"[DEBUG] voice_worker is running? {self.voice_worker.isRunning()}")
                self.voice_worker = None
            print("[DEBUG] All resources cleaned up (except shared video stream).")
        except Exception as e:
            print(f"[DEBUG] Error during signup cleanup: {e}")

    def handle_signin_command(self):
        self.signin_requested.emit()

    def set_computer_speech(self, text):
        self.image_page.update_computer_speech(text)

    def closeEvent(self, event):
        try:
            if hasattr(self, 'voice_worker') and self.voice_worker is not None:
                self.voice_worker.stop()
            event.accept()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            event.accept()

    def handle_try_again(self):
        # Remove last image from UI and from captured_images list
        self.image_page.clear_last_captured_image()
        if self.captured_images:
            self.captured_images.pop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignUpWindow()
    window.show()
    sys.exit(app.exec()) 