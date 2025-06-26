from abc import ABC, abstractmethod
import uuid
from domain.entities.User import User

class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        pass
    
    @abstractmethod
    def update_by_id(self, user: User):
        pass
    
    @abstractmethod
    def delete_by_id(self, user_id: uuid.UUID):
        pass
    
    @abstractmethod
    def get_all(self) -> list[User]:
        pass
    
    @abstractmethod
    def delete_by_email(self, email: str):
        pass
    
    @abstractmethod
    def update_by_email(self, user: User):
        pass
    
