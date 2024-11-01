from typing import Any, cast

import dacite
import requests

from models import Employee
from repositories import EmployeeRepository

from .base import RestBaseRepository
from .util import TokenProvider


class RestEmployeeRepository(EmployeeRepository, RestBaseRepository):
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        RestBaseRepository.__init__(self, base_url, token_provider)

    def get_random_agent(self, client_id: str) -> Employee | None:
        resp = self.authenticated_get(f'{self.base_url}/api/v1/random/{client_id}/agent')

        if resp.status_code == requests.codes.ok:
            json = cast(dict[str, Any], resp.json())
            json['client_id'] = json.pop('clientId')
            json['invitationStatus'] = json.pop('invitation_status')
            json['invitationDate'] = json.pop('invitation_date')
            return dacite.from_dict(data_class=Employee, data=json)

        if resp.status_code == requests.codes.not_found:
            return None

        self.unexpected_error(resp)  # noqa: RET503
