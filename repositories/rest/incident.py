import requests

from repositories import IncidentRepository

from .base import RestBaseRepository
from .util import TokenProvider


class RestIncidentRepository(IncidentRepository, RestBaseRepository):
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        RestBaseRepository.__init__(self, base_url, token_provider)

    def create(self, *, client_id: str, name: str, channel: str, reported_by: str, created_by: str, description: str) -> None:  # noqa: PLR0913
        data = {
            'clientId': client_id,
            'name': name,
            'channel': channel,
            'reportedBy': reported_by,
            'createdBy': created_by,
            'description': description,
        }

        resp = self.authenticated_post(f'{self.base_url}/api/v1/incidents', data)

        if resp.status_code == requests.codes.created:
            return

        self.unexpected_error(resp)
