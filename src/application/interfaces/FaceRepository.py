from abc import ABC, abstractmethod
import uuid
from typing import Optional, List
from domain.entities.Face import Face
class FaceRepository(ABC):
    @abstractmethod
    def add(self, face: Face) -> Face:
        pass
        
    @abstractmethod
    def get_by_user_id(self, user_id: uuid.UUID) -> List[dict]:
        pass
        
    @abstractmethod
    def delete_by_user_id(self, user_id: uuid.UUID) -> None:
        pass