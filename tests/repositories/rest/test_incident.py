import json
from typing import cast

import responses
from faker import Faker
from requests import HTTPError
from unittest_parametrize import ParametrizedTestCase

from repositories.rest import RestIncidentRepository


class TestIncident(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.base_url = self.faker.url().rstrip('/')
        self.repo = RestIncidentRepository(self.base_url, None)

    def gen_random_data(self) -> dict[str, str]:
        return {
            'clientId': cast(str, self.faker.uuid4()),
            'name': self.faker.name(),
            'channel': self.faker.name(),
            'reportedBy': cast(str, self.faker.uuid4()),
            'createdBy': cast(str, self.faker.uuid4()),
            'description': cast(str, self.faker.uuid4()),
        }

    def test_create_success(self) -> None:
        data = self.gen_random_data()

        with responses.RequestsMock() as rsps:
            rsps.post(
                f'{self.base_url}/api/v1/incidents',
                status=201,
            )

            self.repo.create(
                client_id=data['clientId'],
                name=data['name'],
                channel=data['channel'],
                reported_by=data['reportedBy'],
                created_by=data['createdBy'],
                description=data['description'],
            )

            body = cast(str | bytes, rsps.calls[0].request.body)
            req_json = json.loads(body)
            self.assertEqual(req_json, data)

    def test_create_unexpected_error(self) -> None:
        data = self.gen_random_data()

        with responses.RequestsMock() as rsps:
            rsps.post(
                f'{self.base_url}/api/v1/incidents',
                status=500,
            )

            with self.assertRaises(HTTPError):
                self.repo.create(
                    client_id=data['clientId'],
                    name=data['name'],
                    channel=data['channel'],
                    reported_by=data['reportedBy'],
                    created_by=data['createdBy'],
                    description=data['description'],
                )
