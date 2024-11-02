from dataclasses import dataclass
from datetime import datetime

from .role import Role


@dataclass
class Employee:
    id: str
    client_id: str
    name: str
    email: str
    role: Role
    invitation_status: str
    invitation_date: datetime
