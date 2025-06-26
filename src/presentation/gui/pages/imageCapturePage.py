from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import os
import cv2
import mediapipe as mp
from PyQt6.QtCore import pyqtSignal
from infrastructure.utils.image_utils import frame_to_bytes

class ImageCapturePage(QWidget):
    # Signal to emit when an image is confirmed
    image_confirmed = pyqtSignal(bytes)  # Emits the face image data
    computer_speech = pyqtSignal(str)   # Signal to update computer voice message

    def __init__(self, stream):
        super().__init__()
        self.stream = stream
        self.images_captured = 0
        self.total_images = 2
        
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 0 for short range, 1 for long range
            min_detection_confidence=0.5
        )
        
        self.setup_ui()
        self.setup_timers()
        self.computer_speech.connect(self.update_computer_speech)

    def process_face(self, frame):
        try:
            frame = cv2.flip(frame, 1)
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = self.face_detection.process(rgb_frame)
            
            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    
                    padding_x = int(bbox.width * iw * 0.2)
                    padding_y = int(bbox.height * ih * 0.2)
                    
                    x = int(bbox.xmin * iw) - padding_x
                    y = int(bbox.ymin * ih) - padding_y
                    w = int(bbox.width * iw) + (2 * padding_x)
                    h = int(bbox.height * ih) + (2 * padding_y)
                
                    # Ensure coordinates are within frame
                    x, y = max(0, x), max(0, y)
                    w = min(w, iw - x)
                    h = min(h, ih - y)
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Extract face region
                    face_region = frame[y:y+h, x:x+w]
                    if face_region.size == 0:
                        return frame, None
                    
                    # Resize face region to model input size (105x105)
                    face_region = cv2.resize(face_region, (105, 105))
                    
                    return frame, face_region
                    
            return frame, None
            
        except Exception as e:
            print(f"Error processing face: {e}")
            return frame, None

    def setup_ui(self):
        self.setMinimumSize(800, 600)  # Ensure a reasonable minimum size
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Camera view (top, 40% height)
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.camera_label, 4)

        # Captured images (middle, 40% height)
        self.captured_images_widget = QWidget()
        self.captured_images_layout = QHBoxLayout()
        self.captured_images_layout.setContentsMargins(0, 0, 0, 0)
        self.captured_images_layout.setSpacing(10)
        self.captured_images_widget.setLayout(self.captured_images_layout)
        main_layout.addWidget(self.captured_images_widget, 4)

        # Texts (bottom, 20% height)
        text_layout = QVBoxLayout()
        self.timer_label = QLabel("Ready to capture")
        self.timer_label.setStyleSheet("font-size: 24px; color: #2c3e50;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_layout.addWidget(self.timer_label)
        main_layout.addLayout(text_layout, 2)

        self.setLayout(main_layout)

    def resizeEvent(self, event):
        # Dynamically resize camera and images
        w = self.width()
        h = self.height()
        cam_h = int(h * 0.4)
        img_h = int(h * 0.4)
        self.camera_label.setFixedSize(w, cam_h)
        for i in range(self.captured_images_layout.count()):
            item = self.captured_images_layout.itemAt(i)
            if item and item.widget():
                item.widget().setFixedSize(w // max(1, self.captured_images_layout.count()), img_h)
        self.captured_images_widget.setFixedSize(w, img_h)
        super().resizeEvent(event)

    def setup_timers(self):
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera_view)
        self.camera_timer.start(10)

    def start_image_capture(self):
        self.timer_label.setText("Taking photo")
        self.timer_label.setStyleSheet("font-size: 24px; color: #27ae60;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.capture_image()

    def update_computer_speech(self, text):
        self.timer_label.setText(text)
        self.timer_label.setStyleSheet("font-size: 24px; color: #2c3e50;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def add_captured_image(self, face_region):
        rgb_image = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Set size dynamically in resizeEvent
        self.captured_images_layout.addWidget(label)
        self.resizeEvent(None)

    def capture_image(self):
        frame = self.stream.read()
        if frame is not None:
            display_frame, face_region = self.process_face(frame)
            if face_region is not None:
                try:
                    face_data = frame_to_bytes(face_region)
                    self.image_confirmed.emit(face_data)
                    self.add_captured_image(display_frame)
                    self.images_captured += 1
                    self.timer_label.setText("Photo captured successfully!\nSay save it to keep it or try again to retry.")
                    self.timer_label.setStyleSheet("font-size: 24px; color: #27ae60;")
                    if self.images_captured < self.total_images:
                        pass  # No button, so do nothing
                    else:
                        self.timer_label.setText("All Photos Captured")
                except Exception as e:
                    self.timer_label.setText("Error saving photo!")
                    self.timer_label.setStyleSheet("font-size: 24px; color: #e74c3c;")
                    print(f"Error saving face: {e}")
            else:
                self.timer_label.setText("No face detected! Try again.")
                self.timer_label.setStyleSheet("font-size: 24px; color: #e74c3c;")

    def update_camera_view(self):
        if self.stream:
            frame = self.stream.read()
            if frame is not None:
                # Process frame to show face detection
                display_frame, _ = self.process_face(frame)
                
                # Convert to Qt format and display
                rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                    self.camera_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.camera_label.setPixmap(scaled_pixmap)

    def clear_last_captured_image(self):
        # Remove the last image widget from the layout
        count = self.captured_images_layout.count()
        if count > 0:
            item = self.captured_images_layout.takeAt(count - 1)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            self.images_captured = max(0, self.images_captured - 1)
        # Optionally reset timer label
        self.timer_label.setText("Ready to capture. Say 'take it' when ready.")
        self.timer_label.setStyleSheet("font-size: 24px; color: #2c3e50;")