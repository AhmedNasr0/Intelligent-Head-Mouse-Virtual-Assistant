from abc import ABC, abstractmethod
import uuid
from domain.entities.UserSettings import UserSettings

class UserSettingsRepository(ABC):
    @abstractmethod
    def add(self, settings: UserSettings):
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: uuid.UUID) -> UserSettings | None:
        pass

    
    @abstractmethod
    def update_by_user_id(self, settings: UserSettings):
        pass
    
    @abstractmethod
    def delete_by_user_id(self, user_id: uuid.UUID):
        pass
