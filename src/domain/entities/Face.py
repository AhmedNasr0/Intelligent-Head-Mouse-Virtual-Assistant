from dataclasses import dataclass
from dataclasses import field
from typing import Optional
import uuid
from datetime import datetime

@dataclass
class Face:
    user_id: uuid.UUID
    face_data: bytes
    face_id: Optional[uuid.UUID] = field(default=None)
    created_at: Optional[datetime] = field(default=None)
