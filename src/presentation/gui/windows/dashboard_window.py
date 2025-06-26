from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy, QScrollArea, QFrame, QScrollBar
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2
import threading
from infrastructure.services.mouse_service import HeadControlledCursor
from infrastructure.services.actions import ActionController
from presentation.gui.constants import dashboard_page_width, dashboard_page_height
import time
from presentation.gui.workers.voice_command_worker import VoiceCommandWorker
from presentation.gui.workers.rag_voice_worker import RAGVoiceWorker
from infrastructure.services.rag_service import RAGService
from infrastructure.Repository.UserSettingsRepository import UserSettingsRepository
import uuid
from domain.entities.UserSettings import UserSettings


class RAGChatWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(200)
        self.setStyleSheet("background: white; text:black ; border-radius: 10px; border-top: 1px solid #ccc;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        # Info button row
        info_row = QHBoxLayout()
        info_row.addStretch(1)
        self.info_btn = QPushButton("i")
        self.info_btn.setFixedSize(20, 20)
        self.info_btn.setStyleSheet("QPushButton { background: green; color: black; border-radius: 10px; font-weight: bold; } QPushButton::hover { background: #2980b9; }")
        self.info_btn.setToolTip("click the mic to ask your question by voice.")
        self.info_btn.setCursor(Qt.CursorShape.WhatsThisCursor)
        info_row.addWidget(self.info_btn)
        layout.addLayout(info_row)
        # Chat history area
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFixedHeight(140)
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.addStretch(1)
        self.chat_area.setWidget(self.chat_content)
        layout.addWidget(self.chat_area, 1)  # Make chat area expand
        # Start talking button
        # Add default message
        self.add_message("How can I help you today?", sender="computer")
        
        self.talk_btn = QPushButton("🎤 Start Talking")
        self.talk_btn.setStyleSheet("background: green; color: black; border: 1px solid; border-radius: 50px; font-weight: bold;")
        self.talk_btn.setFixedHeight(25)
        layout.addWidget(self.talk_btn)
        
    def add_message(self, text, sender="user"):
        label = QLabel(text)
        if sender == "user":
            label.setStyleSheet("background: gray; color: white; border-radius: 15px; padding: 3px; margin: 2px 0;")
        else:
            label.setStyleSheet("background: green; color: white; border-radius: 15px; padding: 3px; margin: 2px 0;")
        label.setWordWrap(True)
        self.chat_layout.insertWidget(self.chat_layout.count()-1, label)
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum()))

