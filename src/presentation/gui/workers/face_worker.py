from PyQt6.QtCore import QThread, pyqtSignal
import time
from infrastructure.services.verify_service import FaceVerifierService
from infrastructure.Repository.FaceRepository import FaceRepository
from infrastructure.Repository.UserRepository import UserRepository
from infrastructure.utils.image_utils import bytes_to_image
import cv2
import numpy as np


class FaceWorker(QThread):
    # Signals for communication with the main thread
    frame_ready = pyqtSignal(object)  # Emits processed frame
    verification_complete = pyqtSignal(bool, str)  # Changed to str for UUID
    error_occurred = pyqtSignal(str)  # Emits error messages

    def __init__(self, model_path):
        super().__init__()
        self.model_path = model_path
        self.face_verifier = None
        self.is_running = True
        self.current_frame = None
        self.last_verification_time = 0
        self.verification_cooldown = 1.0  # seconds between verifications
        self.face_repository = FaceRepository()
        self.user_repository = UserRepository()
        self.faces_data = []
        self.user_faces = {}  # Dictionary to store faces grouped by user_id
        self.verified_user_id = None
        self.is_paused = False
        self.verification_thread = None
        self.face_region = None

    def run(self):
        """Main thread loop"""
        try:
            print("[DEBUG] Initializing FaceWorker...")
            self.face_verifier = FaceVerifierService(self.model_path)
            self.get_all_faces_grouped_by_user_id()

            while self.is_running:
                if self.current_frame is not None and not self.is_paused:
                    # Process frame and get face region
                    processed_frame, face_region = self.face_verifier.process_frame(self.current_frame)
                    
                    # Emit the processed frame for display
                    self.frame_ready.emit(processed_frame)
                    
                    if processed_frame is not None and face_region is not None:
                        # Start verification in a separate thread if not already running
                        if self.verification_thread is None or not self.verification_thread.isRunning():
                            self.face_region = face_region
                            self.verification_thread = VerificationThread(self)
                            self.verification_thread.verification_complete.connect(self.handle_verification_complete)
                            self.verification_thread.start()
                            

                # Small delay to prevent CPU overuse
                time.sleep(0.01)
                
        except Exception as e:
            print(f"[ERROR] Error in face worker: {str(e)}")
            self.error_occurred.emit(f"Error in face worker: {str(e)}")
        finally:
            if self.face_verifier:
                print("[DEBUG] Cleaning up face verifier...")
                self.face_verifier.cleanup()

    def update_frame(self, frame):
        """Update the current frame to be processed"""
        self.current_frame = frame
        
    def handle_verification_complete(self, is_verified, user_id):
        """Handle the verification complete signal"""
        if is_verified:
            self.verified_user_id = user_id
            self.is_paused = True
            self.verification_complete.emit(True, str(user_id))  # Ensure user_id is string

    def stop(self):
        """Stop the worker thread"""
        print("[DEBUG] Stopping FaceWorker...")
        self.is_running = False

        if self.verification_thread:
            self.verification_thread.stop()
            self.verification_thread.wait()
            print("[DEBUG] Verification thread stopped")
            if self.verification_thread.isRunning():
                self.verification_thread.quit()
                self.verification_thread.wait()
                print("[DEBUG] Verification thread quit")
            self.verification_thread = None 
        self.isRunning = False
        self.requestInterruption()
        self.wait()
    
    def get_all_faces_grouped_by_user_id(self):
        """Get all faces grouped by user_id"""
        # Get all faces from the database
        faces = self.face_repository.get_all()
        
        # Convert face data to images and store user_id information
        for face in faces:
            face_image = bytes_to_image(face.face_data)
            self.faces_data.append(face_image)
            
            # Group faces by user_id
            if face.user_id not in self.user_faces:
                self.user_faces[face.user_id] = []
            self.user_faces[face.user_id].append(face_image)
        
        # Print summary of loaded faces
        for user_id, faces in self.user_faces.items():
            print(f"[DEBUG] User {user_id} has {len(faces)} faces")


class VerificationThread(QThread):
    verification_complete = pyqtSignal(bool, str)  # Changed to str for UUID
    
    def __init__(self, face_worker):
        super().__init__()
        self.face_worker = face_worker

    def run(self):
        """Run the verification process in a separate thread"""
        try:
            # print("[DEBUG] Starting verification process in separate thread...")
            
            # Check all faces for all users
            for user_id, user_face_images in self.face_worker.user_faces.items():
                if len(user_face_images) >= 2:  # Only check users with 2 or more faces
                    match_count = 0
                    for i, user_face in enumerate(user_face_images):
                        # Resize and normalize the face for comparison
                        user_face = cv2.resize(user_face, (105, 105))
                        user_face = user_face / 255.0
                        
                        # Verify face using the service
                        verification_result = self.face_worker.face_verifier.verify_face(
                            self.face_worker.face_region, user_face)
                        
                        if verification_result:
                            match_count += 1
                            print(f"[DEBUG] Match found for user {user_id} - face {i+1}/{len(user_face_images)}")
                            
                            # If we have at least 2 matches for this user, verify immediately
                            if match_count >= 2:
                                self.verification_complete.emit(True, str(user_id))  # Ensure user_id is string
                                return  # Exit the loop as we found our match
            
            self.verification_complete.emit(False, "")
            
        except Exception as e:
            print(f"[ERROR] Error in verification thread: {str(e)}")
            self.face_worker.error_occurred.emit(f"Error in verification thread: {str(e)}")
    
    def stop(self):
        print("[DEBUG] Stopping VerificationThread...")
        self._running = False
        self.requestInterruption()
        self.wait()
        print("[DEBUG] in class VerificationThread stopped")

