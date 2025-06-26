import cv2
import os
import uuid
import numpy as np
import tensorflow as tf
import mediapipe as mp

# Define base directory and create it if it doesn't exist
BASE_DIR = os.path.join(os.getcwd(), 'Data')
PROCESSED_DIR = os.path.join(BASE_DIR, 'LFW', "Ahmed_Nasr")

def collect_positive_anchor():
    print("\nStarting face collection...")
    
    # Create directory if it doesn't exist
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # Initialize MediaPipe Face Mesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    mp_drawing = mp.solutions.drawing_utils
    drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("\nInstructions:")
    print("- Press 'c': Capture and save image with augmentations")
    print("- Press 'q': Quit")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        # Flip the frame horizontally
        frame = cv2.flip(frame, 1)

        # Convert the image to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame and detect faces
        results = face_mesh.process(rgb_frame)
        
        # Store current face ROI
        current_face_roi = None
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                
                # Get face bounding box
                face_points = []
                for landmark in face_landmarks.landmark:
                    h, w, _ = frame.shape
                    x, y = int(landmark.x * w), int(landmark.y * h)
                    face_points.append([x, y])
                
                face_points = np.array(face_points)
                x, y, w, h = cv2.boundingRect(face_points)

                # Extract face ROI with margin
                margin = 50
                roi_x = max(0, x - margin)
                roi_y = max(0, y - margin)
                roi_w = min(frame.shape[1] - roi_x, w + 2 * margin)
                roi_h = min(frame.shape[0] - roi_y, h + 2 * margin)
                
                face_roi = frame[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]
                
                if face_roi.size > 0:  # Check if ROI is valid
                    # Resize face ROI to 250x250 pixels
                    current_face_roi = cv2.resize(face_roi, (250, 250))
                    
                    # Draw face landmarks on the frame
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=drawing_spec,
                        connection_drawing_spec=drawing_spec
                    )

        # Show the frame
        cv2.imshow("Image", frame)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('c') and current_face_roi is not None:
            # Generate unique filename
            unique_filename = str(uuid.uuid1())
            
            # Save the original image first
            original_path = os.path.join(PROCESSED_DIR, f"{unique_filename}_original.jpg")
            cv2.imwrite(original_path, current_face_roi)
            print(f"✅ Saved original image!")
            
            
        elif key == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()
    print("\nImage collection completed!")

if __name__ == "__main__":
    print("Starting data collection process...")
    collect_positive_anchor()