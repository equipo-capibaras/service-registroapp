from dataclasses import dataclass


@dataclass
class Employee:
    id: str
    client_id: str
    name: str
    email: str
    role: str
    invitation_status: str
    invitation_date: str
