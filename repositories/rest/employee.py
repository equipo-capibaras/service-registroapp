import datetime
from enum import Enum
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
            json['invitation_status'] = json.pop('invitationStatus')
            json['invitation_date'] = json.pop('invitationDate')
            return dacite.from_dict(
                data_class=Employee,
                data=json,
                config=dacite.Config(cast=[Enum], type_hooks={datetime.datetime: datetime.datetime.fromisoformat}),
            )

        if resp.status_code == requests.codes.not_found:
            return None

        self.unexpected_error(resp)  # noqa: RET503
