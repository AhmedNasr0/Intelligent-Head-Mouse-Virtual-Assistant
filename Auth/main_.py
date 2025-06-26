import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                            QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
import cv2
import numpy as np
from real_time_verify import real_time_verification
import mediapipe as mp
import pyautogui
import speech_recognition as sr
import threading
import queue

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Accessibility Assistant")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.init_ui()
        self.init_face_detection()
        self.init_voice_recognition()
        
        # State variables
        self.is_logged_in = False
        self.is_tracking = False
        self.is_listening = False
        self.command_queue = queue.Queue()
        
        # Start command processing thread
        self.command_thread = threading.Thread(target=self.process_commands, daemon=True)
        self.command_thread.start()
        
    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Create main content area
        self.content_area = QStackedWidget()
        main_layout.addWidget(self.content_area)
        
        # Add pages
        self.login_page = self.create_login_page()
        self.dashboard_page = self.create_dashboard_page()
        self.settings_page = self.create_settings_page()
        
        self.content_area.addWidget(self.login_page)
        self.content_area.addWidget(self.dashboard_page)
        self.content_area.addWidget(self.settings_page)
        
        # Set initial page
        self.content_area.setCurrentWidget(self.login_page)
        
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setMaximumWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Logo/Title
        title = QLabel("Accessibility\nAssistant")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 16, QFont.Bold))
        sidebar_layout.addWidget(title)
        
        # Navigation buttons
        self.login_btn = QPushButton("Login")
        self.dashboard_btn = QPushButton("Dashboard")
        self.settings_btn = QPushButton("Settings")
        
        for btn in [self.login_btn, self.dashboard_btn, self.settings_btn]:
            btn.setMinimumHeight(40)
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # Connect buttons
        self.login_btn.clicked.connect(lambda: self.content_area.setCurrentWidget(self.login_page))
        self.dashboard_btn.clicked.connect(lambda: self.content_area.setCurrentWidget(self.dashboard_page))
        self.settings_btn.clicked.connect(lambda: self.content_area.setCurrentWidget(self.settings_page))
        
        # Initially disable dashboard and settings
        self.dashboard_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        
        return sidebar
        
    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Face Recognition Login")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 24))
        layout.addWidget(title)
        
        # Status label
        self.login_status = QLabel("Please look at the camera")
        self.login_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.login_status)
        
        # Login button
        self.login_button = QPushButton("Start Face Recognition")
        self.login_button.clicked.connect(self.start_face_recognition)
        layout.addWidget(self.login_button)
        
        return page
        
    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 24))
        layout.addWidget(title)
        
        # Control buttons
        self.track_button = QPushButton("Start Head Tracking")
        self.track_button.clicked.connect(self.toggle_head_tracking)
        layout.addWidget(self.track_button)
        
        self.voice_button = QPushButton("Start Voice Commands")
        self.voice_button.clicked.connect(self.toggle_voice_commands)
        layout.addWidget(self.voice_button)
        
        # Status labels
        self.track_status = QLabel("Head Tracking: Off")
        self.voice_status = QLabel("Voice Commands: Off")
        layout.addWidget(self.track_status)
        layout.addWidget(self.voice_status)
        
        return page
        
    def create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Settings")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 24))
        layout.addWidget(title)
        
        # Add settings controls here
        return page
        
    def init_face_detection(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.5
        )
        
    def init_voice_recognition(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
    def start_face_recognition(self):
        self.login_button.setEnabled(False)
        self.login_status.setText("Verifying...")
        
        # Start face recognition in a separate thread
        threading.Thread(target=self.run_face_recognition, daemon=True).start()
        
    def run_face_recognition(self):
        model_path = "saved_models/model_aug_acc1.00_adam_binary_ct_20250325.keras"
        try:
            real_time_verification(model_path)
            self.is_logged_in = True
            self.update_ui_after_login()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Face recognition failed: {str(e)}")
            self.login_button.setEnabled(True)
            self.login_status.setText("Verification failed. Please try again.")
            
    def update_ui_after_login(self):
        self.login_button.setEnabled(True)
        self.login_status.setText("Login successful!")
        self.dashboard_btn.setEnabled(True)
        self.settings_btn.setEnabled(True)
        self.content_area.setCurrentWidget(self.dashboard_page)
        
    def toggle_head_tracking(self):
        self.is_tracking = not self.is_tracking
        if self.is_tracking:
            self.track_button.setText("Stop Head Tracking")
            self.track_status.setText("Head Tracking: On")
            threading.Thread(target=self.run_head_tracking, daemon=True).start()
        else:
            self.track_button.setText("Start Head Tracking")
            self.track_status.setText("Head Tracking: Off")
            
    def toggle_voice_commands(self):
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.voice_button.setText("Stop Voice Commands")
            self.voice_status.setText("Voice Commands: On")
            threading.Thread(target=self.run_voice_recognition, daemon=True).start()
        else:
            self.voice_button.setText("Start Voice Commands")
            self.voice_status.setText("Voice Commands: Off")
            
    def run_head_tracking(self):
        cap = cv2.VideoCapture(0)
        while self.is_tracking:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process frame with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            
            if results.detections:
                for detection in results.detections:
                    # Get face position and move cursor
                    bbox = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    
                    # Calculate face center
                    x = int(bbox.xmin * iw + bbox.width * iw / 2)
                    y = int(bbox.ymin * ih + bbox.height * ih / 2)
                    
                    # Move cursor (scaled to screen size)
                    screen_width, screen_height = pyautogui.size()
                    cursor_x = int(x * screen_width / iw)
                    cursor_y = int(y * screen_height / ih)
                    pyautogui.moveTo(cursor_x, cursor_y)
                    
        cap.release()
        
    def run_voice_recognition(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=1)
                    command = self.recognizer.recognize_google(audio).lower()
                    self.command_queue.put(command)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    self.voice_status.setText("Voice Commands: Error - Check internet connection")
                    break
                    
    def process_commands(self):
        while True:
            try:
                command = self.command_queue.get(timeout=1)
                self.execute_command(command)
            except queue.Empty:
                continue
                
    def execute_command(self, command):
        # Add command execution logic here
        if "click" in command:
            pyautogui.click()
        elif "double click" in command:
            pyautogui.doubleClick()
        elif "right click" in command:
            pyautogui.rightClick()
        elif "scroll up" in command:
            pyautogui.scroll(10)
        elif "scroll down" in command:
            pyautogui.scroll(-10)
        elif "stop" in command:
            self.is_tracking = False
            self.is_listening = False
            self.track_status.setText("Head Tracking: Off")
            self.voice_status.setText("Voice Commands: Off")
            self.track_button.setText("Start Head Tracking")
            self.voice_button.setText("Start Voice Commands")
            
    def closeEvent(self, event):
        self.is_tracking = False
        self.is_listening = False
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())