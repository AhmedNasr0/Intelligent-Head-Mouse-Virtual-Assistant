import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Optional
from abc import ABC, abstractmethod

class FaceVerificationService(ABC):
    
    @abstractmethod
    def verify_face(self, image: np.ndarray) -> bool:
        """Verify if the face in the image is a match for the user's face"""
        pass

