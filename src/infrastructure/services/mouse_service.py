import cv2
import mediapipe as mp
import numpy as np
import math
import time
from collections import deque
import threading
from infrastructure.services.actions import ActionController
import ctypes

class HeadControlledCursor:
    """
    Main controller for head-controlled cursor movement and actions.
    Uses MediaPipe face mesh to track head movements and control cursor position.
    """
    
    def __init__(self, smoothing_factor=0.9, amplification=6.5, dashboard_window=None):
        """
        Initialize the head-controlled cursor system.
        
        Args:
            smoothing_factor: Factor for cursor movement smoothing (0-1)
            amplification: Factor for amplifying head movements
            dashboard_window: Reference to the dashboard window
        """
        # Disable pyautogui failsafe for smoother operation
        
        # Initialize MediaPipe face detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            refine_landmarks=True
        )
        
        # Store dashboard window reference
        self.dashboard_window = dashboard_window
        
        # Initialize drawing utilities
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = mp.solutions.drawing_styles.get_default_face_mesh_contours_style()
        
        # Initialize action controller
        self.action_controller = ActionController()
        
        # Get screen dimensions
        self.screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        self.screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        
        # Movement settings
        self.smoothing_factor = smoothing_factor
        self.amplification = amplification
        
        # Position tracking
        self.prev_x, self.prev_y = self.screen_width // 2, self.screen_height // 2
        self.position_history_size = 500
        self.position_history_x = deque(maxlen=self.position_history_size)
        self.position_history_y = deque(maxlen=self.position_history_size)
        
        # Calibration state
        self.calibrated = False
        self.calibration_points = []
        self.calibration_count = 0
        self.reference_point = None
        self.baseline_mouth_width = None
        
        # Landmark indices
        self.TIP_INDEX = 6
        
        # Dead zone settings
        self.dead_zone = 0.010
        self.position_dead_zone = 30
        
        # Cursor thread
        self.cursor_x, self.cursor_y = self.screen_width // 2, self.screen_height // 2
        self.cursor_thread_active = False
        self.cursor_thread = None
        
        # Action settings
        self.current_action = "click"
        self.action_mapping = {
            "click": self.action_controller.click,
            "double_click": self.action_controller.double_click,
            "right_click": self.action_controller.right_click,
            "scroll_up": self.action_controller.scroll_up,
            "scroll_down": self.action_controller.scroll_down
        }
        
        # Drag and drop state
        self.is_dragging = False
        self.drag_start_pos = None
        self.selected_item = None
        self.current_mode = None
        
        # Smile detection
        self.smile_start_time = None
        self.smile_duration_threshold = 1.5
        self.last_smile_time = None
        self.last_click_time = 0
        self.click_cooldown = 0.5
        
        # Mouth open detection for drag and drop
        self.mouth_open_start_time = None
        self.is_mouth_open = False
        self.mouth_open_threshold = 0.2  # You may need to tune this
        self.mouth_open_duration = 2.0
        
        # Time tracking for debug prints
        self.time = time.time()
        self.t = time.time()  # Add this line for cursor position debug prints
        
        # Debug mode
        self.debug_mode = True
        
        print("Head Controlled Cursor initialized")
        print(f"Screen: {self.screen_width}x{self.screen_height}, Amplification: {self.amplification}x")
        print(f"Smoothing: {self.smoothing_factor}")
    
    def calibrate(self, landmarks):
        """
        Perform calibration to set neutral position.
        Collects 8 points and calculates average position as reference.
        
        Args:
            landmarks: MediaPipe face landmarks
            
        Returns:
            bool: True if calibration is complete
        """
        # Get nose position
        landmark = landmarks.landmark[self.TIP_INDEX]
        point = (landmark.x, landmark.y, landmark.z)
        
        # Get mouth width
        left_mouth = landmarks.landmark[61]
        right_mouth = landmarks.landmark[291]
        mouth_width = abs(right_mouth.x - left_mouth.x)
        
        # Get face width
        left_cheek = landmarks.landmark[234]
        right_cheek = landmarks.landmark[454]
        face_width = abs(right_cheek.x - left_cheek.x)
        
        # Calculate mouth-to-face ratio
        mouth_to_face_ratio = mouth_width / face_width
        
        self.calibration_points.append((point, mouth_to_face_ratio))    
        self.calibration_count += 1
        
        if self.calibration_count >= 8:
            # Calculate average position
            x_sum = sum([p[0][0] for p in self.calibration_points])
            y_sum = sum([p[0][1] for p in self.calibration_points])
            z_sum = sum([p[0][2] for p in self.calibration_points])
            count = len(self.calibration_points)
            
            # Calculate average mouth-to-face ratio
            mouth_ratio_sum = sum([p[1] for p in self.calibration_points])
            self.baseline_mouth_ratio = mouth_ratio_sum / count
            
            self.reference_point = (x_sum / count, y_sum / count, z_sum / count)
            self.calibrated = True
            print("Calibration complete!")
            print(f"Baseline mouth width: {self.baseline_mouth_ratio:.3f}")
            
            # Initialize position history
            center_x, center_y = self.screen_width // 2, self.screen_height // 2
            for _ in range(self.position_history_size):
                self.position_history_x.append(center_x)
                self.position_history_y.append(center_y)
                
            # Start cursor thread
            if not self.cursor_thread_active:
                self.cursor_thread_active = True
                self.cursor_thread = threading.Thread(target=self.cursor_update_thread)
                self.cursor_thread.daemon = True
                self.cursor_thread.start()
            
        return self.calibrated
    
    def apply_smoothing(self, new_x, new_y):
        """
        Apply smoothing to cursor position using exponential smoothing and weighted moving average.
        
        Args:
            new_x: New x position
            new_y: New y position
            
        Returns:
            tuple: Smoothed (x, y) position
        """
        # Add to history buffer
        self.position_history_x.append(new_x)
        self.position_history_y.append(new_y)
        
        # Apply exponential smoothing
        smooth_x = new_x * (1 - self.smoothing_factor) + self.prev_x * self.smoothing_factor
        smooth_y = new_y * (1 - self.smoothing_factor) + self.prev_y * self.smoothing_factor
        
        # Apply weighted moving average if we have enough history
        smooth_percentage = 0.6
        weighted_percentage = 0.4
        if len(self.position_history_x) >= 5:
            weights = [0.05, 0.1, 0.15, 0.2, 0.5]
            recent_x = list(self.position_history_x)[-5:]
            recent_y = list(self.position_history_y)[-5:]
            
            weighted_x = sum(x * w for x, w in zip(recent_x, weights))
            weighted_y = sum(y * w for y, w in zip(recent_y, weights))
            
            final_x = smooth_x * smooth_percentage + weighted_x * weighted_percentage
            final_y = smooth_y * smooth_percentage + weighted_y * weighted_percentage
            
            self.prev_x, self.prev_y = final_x, final_y
            return int(final_x), int(final_y)
        
        self.prev_x, self.prev_y = smooth_x, smooth_y
        return int(smooth_x), int(smooth_y)
    
    def cursor_update_thread(self):
        """Thread for smooth cursor position updates."""
        while self.cursor_thread_active:
            try:
                current_x, current_y = self.cursor_x, self.cursor_y
                self.action_controller.set_cursor_position(current_x, current_y)
                time.sleep(1/120)  # 120 Hz update rate
            except Exception as e:
                if self.debug_mode:
                    print(f"Cursor update error: {str(e)}")
                time.sleep(0.1)
    
    def calculate_mouth_aspect_ratio(self, landmarks):
        """
        Calculate the mouth aspect ratio (MAR).
        
        Args:
            landmarks: MediaPipe face landmarks
            
        Returns:
            float: Mouth aspect ratio
        """
        top_lip = landmarks.landmark[13]
        bottom_lip = landmarks.landmark[14]
        left_mouth = landmarks.landmark[61]
        right_mouth = landmarks.landmark[291]

        mouth_width = abs(right_mouth.x - left_mouth.x)
        mouth_height = abs(top_lip.y - bottom_lip.y)

        if mouth_width == 0:
            return 0

        mar = mouth_height / mouth_width
        return mar

    def detect_smile(self, landmarks):
        """
        Detect if the person is smiling based on mouth shape.
        
        Args:
            landmarks: MediaPipe face landmarks
            
        Returns:
            bool: True if smiling is detected
        """
        # Get mouth points
        left_mouth = landmarks.landmark[61]
        right_mouth = landmarks.landmark[291]
        top_lip = landmarks.landmark[13]
        bottom_lip = landmarks.landmark[14]
        
        # Get face points for width calculation
        left_cheek = landmarks.landmark[234]
        right_cheek = landmarks.landmark[454]
        
        # Calculate current mouth width and face width
        current_mouth_width = abs(right_mouth.x - left_mouth.x)
        current_face_width = abs(right_cheek.x - left_cheek.x)
        
        # Calculate mouth height
        mouth_height = abs(top_lip.y - bottom_lip.y)
        
        # Calculate mouth-to-face ratio
        mouth_to_face_ratio = current_mouth_width / current_face_width
        
        # Calculate mouth aspect ratio (MAR)
        mar = mouth_height / current_mouth_width if current_mouth_width > 0 else 0
        
        # Calculate head tilt using nose points
        nose_tip = landmarks.landmark[1]
        nose_bridge = landmarks.landmark[6]
        head_tilt = abs(nose_tip.y - nose_bridge.y)
        
        # Adjust thresholds based on head tilt
        tilt_factor = 1.0 + (head_tilt * 1.5)
        
        # Smile detection criteria
        is_wider_smile = mouth_to_face_ratio > (self.baseline_mouth_ratio * 1.05 * tilt_factor)
        is_mouth_shape_ok = mar < (0.45 * tilt_factor)
        mouth_corners_movement = abs(left_mouth.y - right_mouth.y)
        is_mouth_aligned = mouth_corners_movement < 0.08
        
        return is_wider_smile and is_mouth_shape_ok and is_mouth_aligned

    def is_in_control_region(self):
        """
        Check if cursor is in either dashboard or taskbar region.
        
        Returns:
            bool: True if cursor is in any control region
        """
        # Check taskbar first
        in_taskbar = self.action_controller.is_in_taskbar(self.cursor_x, self.cursor_y)
        if in_taskbar:
            return True

        # Get current dashboard region
        if self.dashboard_window:
            dashboard_region = self.dashboard_window.get_dashboard_region()
            if dashboard_region:
                left, top, width, height = dashboard_region
                
                # Check if cursor is within dashboard bounds using screen coordinates
                is_in_dashboard = (left <= self.cursor_x <= left + width and 
                                 top <= self.cursor_y <= top + height)
                
                # Only print if cursor is actually in dashboard
                current_time = time.time()
                # if is_in_dashboard and self.debug_mode and current_time - self.t > 1:
                #     print(f"\nDashboard Click Detected:")
                #     print(f"Screen Dimensions: {self.screen_width}x{self.screen_height}")
                #     print(f"Dashboard Region: Left={left}, Top={top}, Width={width}, Height={height}")
                #     print(f"Cursor Position: X={self.cursor_x}, Y={self.cursor_y}")
                #     print(f"Is in dashboard: {is_in_dashboard}\n")
                #     self.t = current_time
                return is_in_dashboard
        
        return False

    def process_frame(self, frame):
        """
        Process a video frame to update cursor position and handle actions.
        
        Args:
            frame: Video frame to process
            
        Returns:
            numpy.ndarray: Processed frame with debug information
        """
        # Flip frame horizontally
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Draw landmarks in debug mode
            if self.debug_mode:
                self.mp_drawing.draw_landmarks(
                    frame,
                    face_landmarks,
                    self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.drawing_spec
                )
            
            # Calibrate if needed
            if not self.calibrated:
                is_calibrated = self.calibrate(face_landmarks)
                if self.debug_mode:
                    cv2.putText(frame, f"Calibrating... {self.calibration_count}/8", 
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                return frame
            
            # Get nose position
            landmark = face_landmarks.landmark[self.TIP_INDEX]
            current_point = (landmark.x, landmark.y, landmark.z)
            
            # Draw nose tip point in debug mode
            if self.debug_mode:
                height, width = frame.shape[:2]
                nose_x = int(landmark.x * width)
                nose_y = int(landmark.y * height)
                cv2.circle(frame, (nose_x, nose_y), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"Tip ({self.TIP_INDEX})", (nose_x + 10, nose_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Detect gestures
            self.is_smiling = self.detect_smile(face_landmarks)
            mar = self.calculate_mouth_aspect_ratio(face_landmarks)
            self.is_mouth_open = mar > self.mouth_open_threshold

            # Check if cursor is in control regions
            in_control_region = self.is_in_control_region()
            current_time = time.time()
            
            # --- Drag and Drop: Mouth Open/Close ---
            if self.is_mouth_open:
                if not self.mouth_open_start_time:
                    self.mouth_open_start_time = current_time
                if not self.is_dragging and (current_time - self.mouth_open_start_time) >= self.mouth_open_duration:
                    self.is_dragging = True
                    self.drag_start_pos = (self.cursor_x, self.cursor_y)
                    self.action_controller.mouse_down()
                    if self.debug_mode:
                        print(f"Started dragging after {self.mouth_open_duration} seconds of mouth open")
            else:
                if self.is_dragging:
                    self.is_dragging = False
                    self.action_controller.mouse_up()
                    self.drag_start_pos = None
                    if self.debug_mode:
                        print("Stopped dragging due to mouth closing")
                self.mouth_open_start_time = None

            # --- Smile Actions: Click, etc (unchanged) ---
            if self.is_smiling:
                if not self.smile_start_time:
                    self.smile_start_time = current_time
                    self.last_smile_time = current_time
                # If not dragging, perform the selected action
                if not self.is_dragging and (current_time - self.last_click_time) >= self.click_cooldown:
                    try:
                        if in_control_region:
                            if self.debug_mode:
                                self.action_controller.click()
                        else:
                            action_func = self.action_mapping.get(self.current_action)
                            action_func()
                    except Exception as e:
                        if self.debug_mode:
                            print(f"Error executing action {self.current_action}: {str(e)}")
                    self.last_click_time = current_time
                self.last_smile_time = current_time
            else:
                self.smile_start_time = None
                self.last_smile_time = None
            
            # Calculate cursor position
            x_offset = (current_point[0] - self.reference_point[0]) * self.amplification
            y_offset = (current_point[1] - self.reference_point[1]) * self.amplification
            
            # Apply dead zone to movement
            if abs(x_offset) < self.dead_zone:
                x_offset = 0
            if abs(y_offset) < self.dead_zone:
                y_offset = 0
            
            # Map to screen coordinates
            cursor_x = int(self.screen_width * (0.5 + x_offset))
            cursor_y = int(self.screen_height * (0.5 + y_offset))
            
            # Ensure cursor stays within screen bounds
            cursor_x = max(0, min(cursor_x, self.screen_width - 1))
            cursor_y = max(0, min(cursor_y, self.screen_height - 1))
            
            # Apply position dead zone
            if abs(cursor_x - self.prev_x) < self.position_dead_zone:
                cursor_x = self.prev_x
            if abs(cursor_y - self.prev_y) < self.position_dead_zone:
                cursor_y = self.prev_y
            
            # Apply smoothing
            smooth_x, smooth_y = self.apply_smoothing(cursor_x, cursor_y)
            
            # Update cursor position
            self.cursor_x, self.cursor_y = smooth_x, smooth_y
            
            # Draw debug info
            if self.debug_mode:
                cv2.putText(frame, f"Cursor: ({smooth_x}, {smooth_y})", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                if in_control_region:
                    cv2.putText(frame, "In Control Region", 
                                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame
    
    def start(self):
        """Start the head control system."""
        if not self.cursor_thread_active:
            self.cursor_thread_active = True
            self.cursor_thread = threading.Thread(target=self.cursor_update_thread)
            self.cursor_thread.daemon = True
            self.cursor_thread.start()
    
    def stop(self):
        """Stop the head control system."""
        self.cursor_thread_active = False
        if self.cursor_thread:
            self.cursor_thread.join()
            self.cursor_thread = None

    def recalibrate(self):
        """Reset calibration and start new calibration process."""
        self.calibrated = False
        self.calibration_points = []
        self.calibration_count = 0
        self.reference_point = None
        self.baseline_mouth_width = None
    
    def set_action(self, action_name):
        """
        Set the current action based on button selection.
        
        Args:
            action_name: Name of the action to set  
        """
        if action_name in self.action_mapping:
            self.current_action = action_name
        else:
            if self.debug_mode:
                print(f"Warning: Attempted to set invalid action: {action_name}")
    
    def get_action(self):
        """
        Get the current action.
        
        Returns:
            str: Current action name
        """
        return self.current_action
    
    def handle_drag(self):
        """No-op: Drag is now handled by mouth open/close in process_frame."""
        pass

if __name__ == "__main__":
    controller = HeadControlledCursor(
        smoothing_factor=0.9,
        amplification=5.0
    )
    controller.start()