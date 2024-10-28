import base64
import json
from typing import cast
from unittest.mock import Mock

from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Role
from repositories import IncidentRepository

from .util import gen_token


class TestIncident(ParametrizedTestCase):
    INCIDENT_API_USER_URL = '/api/v1/users/me/incidents'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def call_incident_api_user(self, token: dict[str, str] | None) -> TestResponse:
        if token is None:
            return self.client.post(self.INCIDENT_API_USER_URL)

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(self.INCIDENT_API_USER_URL, headers={'X-Apigateway-Api-Userinfo': token_encoded})

    def test_user_incidents_no_token(self) -> None:
        resp = self.call_incident_api_user(None)

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': 'Token is missing'})

    @parametrize(
        'missing_field',
        [
            ('sub',),
            ('cid',),
            ('role',),
            ('aud',),
        ],
    )
    def test_user_incidents_token_missing_fields(self, missing_field: str) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=Role.USER,
            assigned=True,
        )
        del token[missing_field]
        resp = self.call_incident_api_user(token)

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': f'{missing_field} is missing in token'})

    def test_user_incidents(self) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=Role.USER,
            assigned=True,
        )

        incident_repo_mock = Mock(IncidentRepository)
        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_incident_api_user(token)

        self.assertEqual(resp.status_code, 201)
