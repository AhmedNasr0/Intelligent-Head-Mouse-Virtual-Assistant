from typing import Optional
import uuid
from application.interfaces.UserSettingsRepository import UserSettingsRepository
from domain.entities.UserSettings import UserSettings
from infrastructure.database.database import db

class UserSettingsRepository(UserSettingsRepository):
    def add(self, settings: UserSettings) -> None:
        
        try:
            setting_id=uuid.uuid4()
            settings.setting_id=setting_id 
            db.cursor.execute(
                """
                INSERT INTO user_settings (setting_id, user_id, smoothing, amplification)
                VALUES (%s, %s, %s, %s)
                """,
                (str(setting_id), str(settings.user_id), settings.smoothing, settings.amplification)
            )
            db.conn.commit()
        except Exception as e:
            db.conn.rollback()
            raise e

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSettings]:
        db.cursor.execute(
            "SELECT * FROM user_settings WHERE user_id = %s",
            (str(user_id),)
        )
        result = db.cursor.fetchone()
        if result:
            return UserSettings(
                setting_id=uuid.UUID(result['setting_id']),
                user_id=uuid.UUID(result['user_id']),
                smoothing=result.get('smoothing', 0.9),
                amplification=result.get('amplification', 6.5)
            )
        return None

    def update_by_user_id(self, settings: UserSettings) -> None:
        try:
            db.cursor.execute(
                """
                UPDATE user_settings 
                SET smoothing = %s, amplification = %s
                WHERE user_id = %s
                """,
                (settings.smoothing, settings.amplification, str(settings.user_id))
            )
            db.conn.commit()
        except Exception as e:
            db.conn.rollback()
            raise e

    def delete_by_user_id(self, user_id: uuid.UUID) -> None:
        try:
            db.cursor.execute(
                "DELETE FROM user_settings WHERE user_id = %s",
                (str(user_id),)
            )
            db.conn.commit()
        except Exception as e:
            db.conn.rollback()
            raise e 