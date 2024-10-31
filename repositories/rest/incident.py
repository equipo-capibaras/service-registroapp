from typing import Any

import requests

from models import Incident, IncidentResponse
from repositories import IncidentRepository

from .base import RestBaseRepository
from .util import TokenProvider


class RestIncidentRepository(IncidentRepository, RestBaseRepository):
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        RestBaseRepository.__init__(self, base_url, token_provider)

    def create(self, incident: Incident) -> IncidentResponse | None:
        data = {
            'client_id': incident.client_id,
            'name': incident.name,
            'channel': incident.channel.value,
            'reported_by': incident.reported_by,
            'created_by': incident.created_by,
            'description': incident.description,
            'assigned_to': incident.assigned_to,
        }

        resp = self.authenticated_post(f'{self.base_url}/api/v1/register/incident', json=data)

        if resp.status_code == requests.codes.created:
            response_data = resp.json()
            return IncidentResponse(
                id=response_data['id'],
                client_id=response_data['client_id'],
                name=response_data['name'],
                channel=response_data['channel'],
                reported_by=response_data['reported_by'],
                created_by=response_data['created_by'],
                assigned_to=response_data['assigned_to'],
            )

        return None


