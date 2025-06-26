import os
import cv2
from threading import Thread
import numpy as np
import tensorflow as tf
import mediapipe as mp
from infrastructure.services.ml.deeplearning.utils import CustomWeightInitializer, CustomBiasInitializer
from infrastructure.services.ml.deeplearning.data_preprocessing import preprocess
from infrastructure.services.ml.deeplearning.distance_layers import L1Dist
import time

def verify_single_image(model, input_img, validation_img, detection_threshold=0.8) -> bool:
    """Verify a single pair of images"""
    # Make Predictions for the input image and the validation image
    result = model.predict([
        np.expand_dims(input_img, axis=0),
        np.expand_dims(validation_img, axis=0)
    ])
    similarity_score = result[0][0]
    return similarity_score > detection_threshold

def verify_multiple_images(model, input_img, validation_imgs):
    """Verify multiple pairs of images"""
    results = []
    for i, validation_img in enumerate(validation_imgs):
        verification_result = verify_single_image(model, input_img, validation_img)
        results.append(verification_result)
    
    # Calculate percentage of True results
    true_percentage = sum(results) / len(results)
    return true_percentage > 0.8  # Return True if more than 50% matches


class FaceVerifierService:
    def __init__(self, model_path):
        self.model_path = model_path
        self._load_model(model_path)
        self.init_media_pipe()
        self.last_verification_time = 0
        self.verification_cooldown = 1.0  # seconds between verifications
        self.verification_status = None
        self.last_capture_time = 0
        self.capture_cooldown = 1.0  # seconds between captures
        self.verification_counter = 0
        self.is_paused = False
        self.last_frame = None
        self._create_directory()
        

    def _load_model(self, model_path):
        custom_objects = {
            'CustomWeightInitializer': CustomWeightInitializer,
            'CustomBiasInitializer': CustomBiasInitializer,
            'L1Dist': L1Dist
        }
        self.model = tf.keras.saving.load_model(model_path, custom_objects=custom_objects)

    def init_media_pipe(self):
        """Initialize MediaPipe face detection"""
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1,  # 0 for short-range, 1 for long-range
            min_detection_confidence=0.7
        )

    
    def verify_face(self, incoming_frame , reference_frame) -> bool:
        """Face verification"""
        if incoming_frame is None:
            return False
        if reference_frame is None:
            return False
        return verify_single_image(self.model, incoming_frame, reference_frame)
    
    
    def process_frame(self, frame):
        """Process a single frame for face detection and verification
        Returns:
            tuple: A tuple containing the processed frame and the face region
        """
        if frame is None:
            return None, None

        try:
            # Flip frame horizontally for selfie view
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame with MediaPipe
            results = self.face_detection.process(rgb_frame)
            
            current_time = time.time()
            
            # If faces are detected
            if results.detections:
                for detection in results.detections:
                    # Get bounding box
                    bbox = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    
                    # Add padding to make the box larger (20% padding)
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
                    
                    # Draw rectangle around face
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Extract and preprocess face region
                    face_region = frame[y:y+h, x:x+w]
                    if face_region.size == 0:
                        continue
                                        
                    
                    # Resize face region to model input size
                    face_region = cv2.resize(face_region, (105, 105))
                    face_region = face_region / 255.0  # Normalize
                    
                    
                    # Display verification status
                    status_color = (0, 255, 0) if self.verification_status else (0, 0, 255)
                    status_text = "VERIFIED" if self.verification_status else "NOT VERIFIED"
                    cv2.putText(frame, status_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2)
            
            # Store the last frame
            self.last_frame = frame.copy()
            return frame , face_region
            
        except Exception as e:
            print(f"❌ Error processing frame: {e}")
            return None, None

    def _create_directory(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(os.path.join('application_data', 'input_image'), exist_ok=True)
        os.makedirs(os.path.join('application_data', 'verification_images'), exist_ok=True)

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'face_detection'):
            self.face_detection.close()
    
    def send_verification_status(self, verification_result):
        """Send verification status to the main thread"""
        self.verification_status = verification_result

