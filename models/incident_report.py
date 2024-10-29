from dataclasses import dataclass

from models import Channel


@dataclass
class Incident:
    client_id: str
    name: str
    channel: Channel
    reported_by: str
    created_by: str
    description: str