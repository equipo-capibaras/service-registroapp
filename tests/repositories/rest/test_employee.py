import responses
from faker import Faker
from unittest_parametrize import ParametrizedTestCase

from models import Employee
from repositories.rest import RestEmployeeRepository


class TestEmployee(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.base_url = self.faker.url().rstrip('/')
        self.repo = RestEmployeeRepository(self.base_url, None)

    def test_get_random_agent_success(self) -> None:
        # Simular respuesta exitosa del servicio con un agente aleatorio
        response_data = {
            'id': str(self.faker.uuid4()),
            'clientId': str(self.faker.uuid4()),
            'name': self.faker.name(),
            'email': self.faker.email(),
            'role': 'agent',
            'invitationStatus': 'accepted',
            'invitationDate': self.faker.date_time().isoformat(),
        }

        with responses.RequestsMock() as rsps:
            rsps.get(
                f'{self.base_url}/api/v1/random/{response_data["clientId"]}/agent',
                json=response_data,
                status=200,
            )

            result = self.repo.get_random_agent(response_data['clientId'])

            # Verificar que el resultado no sea None
            self.assertIsNotNone(result)

            # Verificar que el resultado sea una instancia de Employee
            if result is not None:  # Necesario para que mypy no marque error
                self.assertIsInstance(result, Employee)
                self.assertEqual(result.id, response_data['id'])
                self.assertEqual(result.client_id, response_data['clientId'])
                self.assertEqual(result.name, response_data['name'])
                self.assertEqual(result.email, response_data['email'])
                self.assertEqual(result.role, response_data['role'])
                self.assertEqual(result.invitation_status, response_data['invitationStatus'])
                self.assertEqual(result.invitation_date, response_data['invitationDate'])

    def test_get_random_agent_not_found(self) -> None:
        client_id = str(self.faker.uuid4())

        with responses.RequestsMock() as rsps:
            rsps.get(
                f'{self.base_url}/api/v1/random/{client_id}/agent',
                status=404,
            )

            result = self.repo.get_random_agent(client_id)

            # Verificar que el resultado sea None en caso de no encontrar un agente
            self.assertIsNone(result)
