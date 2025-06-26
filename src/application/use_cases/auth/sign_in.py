from dataclasses import dataclass
from ...services.face_verification_service import FaceVerificationService
import numpy as np
from ..user_management.user_usecase import UserUseCase

class SignInUseCase:
    def __init__(self, face_verification_service: FaceVerificationService, user_usecase: UserUseCase):
        self.face_verification_service = face_verification_service
        self.user_usecase = user_usecase
    
    def sign_in_with_face(self, image: np.ndarray, email: str) -> bool:
        """Sign in with a face image"""
        try:
            # Verify face
            is_verified = self.face_verification_service.verify_face(image)
            if not is_verified:
                return False
            
            # Get user
            user = self.user_usecase.get_user_by_email(email)
            
            if not user:
                return False
            
            # Verify face against reference faces
            result = self.face_verifier.verify(command.face_image, user.faces)
            
            return result.is_verified
        except Exception as e:
            print(f"Sign in failed: {e}")
            return False 