import json
from typing import cast

import responses
from faker import Faker
from unittest_parametrize import ParametrizedTestCase

from models import Channel, Incident, IncidentResponse
from repositories.rest import RestIncidentRepository


class TestIncident(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.base_url = self.faker.url().rstrip('/')
        self.repo = RestIncidentRepository(self.base_url, None)

    def gen_random_incident(self) -> Incident:
        return Incident(
            client_id=str(self.faker.uuid4()),
            name=self.faker.name(),
            channel=self.faker.random_element([Channel.WEB, Channel.EMAIL, Channel.MOBILE]),
            reported_by=str(self.faker.uuid4()),
            created_by=str(self.faker.uuid4()),
            description=self.faker.sentence(),
            assigned_to=str(self.faker.uuid4()),
        )

    def test_create_success(self) -> None:
        incident = self.gen_random_incident()
        response_data = {
            'id': str(self.faker.uuid4()),
            'client_id': incident.client_id,
            'name': incident.name,
            'channel': incident.channel.value,
            'reported_by': incident.reported_by,
            'created_by': incident.created_by,
            'assigned_to': incident.assigned_to,
        }

        with responses.RequestsMock() as rsps:
            rsps.post(
                f'{self.base_url}/api/v1/register/incident',
                json=response_data,
                status=201,
            )

            result = self.repo.create(incident)

            # Verificar que el resultado no sea None
            self.assertIsNotNone(result)

            # Verificar que el resultado sea una instancia de IncidentResponse
            if result is not None:  # Necesario para que mypy no marque error
                self.assertIsInstance(result, IncidentResponse)
                self.assertEqual(result.id, response_data['id'])
                self.assertEqual(result.client_id, response_data['client_id'])
                self.assertEqual(result.name, response_data['name'])
                self.assertEqual(result.channel, response_data['channel'])
                self.assertEqual(result.reported_by, response_data['reported_by'])
                self.assertEqual(result.created_by, response_data['created_by'])
                self.assertEqual(result.assigned_to, response_data['assigned_to'])

            # Verificar que la solicitud se envió correctamente
            body = cast(str | bytes, rsps.calls[0].request.body)
            req_json = json.loads(body)
            self.assertEqual(
                req_json,
                {
                    'client_id': incident.client_id,
                    'name': incident.name,
                    'channel': incident.channel.value,
                    'reported_by': incident.reported_by,
                    'created_by': incident.created_by,
                    'description': incident.description,
                    'assigned_to': incident.assigned_to,
                },
            )

    def test_create_unexpected_error(self) -> None:
        incident = self.gen_random_incident()

        with responses.RequestsMock() as rsps:
            rsps.post(
                f'{self.base_url}/api/v1/register/incident',
                status=500,
            )

            result = self.repo.create(incident)

            # Verificar que el resultado sea None en caso de error
            self.assertIsNone(result)