class DashboardWindow(QWidget):
    """
    Main dashboard window for the head-controlled cursor system.
    Provides a user interface for controlling cursor actions and settings.
    """
    
    def __init__(self, voice_service, user=None):
        """
        Initialize the dashboard window with all necessary components.
        Sets up the UI, initializes controllers, and starts video processing.
        """
        super().__init__()
        
        self.scaling_factor = self.screen().devicePixelRatio() # the scaling factor of the screen
        self.voice_service = voice_service
        self.user = user
        self.setWindowTitle("Intelligent Head-Mouse Virtual Assistant")
        self.setFixedSize(dashboard_page_width, dashboard_page_height)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)  # Always on top
                
        
        self.settings_repo = UserSettingsRepository()
        # --- Load user settings from DB if user is provided ---
        # Default settings
        
        
        # --- Load user settings from DB if user is provided ---
        self.settings_repo = UserSettingsRepository()
        if self.user is not None:
            try:
                print(f"[DEBUG] Loading user: {self.user}")
                print(f"[DEBUG] Loading id for user: {self.user.user_id}")
                user_id = uuid.UUID(str(self.user.user_id))
                print(f"[DEBUG] Loading settings for user: {user_id}")
                settings = self.settings_repo.get_by_user_id(user_id)
                
                if settings:
                    # Settings exist for this user, use them
                    smoothing = settings.smoothing
                    amplification = settings.amplification
                    print(f"[DEBUG] Successfully loaded settings: smoothing={smoothing}, amplification={amplification}")
                else:
                    # Create new settings for this user with default values
                    settings = UserSettings(
                        user_id=user_id,
                        smoothing=smoothing,
                        amplification=amplification
                    )
                    self.settings_repo.add(settings)
                    print(f"[DEBUG] Created new settings: smoothing={smoothing}, amplification={amplification}")
            except Exception as e:
                print(f"[ERROR] Failed to load user settings: {e}")
                import traceback
                traceback.print_exc()
        self.mouse_controller = HeadControlledCursor(dashboard_window=self, smoothing_factor=smoothing, amplification=amplification)
        self.action_controller = ActionController()
        self.action_controller.dashboard_window = self  # Connect with action controller
        
        # Action tracking
        self.current_action = None  # Currently selected action
        
        # Window state tracking
        self.is_visible = False  # Track if window is visible
        
        # Drag and drop state
        self.is_dragging = False
        self.drag_start_pos = None
        self.selected_item = None
        
        # Time tracking for debug prints
        self.time = time.time()
        
        # Calibration countdown flag
        self.is_calibrating_countdown = False
        
        
        
        # Setup UI and start video processing
        self.setup_ui()
        # --- Update value labels to reflect loaded settings ---
        if hasattr(self, 'amplification_value'):
            self.amplification_value.setText(f"{self.mouse_controller.amplification:.1f}")
        if hasattr(self, 'smoothing_value'):
            self.smoothing_value.setText(f"{self.mouse_controller.smoothing_factor:.2f}")
        self.start_video()
        # Start calibration countdown on startup
        self.handle_recalibrate()

        # Start VoiceCommandWorker for global commands
        self.voice_command_worker = VoiceCommandWorker(self.voice_service, self.mouse_controller)
        self.voice_command_worker.command_recognized.connect(self.on_command_recognized)
        self.voice_command_worker.command_executed.connect(self.on_command_executed)
        self.voice_command_worker.start()

        # Connect RAG chat button
        self.rag_chat.talk_btn.clicked.connect(self.start_rag_voice_chat)
    
    def setup_ui(self):
        """
        Set up the user interface components including:
        - Camera feed display
        - Action buttons
        - Control settings (amplification, smoothing)
        - Status labels
        """
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(5, 5, 5, 10)
        
        # Welcome message at the top
        if self.user is not None:
            print(self.user)
            self.welcome_label = QLabel(f"Welcome, {self.user.name}!👋")
            self.welcome_label.setStyleSheet("font-size: 14px; color: #2ecc71; font-weight: bold; margin-bottom: 8px; background-color: white;")
            self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.welcome_label)
        
        # Camera feed section
        self.setup_camera_section(layout)
        
        # Control buttons section
        self.setup_control_buttons(layout)
        
        # Settings controls section
        self.setup_settings_controls(layout)
        
        # Add RAG chat widget at the bottom
        self.rag_chat = RAGChatWidget()
        layout.addWidget(self.rag_chat, alignment=Qt.AlignmentFlag.AlignBottom)
        
        self.setLayout(layout)
    
    def setup_camera_section(self, layout):
        """
        Set up the camera feed display section.
        
        Args:
            layout: The main layout to add components to
        """
        # Calculate fixed height for camera (40% of dashboard height)
        camera_height = int(dashboard_page_height * 0.25)
        
        # Camera container
        camera_container = QWidget()
        camera_container.setFixedHeight(camera_height)
        camera_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        camera_container.setStyleSheet("background-color: white;")
        # Status label for calibration
        self.status_label = QLabel("Calibrating...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 5px;
            }
        """)
        camera_layout.addWidget(self.status_label)
        
        # Calibration instruction label (English)
        self.calib_instruction_label = QLabel("Please look at the camera, facing the center\n, for calibration.")
        self.calib_instruction_label.setStyleSheet("color: white; background-color: green; border-radius: 10px; font-weight: bold; font-size: 9px; margin-bottom: 2px;")
        self.calib_instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_layout.addWidget(self.calib_instruction_label)
        
        # Camera feed label
        self.camera_label = QLabel()
        self.camera_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: black;
                border: 1px solid green;
                border-radius: 10px;
            }
        """)
        camera_layout.addWidget(self.camera_label)
        
        layout.addWidget(camera_container)
    
    def setup_control_buttons(self, layout):
        """
        Set up the action control buttons section.
        
        Args:
            layout: The main layout to add components to
        """
        # Create buttons container
        self.buttons_container = QWidget()
        self.buttons_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        buttons_layout = QVBoxLayout(self.buttons_container)
        buttons_layout.setSpacing(2)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_container.setStyleSheet("background-color: white;")
        
        # Define available actions
        self.buttons = {
            "Click": self.action_controller.click,
            "Double Click": self.action_controller.double_click,
            "Right Click": self.action_controller.right_click,
            "Scroll Up": self.action_controller.scroll_up,
            "Scroll Down": self.action_controller.scroll_down,
            "Recalibrate": self.handle_recalibrate
        }
        
        # Calculate button height
        left_height = int(dashboard_page_height * 0.25) # 25% of the dashboard height 200px
        btn_height = int(left_height / (len(self.buttons)))
        
        # Create and add action buttons
        for action_name, action_func in self.buttons.items():
            btn = self.create_action_button(action_name, action_func, btn_height)
            buttons_layout.addWidget(btn)
        
        # Add drag instructions
        drag_label = QLabel("To drag: Hold smile for 2 seconds")
        drag_label.setStyleSheet("""
            QLabel {
                background-color: green;
                width: 100%;
                height: 10px;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                font-size: 10px;
                margin-top: 5px;
            }
        """)
        drag_label.setFixedHeight(20)
        buttons_layout.addWidget(drag_label)
        
        layout.addWidget(self.buttons_container)
    
    def create_action_button(self, action_name, action_func, height):
        """
        Create a styled action button.
        
        Args:
            action_name: Name of the action
            action_func: Function to call when button is clicked
            height: Height of the button
            
        Returns:
            QPushButton: The created button
        """
        btn = QPushButton(action_name)
        btn.setFixedHeight(height)
        btn.setMinimumSize(70, height)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet("""
            QPushButton {
                background-color: green;
                color: white;
                border: 1px solid green;
                border-radius: 10px;
                padding: 5px;
                font-weight: bold;
                font-size: 14px;
                margin-top: 2px;
                width: 90%;
                margin-left: 5%;
                margin-right: 5%;
            }
            QPushButton:hover {
                background-color: lightgreen;
            }
            QPushButton:checked {
                background-color: lightgreen;
                border: 2px solid lightgreen;
            }
            QPushButton:pressed {
                background-color: lightgreen;
            }
        """)
        btn.setCheckable(True)
        btn.clicked.connect(lambda checked, name=action_name, func=action_func: self.on_action_selected(name, func))
        return btn
    
    def setup_settings_controls(self, layout):
        """
        Set up the settings controls section (amplification and smoothing).
        
        Args:
            layout: The main layout to add components to
        """
        # Calculate button height
        btn_height = 25
        
        # Add amplification controls
        self.setup_amplification_controls(layout, btn_height)
        
        # Add smoothing controls
        self.setup_smoothing_controls(layout, btn_height)
    
    def setup_amplification_controls(self, layout, btn_height):
        """
        Set up amplification control widgets.
        
        Args:
            layout: The main layout to add components to
            btn_height: Height of the control buttons
        """
        amplification_container = QWidget()
        amplification_layout = QHBoxLayout(amplification_container)
        amplification_layout.setContentsMargins(0, 0, 0, 5)
        amplification_container.setStyleSheet("background-color: white;")
        # Label
        amplification_label = QLabel("Amplification:")
        amplification_label.setStyleSheet("color: black; font-weight: bold;")
        amplification_layout.addWidget(amplification_label)
        
        # Value display
        self.amplification_value = QLabel(f"{self.mouse_controller.amplification:.1f}")
        self.amplification_value.setStyleSheet("color: black; font-weight: bold;")
        amplification_layout.addWidget(self.amplification_value)
        
        # Control buttons
        amp_minus_btn = QPushButton("-")
        amp_minus_btn.setFixedSize(30, btn_height)
        amp_minus_btn.setStyleSheet("background-color: green; color: white; border: 1px solid green; border-radius: 10px;")
        amp_minus_btn.clicked.connect(lambda: self.adjust_amplification(-0.5))
        amplification_layout.addWidget(amp_minus_btn)
        
        
        amp_plus_btn = QPushButton("+")
        amp_plus_btn.setFixedSize(30, btn_height)
        amp_plus_btn.setStyleSheet("background-color: green; color: white; border: 1px solid green; border-radius: 10px;")
        amp_plus_btn.clicked.connect(lambda: self.adjust_amplification(0.5))
        amplification_layout.addWidget(amp_plus_btn)
        
        layout.addWidget(amplification_container)
    
    def setup_smoothing_controls(self, layout, btn_height):
        """
        Set up smoothing control widgets.
        
        Args:
            layout: The main layout to add components to
            btn_height: Height of the control buttons
        """
        smoothing_container = QWidget()
        smoothing_layout = QHBoxLayout(smoothing_container)
        smoothing_layout.setContentsMargins(0, 0, 0, 5)
        smoothing_container.setStyleSheet("background-color: white;")
        # Label
        smoothing_label = QLabel("Smoothing:")
        smoothing_label.setStyleSheet("color: black; font-weight: bold;")
        smoothing_layout.addWidget(smoothing_label)
        
        # Value display
        self.smoothing_value = QLabel(f"{self.mouse_controller.smoothing_factor:.2f}")
        self.smoothing_value.setStyleSheet("color: black; font-weight: bold;")
        smoothing_layout.addWidget(self.smoothing_value)
        
        # Control buttons
        smooth_minus_btn = QPushButton("-")
        smooth_minus_btn.setFixedSize(30, btn_height)
        smooth_minus_btn.setStyleSheet("background-color: green; color: white; border: 1px solid green; border-radius: 10px;")
        smooth_minus_btn.clicked.connect(lambda: self.adjust_smoothing(-0.05))
        smoothing_layout.addWidget(smooth_minus_btn)
        
        smooth_plus_btn = QPushButton("+")
        smooth_plus_btn.setFixedSize(30, btn_height)
        smooth_plus_btn.setStyleSheet("background-color: green; color: white; border: 1px solid green; border-radius: 10px;")
        smooth_plus_btn.clicked.connect(lambda: self.adjust_smoothing(0.05))
        smoothing_layout.addWidget(smooth_plus_btn)
        
        layout.addWidget(smoothing_container)
    
    def on_action_selected(self, action_name, action_func):
        """
        Handle action button selection.
        
        Args:
            action_name: Name of the selected action
            action_func: Function to execute for the action
        """
        # Uncheck all other buttons
        for btn in self.findChildren(QPushButton):
            if btn.text() != action_name:
                btn.setChecked(False)
        
        # Map button text to action name
        action_map = {
            "Click": "click",
            "Double Click": "double_click",
            "Right Click": "right_click",
            "Scroll Up": "scroll_up",
            "Scroll Down": "scroll_down"
        }
        
        # Get the corresponding action name
        selected_action = action_map.get(action_name)
        if selected_action:
            # Update the mouse controller's current action
            self.mouse_controller.set_action(selected_action)
            self.current_action = selected_action
            
            # Update status label
            self.status_label.setText(f"Selected Action: {action_name}")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: green;
                    font-weight: bold;
                    font-size: 14px;
                    margin-bottom: 5px;
                }
            """)
            # If this is a control button (not Recalibrate), perform a the action
            if action_name != "Recalibrate":
                action_func()
        else:
            if action_name == "Recalibrate":
                self.handle_recalibrate()
    
    def handle_recalibrate(self):
        """Handle the recalibration process with visual feedback and countdown. Only run once at a time."""
        if getattr(self, '_calibration_in_progress', False):
            print('[DEBUG] Calibration already in progress, skipping duplicate.')
            return
        self._calibration_in_progress = True
        self.is_calibrating_countdown = True
        self.calib_instruction_label.setVisible(True)
        self.countdown_value = 5
        self.status_label.setText(f"Calibrating in {self.countdown_value}...")
        def update_countdown():
            self.countdown_value -= 1
            if self.countdown_value > 0:
                self.status_label.setText(f"Calibrating in {self.countdown_value}...")
                QTimer.singleShot(1000, update_countdown)
            else:
                self.status_label.setText("Recalibrating...")
                self.mouse_controller.recalibrate()
                self.is_calibrating_countdown = False
                self.calib_instruction_label.setVisible(False)
                self.status_label.setText("Calibrated")
                self._calibration_in_progress = False
                QTimer.singleShot(2000, lambda: self.calib_instruction_label.setVisible(False))
        QTimer.singleShot(1000, update_countdown)
    
    def start_video(self):
        """Start the video capture and processing thread."""
        self.mouse_thread = threading.Thread(target=self.run_mouse_control)
        self.mouse_thread.daemon = True
        self.mouse_thread.start()
    
    def run_mouse_control(self):
        """
        Main video processing loop.
        Captures video frames, processes them, and updates the display.
        """
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        while self.mouse_thread and self.mouse_thread.is_alive():
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Process frame and update camera feed
            processed_frame = self.mouse_controller.process_frame(frame)
            
            # Update calibration status
            self.update_calibration_status()
            
            # Convert and display frame
            self.display_frame(processed_frame)
            
            # Small delay to prevent high CPU usage
            cv2.waitKey(1)
        
        cap.release()
    
    def update_calibration_status(self):
        """Update the calibration status label based on current state."""
        if self.is_calibrating_countdown:
            return
        if not self.mouse_controller.calibrated:
            self.status_label.setText(f"Calibrating... {self.mouse_controller.calibration_count}/8")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    font-size: 14px;
                    margin-bottom: 5px;
                }
            """)
        elif self.current_action is None:
            self.status_label.setText("Select an action (default action is click)")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: green;
                    font-weight: bold;
                    font-size: 10px;
                    margin-bottom: 2px;
                }
            """)
    
    def display_frame(self, frame):
        """
        Convert and display the processed video frame.
        
        Args:
            frame: The processed video frame to display
        """
        # Convert frame to RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        
        # Convert to QImage
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Calculate target size
        label_size = self.camera_label.size()
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale and display
        scaled_pixmap = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.camera_label.setPixmap(scaled_pixmap)
    
    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        self.is_visible = True
        # Update dashboard region when window becomes visible
        self.action_controller.update_dashboard_region(self.get_dashboard_region())
        # Initialize RAG service when dashboard is shown
        try:
            self.rag_service = RAGService(self.voice_service)
            self.rag_service.initialize()
        except Exception as e:
            print(f"[ERROR] Failed to initialize RAGService: {e}")

    def hideEvent(self, event):
        """Handle window hide event"""
        super().hideEvent(event)
        self.is_visible = False
        # Clear dashboard region when window is hidden
        self.action_controller.update_dashboard_region(None)

    def get_dashboard_region(self):
        """
        Get the current dashboard window region in real-time.
        Returns the top-left position and dimensions of the dashboard window.
        
        Returns:
            tuple: (left, top, width, height) of the dashboard window
        """
        # get the scale factor and size of current screen then scale
        # the widget to the original size because pyat6 take the scaled size 
        # of the widget and not the original size
        
        
        if self.is_visible:
            # Get current window geometry
            geometry = self.frameGeometry()
            # Get the window's position in screen coordinates
            pos = self.mapToGlobal(self.rect().topLeft())
            return (pos.x() * self.scaling_factor, pos.y() * self.scaling_factor, geometry.width() * self.scaling_factor, geometry.height() * self.scaling_factor)
        return None
    
    def adjust_amplification(self, change):
        """
        Adjust the cursor movement amplification.
        Args:
            change: Amount to change the amplification by
        """
        new_value = self.mouse_controller.amplification + change
        if 1.0 <= new_value <= 10.0:  # Limit amplification between 1.0 and 10.0
            self.mouse_controller.amplification = new_value
            self.amplification_value.setText(f"{new_value:.1f}")
            # Update user settings in DB
            if hasattr(self, 'user') and self.user is not None:
                repo = UserSettingsRepository()
                settings = repo.get_by_user_id(uuid.UUID(str(self.user.user_id)))
                if not settings:
                    from domain.entities.UserSettings import UserSettings
                    settings = UserSettings(
                        user_id=uuid.UUID(str(self.user.user_id)),
                        smoothing=self.mouse_controller.smoothing_factor,
                        amplification=new_value
                    )
                    repo.add(settings)
                else:
                    settings.amplification = new_value
                    repo.update_by_user_id(settings)
            print(f"[DEBUG] Amplification set to {new_value} and saved to DB")
    
    def adjust_smoothing(self, change):
        """
        Adjust the cursor movement smoothing factor.
        Args:
            change: Amount to change the smoothing by
        """
        new_value = self.mouse_controller.smoothing_factor + change
        if 0.1 <= new_value <= 0.95:  # Limit smoothing between 0.1 and 0.95
            self.mouse_controller.smoothing_factor = new_value
            self.smoothing_value.setText(f"{new_value:.2f}")
            # Update user settings in DB
            if hasattr(self, 'user') and self.user is not None:
                repo = UserSettingsRepository()
                settings = repo.get_by_user_id(uuid.UUID(str(self.user.user_id)))
                if not settings:
                    from domain.entities.UserSettings import UserSettings
                    settings = UserSettings(
                        user_id=uuid.UUID(str(self.user.user_id)),
                        smoothing=new_value,
                        amplification=self.mouse_controller.amplification
                    )
                    repo.add(settings)
                else:
                    settings.smoothing = new_value
                    repo.update_by_user_id(settings)
            print(f"[DEBUG] Smoothing set to {new_value} and saved to DB")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop RAG worker
        # self.rag_worker.stop()
        # Stop voice workers
        if hasattr(self, 'voice_command_worker'):
            self.voice_command_worker.stop()
        if hasattr(self, 'rag_voice_worker'):
            self.rag_voice_worker.stop()
        
        super().closeEvent(event)
    
    def start_voice_chat(self):
        self.rag_chat.add_message("I'm listening, please ask your question.", sender="computer")
        
    def start_rag_voice_chat(self):
        self.rag_chat.talk_btn.setEnabled(False)
        self.rag_chat.talk_btn.setText("Listening...")
        
        self.rag_chat.add_message("I'm listening, please ask your question.", sender="computer")
        self.rag_voice_worker = RAGVoiceWorker(self.rag_service)
        self.rag_voice_worker.user_message.connect(lambda msg: self.rag_chat.add_message(msg, sender="user"))
        self.rag_voice_worker.rag_response.connect(lambda msg: self.rag_chat.add_message(msg, sender="computer"))
        self.rag_voice_worker.speaking_started.connect(lambda: self.rag_chat.talk_btn.setText("Listening..."))
        self.rag_voice_worker.speaking_finished.connect(self.on_rag_speaking_finished)
        self.rag_voice_worker.start()

    def on_rag_speaking_finished(self):
        self.rag_chat.talk_btn.setEnabled(True)
        self.rag_chat.talk_btn.setText("🎤 Start Talking")

    def on_command_recognized(self, text):
        # Optionally show recognized command somewhere in the UI
        print(f"Voice command recognized: {text}")

    def on_command_executed(self, result):
        # Optionally show command execution result in the UI
        print(f"Voice command executed: {result}")
    