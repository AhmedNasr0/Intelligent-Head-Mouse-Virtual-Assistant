from dataclasses import dataclass
import uuid
from dataclasses import field
from typing import Optional

@dataclass
class User:
    name: str
    email: Optional[str] = None 
    user_id: Optional[uuid.UUID] = field(default=None)
