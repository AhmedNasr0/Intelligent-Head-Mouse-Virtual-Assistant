from typing import List, Optional
import uuid
from application.interfaces.UserRepository import UserRepository
from domain.entities.User import User
from infrastructure.database.database import db

class UserRepository(UserRepository):
    def add(self, user: User) -> User:
        try:
            user_id=uuid.uuid4()
            user.user_id=user_id
            db.cursor.execute(
                """
                INSERT INTO users (user_id, name, email)
                VALUES (%s, %s, %s)
                """,
                (str(user_id), user.name, user.email)
            )
            db.conn.commit()
            return user
        except Exception as e:
            db.conn.rollback()
            raise e

    def get_by_id(self, user_id: uuid.UUID) -> User:
        db.cursor.execute(
            "SELECT * FROM users WHERE user_id = %s",
            (str(user_id),)
        )
        result = db.cursor.fetchone()
        if result:
            return User(
                user_id=uuid.UUID(result['user_id']),
                name=result['name'],
                email=result['email']
            )
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        db.cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )
        result = db.cursor.fetchone()
        if result:
            return User(
                user_id=uuid.UUID(result['user_id']),
                name=result['name'],
                email=result['email'],
                password=result['password'],
                language=result['language']
            )
        return None

    def update_by_id(self, user: User) -> None:
        try:
            db.cursor.execute(
                """
                UPDATE users 
                SET name = %s, email = %s, password = %s, language = %s
                WHERE user_id = %s
                """,
                (user.name, user.email, user.password, user.language, str(user.user_id))
            )
            db.conn.commit()
        except Exception as e:
            db.conn.rollback()
            raise e

    def delete_by_id(self, user_id: uuid.UUID) -> None:
        try:
            db.cursor.execute(
                "DELETE FROM users WHERE user_id = %s",
                (str(user_id),)
            )
            db.conn.commit()
        except Exception as e:
            db.conn.rollback()
            raise e

    def get_all(self) -> List[User]:
        db.cursor.execute("SELECT * FROM users")
        results = db.cursor.fetchall()
        return [
            User(
                user_id=uuid.UUID(result['user_id']),
                name=result['name'],
                email=result['email'],
                password=result['password'],
                language=result['language']
            )
            for result in results
        ]

    def delete_by_email(self, email: str) -> None:
        try:
            db.cursor.execute(
                "DELETE FROM users WHERE email = %s",
                (email,)
            )
            db.conn.commit()
        except Exception as e:
            db.conn.rollback()
            raise e

    def update_by_email(self, user: User) -> None:
        try:
            db.cursor.execute(
                """
                UPDATE users 
                SET name = %s, password = %s, language = %s
                WHERE email = %s
                """,
                (user.name, user.password, user.language, user.email)
            )
            db.conn.commit()
        except Exception as e:
            db.conn.rollback()
            raise e 