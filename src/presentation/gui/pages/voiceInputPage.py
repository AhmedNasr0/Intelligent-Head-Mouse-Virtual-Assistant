from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


class VoiceInputPage(QWidget):
    def __init__(self, voice_worker):
        super().__init__()
        self.voice_worker = voice_worker
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setStyleSheet("background-color: white;")

        
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.WelcomeHeader = QLabel("Welcome to Intelligent Head-Mouse Virtual Assistant \n Lets get you started and create your account")
        
        self.WelcomeHeader.setStyleSheet(" QLabel {font-size: 26px; color: white; width: 100%; height: fit-content; padding: 2px; background-color:green ; border-radius: 10px;}")
        self.WelcomeHeader.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.WelcomeHeader)
        
        
        # Computer speech label
        self.computer_speech_label = QLabel("Computer 🗣️: ")
        self.computer_speech_label.setStyleSheet("font-size: 18px; color: black; background-color: white;")
        self.computer_speech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.computer_speech_label)
        
        
        # Accumulated text label
        self.accumulated_label = QLabel("You said 💬:")
        self.accumulated_label.setStyleSheet("font-size: 16px; color: black;")
        self.accumulated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.accumulated_label.setWordWrap(True)
        layout.addWidget(self.accumulated_label)
        
        # Voice button
        self.voice_btn = QPushButton("Start Voice Input")
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 16px;
                disabled: true;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.voice_btn.clicked.connect(self.start_voice_input)
        layout.addWidget(self.voice_btn)
        
        self.setLayout(layout)

    def connect_signals(self):
        self.voice_worker.username_detected.connect(self.handle_username)
        self.voice_worker.listening_started.connect(self.handle_listening_started)
        self.voice_worker.listening_stopped.connect(self.handle_listening_stopped)
        self.voice_worker.error_occurred.connect(self.handle_voice_error)
        self.voice_worker.accumulated_text.connect(self.handle_accumulated_text)
        self.voice_worker.computer_speech.connect(self.update_computer_speech)

    def start_voice_input(self):
        self.voice_btn.setEnabled(False)
        self.voice_btn.setText("Listening...")
        self.voice_worker.start()

    def update_computer_speech(self, text):
        """Update the computer speech label"""
        self.computer_speech_label.setText(f"Computer 🗣️: {text}")


    def handle_listening_started(self):
        self.voice_btn.setEnabled(False)
        self.voice_btn.setText("Listening...")

    def handle_listening_stopped(self):
        self.voice_btn.setEnabled(True)
        self.voice_btn.setText("Start Voice Input")
        self.update_computer_speech("Processing your voice input...")

    def handle_voice_error(self, error_message):
        self.voice_btn.setEnabled(True)
        self.voice_btn.setText("Start Voice Input")
        self.update_computer_speech("Sorry, there was an error. Please try again.")

    def handle_username(self, username):
        self.username = username 
        self.update_computer_speech(f"I heard your username is ( {username} ) . Is this correct?")

    def handle_accumulated_text(self, text):
        self.accumulated_label.setText(f"You said 💬: {text}")