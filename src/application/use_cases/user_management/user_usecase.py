
from ...domain.entities import User
from ..interfaces import UserRepository
import uuid

class UserUsecase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def add_user(self, user: User):
        self.user_repository.add(user)
    
    def get_user_by_id(self, user_id: uuid.UUID):
        return self.user_repository.get_by_id(user_id)
    
    def get_user_by_email(self, email: str):
        return self.user_repository.get_by_email(email)
    
    def update_user(self, user: User):
        self.user_repository.update(user)
    
    def delete_user(self, user_id: uuid.UUID):
        self.user_repository.delete(user_id)
    
    def get_all_users(self):
        return self.user_repository.get_all()
    
    def get_user_by_name(self, name: str):
        return self.user_repository.get_by_name(name)
    

    
