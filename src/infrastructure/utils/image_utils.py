import numpy as np
import cv2

def image_to_bytes(image_path: str) -> bytes:
    """Read image from file path and convert it to bytes"""
    with open(image_path, 'rb') as f:
        return f.read()

def frame_to_bytes(frame: np.ndarray) -> bytes:
    """Convert numpy array image frame to bytes"""
    # Encode the frame as JPEG
    success, encoded_image = cv2.imencode('.jpg', frame)
    if not success:
        raise ValueError("Failed to encode image frame")
    return encoded_image.tobytes()

def bytes_to_image(image_bytes: bytes) -> np.ndarray:
    """Convert image bytes to an OpenCV image (numpy array)"""
    try:
        # First try to decode as a regular image
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        # If decoding failed, try to handle it as a raw array
        if image is None:
            # Assuming the bytes are a raw array of shape (height, width, 3)
            # We need to know the dimensions to reshape properly
            # For now, we'll try to infer a square image
            size = int(np.sqrt(len(image_bytes) // 3))
            if size * size * 3 == len(image_bytes):
                image = np.frombuffer(image_bytes, dtype=np.uint8).reshape(size, size, 3)
            else:
                raise ValueError("Could not decode image bytes")
        
        return image
    except Exception as e:
        print(f"Error converting bytes to image: {str(e)}")
        raise
