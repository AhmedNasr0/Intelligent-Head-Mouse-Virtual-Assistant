from typing import List, Optional
import uuid
from application.interfaces.FaceRepository import FaceRepository
from infrastructure.database.database import db
from domain.entities.Face import Face
from datetime import datetime

class FaceRepository(FaceRepository):
    def add(self, face: Face) -> Face:
        try:
            face_id=uuid.uuid4()
            face.face_id=face_id
            created_at=datetime.now()
            db.cursor.execute(
                """
                INSERT INTO faces (face_id, user_id, face_data, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (str(face_id), str(face.user_id), face.face_data, created_at)
            )
            db.conn.commit()
            return face
        except Exception as e:
            db.conn.rollback()
            raise e

    def get_by_user_id(self, user_id: uuid.UUID) -> List[dict]:
        db.cursor.execute(
            "SELECT * FROM faces WHERE user_id = %s",
            (str(user_id),)
        )
        results = db.cursor.fetchall()
        return [dict(result) for result in results]

    def get_all(self) -> List[dict]:
        db.cursor.execute("SELECT * FROM faces")
        results = db.cursor.fetchall()
        return [dict(result) for result in results]

    def get_all_by_user_id(self, user_id: uuid.UUID) -> List[dict]:
        db.cursor.execute("SELECT * FROM faces WHERE user_id = %s", (str(user_id),))
        results = db.cursor.fetchall()
        return [dict(result) for result in results]
    
    def get_all(self) -> List[Face]:
        db.cursor.execute("SELECT * FROM faces")
        results = db.cursor.fetchall()
        return [Face(**result) for result in results]
    
    
    def delete_by_user_id(self, user_id: uuid.UUID) -> None:
        try:
            db.cursor.execute(
                "DELETE FROM faces WHERE user_id = %s",
                (str(user_id),)
            )
            db.conn.commit()
        except Exception as e:
            db.conn.rollback()
            raise e