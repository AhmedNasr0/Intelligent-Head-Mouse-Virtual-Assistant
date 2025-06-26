import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from presentation.gui.main_window import MainWindow
from infrastructure.database.database import db
from infrastructure.Repository.UserRepository import UserRepository
from infrastructure.Repository.UserSettingsRepository import UserSettingsRepository
from infrastructure.Repository.FaceRepository import FaceRepository
from domain.entities.User import User
from domain.entities.UserSettings import UserSettings
from domain.entities.Face import Face
import os
from infrastructure.utils.image_utils import image_to_bytes,bytes_to_image
from pathlib import Path
import cv2
import numpy as np
import ctypes
import torch

def initialize_services():
    """Initialize all required services and repositories"""
    # Initialize repositories
    user_repository = UserRepository()
    user_settings_repository = UserSettingsRepository()
    face_repository = FaceRepository()
    return user_repository, user_settings_repository, face_repository

def test():
    try:
        # Initialize database connection
        print("Initializing database connection...")
        
        # Initialize services
        user_repository, user_settings_repository, face_repository = initialize_services()
        
        # Create Qt application
        # app = QApplication(sys.argv)
        
        # Set application style
        # app.setStyle('Fusion')
        
        # Create and show main window with services     
        # window = MainWindow(user_repository, user_settings_repository)
        # window.show()
        
        # Start application
        # exit_code = app.exec()
        
        # Close database connection when application exits
        # db.close()
        # return exit_code
        # base_dir = Path(__file__).parent.parent
        # verification_dir = base_dir / "application_data" / "verification_images"
        
        # # Initialize camera
        # cap = cv2.VideoCapture(0)  # 0 for default camera
        # if not cap.isOpened():
        #     print("Error: Could not open camera")
        #     return 1
        
        # # Get all faces from the database
        # faces = face_repository.get_all()
        # print(f"Found {len(faces)} faces in database")
        
        # # Convert face data to images and store user_id information
        # faces_data = []
        # user_faces = {}  # Dictionary to store faces grouped by user_id
        
        # for face in faces:
        #     face_image = bytes_to_image(face.face_data)
        #     faces_data.append(face_image)
            
        #     # Group faces by user_id
        #     if face.user_id not in user_faces:
        #         user_faces[face.user_id] = []
        #     user_faces[face.user_id].append(face_image)
        
        # from infrastructure.services.verify_service import FaceVerifierService
        
        # # Initialize face verifier service
        # model_path = base_dir / "src" / "infrastructure" / "models" / "deepLearningModels" / "model_aug_acc1.00_adam_binary_ct_20250325.keras"
        # verify_service = FaceVerifierService(model_path=str(model_path))
        
        # print("Starting face verification. Press 'q' to quit...")
        
        # verified_user_id = None
        # is_paused = False
        
        # while True:
        #     # Capture frame-by-frame
        #     ret, frame = cap.read()
        #     if not ret:
        #         print("Error: Could not read frame")
        #         break
            
        #     if not is_paused:
        #         # Process the frame
        #         processed_frame, is_verified = verify_service.process_frame(frame)
                
        #         if processed_frame is not None:
        #             # Check if we have a verified face
        #             if is_verified:
        #                 # Find which user this face belongs to
        #                 for user_id, user_face_images in user_faces.items():
        #                     for user_face in user_face_images:
        #                         # Resize and normalize the face for comparison
        #                         user_face = cv2.resize(user_face, (105, 105))
        #                         user_face = user_face / 255.0
                                
        #                         # Get the current face region from the frame
        #                         face_region = processed_frame[processed_frame.shape[0]-105:processed_frame.shape[0], 
        #                                                     processed_frame.shape[1]-105:processed_frame.shape[1]]
        #                         face_region = cv2.resize(face_region, (105, 105))
        #                         face_region = face_region / 255.0
                                
        #                         if verify_service.verify_face(face_region, user_face):
        #                             verified_user_id = user_id
        #                             is_paused = True
        #                             break
        #                     if verified_user_id is not None:
        #                         break
                    
        #             # Display the resulting frame
        #             cv2.imshow('Face Verification', processed_frame)
            
        #     # If we have a verified user, show welcome message
        #     if is_paused and verified_user_id is not None:
        #         # Get user information
        #         user = user_repository.get_by_id(verified_user_id)
        #         if user:
        #             # Create a black frame for the welcome message
        #             welcome_frame = np.zeros((200, 600, 3), dtype=np.uint8)
        #             welcome_text = f"Welcome {user.name}!"
        #             continue_text = "Press 'c' to continue..."
                    
        #             # Add text to the frame
        #             cv2.putText(welcome_frame, welcome_text, (50, 80), 
        #                         cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        #             cv2.putText(welcome_frame, continue_text, (50, 140), 
        #                         cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
        #             cv2.imshow('Welcome', welcome_frame)
            
        #     # Handle key presses
        #     key = cv2.waitKey(1) & 0xFF
        #     if key == ord('q'):
        #         break
        #     elif key == ord('c') and is_paused:
        #         is_paused = False
        #         verified_user_id = None
        #         cv2.destroyWindow('Welcome')
        
        # When everything done, release the capture
        # cap.release()
        # cv2.destroyAllWindows()
        # verify_service.cleanup()
        
        
        
        
        
        
        
    except Exception as e:
        print(f"Error starting application: {e}")
        if db.conn:
            db.close()
        return 1

def main():
    """Main entry point for the application"""
    try:
        # Set DPI awareness for proper scaling
        # Set to PROCESS_PER_MONITOR_DPI_AWARE to get the actual screen resolution
        # ctypes.windll.user32.SetProcessDPIAware(2)  # 2 = PROCESS_PER_MONITOR_DPI_AWARE
        
        # Print CUDA information if available
        print("CUDA Available:", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("Current Device:", torch.cuda.current_device())
            print("Device Name:", torch.cuda.get_device_name(torch.cuda.current_device()))
        
        # Initialize Qt application
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Get screen information
        # print(f"screen size before scaling : {QApplication.primaryScreen().size().width()} x {QApplication.primaryScreen().size().height()}")
        screen = QApplication.primaryScreen()
        scale_factor = screen.devicePixelRatio()
        print(f"Screen Scale Factor: {scale_factor}")
        
        # widget_width = QApplication.primaryScreen().size().width()
        # widget_height = QApplication.primaryScreen().size().height()
        # original_width = widget_width * scale_factor
        # original_height = widget_height * scale_factor
        # print(f"Original Size: {original_width} x {original_height}")
        # QApplication.primaryScreen()(0, 0, original_width, original_height)
        # Initialize services
        user_repository, user_settings_repository, face_repository = initialize_services()
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start application event loop
        exit_code = app.exec()
        
        # Clean up database connection
        db.close()
        
        return exit_code
        
    except Exception as e:
        print(f"Error starting application: {e}")
        if db.conn:
            db.close()
        return 1

if __name__ == "__main__":
    sys.exit(main())
