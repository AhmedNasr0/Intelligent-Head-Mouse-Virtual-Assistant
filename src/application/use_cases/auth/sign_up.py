from dataclasses import dataclass
from typing import List
import numpy as np
import uuid

from application.interfaces.FaceRepository import FaceRepository
from domain.entities.User import User
from domain.entities.Face import Face
from application.interfaces.UserRepository import UserRepository
from application.interfaces.UserSettingsRepository import UserSettingsRepository
from domain.entities.UserSettings import UserSettings


@dataclass
class SignUpCommand:
    username: str
    images: List[bytes]

class SignUpUseCase:
    def __init__(self, user_repository: UserRepository, face_repository: FaceRepository , settings_repo : UserSettingsRepository):
        self.user_repository = user_repository
        self.face_repository = face_repository
        self.settings_repository = settings_repo
    def execute(self, signupData: SignUpCommand) -> dict:
        try:
            user = User(
                name=signupData.username,
            )        
            
            self.user_repository.add(user)
            
            for image in signupData.images:
                face = Face(
                    user_id=user.user_id,
                    face_data=image
                )
                self.face_repository.add(face)
            
            settings = UserSettings(
                user_id = user.user_id,
            )
        
            self.settings_repository.add(settings=settings)
            
            return {
                'success': True,
                'user_id': user.user_id,
                'message': 'User created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 