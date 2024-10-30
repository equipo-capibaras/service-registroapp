import base64
import json
from typing import Any, cast
from unittest.mock import Mock

from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Channel, Role, User
from repositories import IncidentRepository, UserRepository

from .util import gen_token


class TestIncident(ParametrizedTestCase):
    INCIDENT_API_USER_URL = '/api/v1/users/me/incidents'
    INCIDENT_API_WEB_URL = '/api/v1/incidents/web'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def call_incident_api_user(self, token: dict[str, str] | None) -> TestResponse:
        if token is None:
            return self.client.post(self.INCIDENT_API_USER_URL)

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(self.INCIDENT_API_USER_URL, headers={'X-Apigateway-Api-Userinfo': token_encoded})

    def call_web_incident_api(self, token: dict[str, str] | None, body: dict[str, Any] | None) -> TestResponse:
        headers = {}
        if token:
            token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
            headers['X-Apigateway-Api-Userinfo'] = token_encoded

        return self.client.post(self.INCIDENT_API_WEB_URL, headers=headers, json=body)

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

    def test_web_incident_no_token(self) -> None:
        resp = self.call_web_incident_api(None, None)
        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 401, 'message': 'Token is missing'})

    @parametrize(
        'role',
        [
            (Role.USER,),
            (Role.ANALYST,),
        ],
    )
    def test_web_incident_invalid_role(self, role: Role) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=role,
            assigned=True,
        )
        resp = self.call_web_incident_api(token, {})
        self.assertEqual(resp.status_code, 403)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 403, 'message': 'Forbidden: You do not have access to this resource.'})

    def test_web_incident_no_client(self) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=None,
            role=Role.ADMIN,
            assigned=True,
        )
        resp = self.call_web_incident_api(token, {})
        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 401, 'message': 'Unauthorized: You do not belong to any client.'})

    def test_web_incident_invalid_body(self) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=Role.ADMIN,
            assigned=True,
        )
        resp = self.call_web_incident_api(token, {"name": "test"})
        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['code'], 400)

    def test_web_incident_user_not_found(self) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=Role.ADMIN,
            assigned=True,
        )
        body = {
            'email': self.faker.email(),
            'name': self.faker.word(),
            'description': self.faker.sentence(),
        }

        user_repo_mock = Mock(UserRepository)
        cast(Mock, user_repo_mock.find_by_email).return_value = None

        with self.app.container.user_repo.override(user_repo_mock):
            resp = self.call_web_incident_api(token, body)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['code'], 404)
        self.assertEqual(resp_data['message'], 'Invalid value for email: User does not exist.')

    def test_web_incident_user_not_belonging_to_client(self) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=Role.ADMIN,
            assigned=True,
        )
        user = User(
            id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),  # Different client_id than token
            name=self.faker.name(),
            email=self.faker.email(),
        )
        body = {
            'email': user.email,
            'name': self.faker.word(),
            'description': self.faker.sentence(),
        }

        user_repo_mock = Mock(UserRepository)
        cast(Mock, user_repo_mock.find_by_email).return_value = user

        with self.app.container.user_repo.override(user_repo_mock):
            resp = self.call_web_incident_api(token, body)

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['code'], 401)
        self.assertEqual(resp_data['message'], 'Unauthorized: User does not belong to your client.')

    def test_web_incident_success(self) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=Role.ADMIN,
            assigned=True,
        )
        user = User(
            id=cast(str, self.faker.uuid4()),
            client_id=token['cid'],
            name=self.faker.name(),
            email=self.faker.email(),
        )
        body = {
            'email': user.email,
            'name': self.faker.word(),
            'description': self.faker.sentence(),
        }

        user_repo_mock = Mock(UserRepository)
        incident_repo_mock = Mock(IncidentRepository)

        cast(Mock, user_repo_mock.find_by_email).return_value = user

        with (
            self.app.container.user_repo.override(user_repo_mock),
            self.app.container.incident_repo.override(incident_repo_mock),
        ):
            resp = self.call_web_incident_api(token, body)

        self.assertEqual(resp.status_code, 201)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['name'], body['name'])
        self.assertEqual(resp_data['channel'], Channel.WEB.value)
        self.assertEqual(resp_data['reported_by'], user.id)
        self.assertEqual(resp_data['created_by'], token['sub'])
