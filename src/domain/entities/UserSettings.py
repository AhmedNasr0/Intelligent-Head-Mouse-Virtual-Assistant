from dataclasses import dataclass
import uuid
from typing import Optional
from dataclasses import dataclass, field

@dataclass
class UserSettings:
    setting_id: Optional[uuid.UUID] = field(default=None)
    user_id: Optional[uuid.UUID] = field(default=None)
    smoothing: float = 0.9
    amplification: float = 6.5