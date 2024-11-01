from dataclasses import dataclass


@dataclass
class IncidentResponse:
    id: str
    client_id: str
    name: str
    channel: str
    reported_by: str
    created_by: str
    assigned_to: str
