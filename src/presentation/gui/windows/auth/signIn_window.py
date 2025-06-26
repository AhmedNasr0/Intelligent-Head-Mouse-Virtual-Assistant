from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
import cv2
from presentation.gui.workers.face_worker import FaceWorker
from infrastructure.Repository.UserRepository import UserRepository
from presentation.gui.constants import  main_page_width, main_page_height 
from presentation.gui.workers.sign_in_voice_worker import SignInVoiceWorker


class SignInWindow(QWidget):
    signin_successful = pyqtSignal()
    signup_requested = pyqtSignal()  # Signal to request switching to signup
    
    def __init__(self, voice_service , video_stream):    
        super().__init__()
        self.setWindowTitle("Real-Time Verification")
        self.setFixedSize(main_page_width, main_page_height)
        # Initialize repositories
        self.user_repository = UserRepository()
        
        # Setup UI
        self.image_label = QLabel()
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("border: 2px solid #ccc; border-radius: 8px;")
        self.image_label.setStyleSheet("""
            border: 2px solid #444;
            border-radius: 10px;
            box-shadow: 0px 0px 10px #aaa;
        """)
        
        
        
        self.status_label = QLabel("Verification in progress...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px;")
        
        self.signInNote =QLabel("If you do not have an account just say sign up to create one")
        self.signInNote.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signInNote.setStyleSheet("font-size: 16px;")
        
        layout = QVBoxLayout()
        layout.addWidget(self.image_label, stretch=8)
        layout.addWidget(self.status_label, stretch=1)
        layout.addWidget(self.signInNote, stretch=1)
        self.setLayout(layout)
        
        # Initialize camera stream
        self.stream = video_stream
        
        # Get model path
        current_file_path = Path(__file__)
        model_path = current_file_path.parent.parent.parent.parent.parent / "infrastructure" / "models" / "deepLearningModels" / "model_aug_acc1.00_adam_binary_ct_20250325.keras"
        
        
        self.voice_worker = SignInVoiceWorker(voice_service)
        self.voice_worker.signup_command.connect(self.handle_signup_command)
        self.voice_worker.start()
        
        
        # Initialize face worker
        self.face_worker = FaceWorker(model_path)
        self.face_worker.frame_ready.connect(self.update_frame)
        self.face_worker.verification_complete.connect(self.handle_verification)
        self.face_worker.error_occurred.connect(self.handle_error)
        self.face_worker.start()
        
        # Timer to update frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.capture_frame)
        self.timer.start(5)  # Update every 5ms
        
        # Timer for transition to dashboard
        self.transition_timer = QTimer()
        self.transition_timer.setSingleShot(True)
        self.transition_timer.timeout.connect(self.show_dashboard)

        

    def capture_frame(self):
        """Capture frame from camera and send to worker"""
        frame = self.stream.read()
        if frame is not None:
            self.face_worker.update_frame(frame)

    def update_frame(self, frame):
        """Update the UI with the processed frame"""
        if frame is not None:
            # Convert frame to RGB
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # Convert to QImage and display
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qt_image))


    def handle_verification(self, is_verified, user_id):
        """Handle verification result"""
        if is_verified:
            # Get user information
            user = self.user_repository.get_by_id(user_id)
            if user:
                self.user = user
                self.status_label.setText(f"✅ Welcome {user.name}!👋 Redirecting to dashboard ↗️")
                self.status_label.setStyleSheet("font-size: 16px; color: green;")
                # Stop the camera and worker
                self.timer.stop()
                self.stream.stop()
                self.face_worker.stop()
                
                # Start the transition timer
                self.transition_timer.start(3000)  # 3 seconds delay

    def show_dashboard(self):
        """Show the dashboard window and close the sign-in window"""
        self.signin_successful.emit()
        

    def handle_error(self, error_message):
        """Handle errors from the worker"""
        self.status_label.setText(f"❌ Error: {error_message}")
        self.status_label.setStyleSheet("font-size: 16px; color: red;")

    def handle_signup_command(self):
        # Speak and emit a signal to request switching to the signup window
        self.signup_requested.emit()

    def closeEvent(self, event):
        try:
            print("Closing SignInWindow...")
            
            if hasattr(self, 'face_worker') and self.face_worker is not None:
                print("Stopping FaceWorker...")
                self.face_worker.stop()
                self.face_worker.wait()
                
            if hasattr(self, 'voice_worker') and self.voice_worker is not None:
                print("Stopping VoiceWorker...")
                self.voice_worker.stop()
                self.voice_worker.wait()
            event.accept()
            print("SignInWindow closed.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            event.accept()

# if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # window = SignInWindow()
    # window.show()
    # sys.exit(app.exec())

