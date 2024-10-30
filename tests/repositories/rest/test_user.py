from typing import cast
from unittest.mock import Mock

import responses
from faker import Faker
from requests import HTTPError
from unittest_parametrize import ParametrizedTestCase, parametrize

from models import User
from repositories.rest import RestUserRepository, TokenProvider


class TestUser(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.base_url = self.faker.url().rstrip('/')
        self.repo = RestUserRepository(self.base_url, None)

    def test_authenticated_get_without_token_provider(self) -> None:
        repo = RestUserRepository(self.base_url, None)

        with responses.RequestsMock() as rsps:
            rsps.get(self.base_url)
            repo.authenticated_get(self.base_url)
            self.assertNotIn('Authorization', rsps.calls[0].request.headers)

    def test_authenticated_get_with_token_provider(self) -> None:
        token = self.faker.pystr()
        token_provider = Mock(TokenProvider)
        cast(Mock, token_provider.get_token).return_value = token

        repo = RestUserRepository(self.base_url, token_provider)

        with responses.RequestsMock() as rsps:
            rsps.get(self.base_url)
            repo.authenticated_get(self.base_url)
            self.assertEqual(rsps.calls[0].request.headers['Authorization'], f'Bearer {token}')

    def test_get_existing(self) -> None:
        user = User(
            id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            name=self.faker.name(),
            email=self.faker.email(),
        )

        with responses.RequestsMock() as rsps:
            rsps.get(
                f'{self.base_url}/api/v1/users/{user.client_id}/{user.id}',
                json={
                    'id': user.id,
                    'clientId': user.client_id,
                    'name': user.name,
                    'email': user.email,
                },
            )

            user_repo = self.repo.get(user.id, user.client_id)

        self.assertEqual(user_repo, user)

    def test_get_not_found(self) -> None:
        user_id = cast(str, self.faker.uuid4())
        client_id = cast(str, self.faker.uuid4())

        with responses.RequestsMock() as rsps:
            rsps.get(f'{self.base_url}/api/v1/users/{client_id}/{user_id}', status=404)

            user_repo = self.repo.get(user_id, client_id)

        self.assertIsNone(user_repo)

    @parametrize(
        'status',
        [
            (500,),
            (201,),
        ],
    )
    def test_get_error(self, status: int) -> None:
        user_id = cast(str, self.faker.uuid4())
        client_id = cast(str, self.faker.uuid4())

        with responses.RequestsMock() as rsps:
            rsps.get(f'{self.base_url}/api/v1/users/{client_id}/{user_id}', status=status)

            with self.assertRaises(HTTPError):
                self.repo.get(user_id, client_id)

    def test_find_by_email_success(self) -> None:
        user = User(
            id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            name=self.faker.name(),
            email=self.faker.email(),
        )

        with responses.RequestsMock() as rsps:
            rsps.post(
                f'{self.base_url}/api/v1/users/detail',
                json={
                    'id': user.id,
                    'clientId': user.client_id,
                    'name': user.name,
                    'email': user.email,
                },
                status=200,
            )

            user_repo = self.repo.find_by_email(user.email)

        self.assertEqual(user_repo, user)

    def test_find_by_email_not_found(self) -> None:
        email = self.faker.email()

        with responses.RequestsMock() as rsps:
            rsps.post(
                f'{self.base_url}/api/v1/users/detail',
                json={
                    'message': 'User not found',
                    'code': 404,
                },
                status=404,
            )

            user_repo = self.repo.find_by_email(email)

        self.assertIsNone(user_repo)

    @parametrize(
        'status',
        [
            (500,),  # Internal Server Error
            (400,),  # Bad Request (unexpected)
        ],
    )
    def test_find_by_email_error(self, status: int) -> None:
        email = self.faker.email()

        with responses.RequestsMock() as rsps:
            rsps.post(f'{self.base_url}/api/v1/users/detail', status=status)

            with self.assertRaises(HTTPError):
                self.repo.find_by_email(email)

    def test_find_by_email_with_token_provider(self) -> None:
        token = self.faker.pystr()
        token_provider = Mock(TokenProvider)
        cast(Mock, token_provider.get_token).return_value = token

        repo = RestUserRepository(self.base_url, token_provider)

        email = self.faker.email()

        with responses.RequestsMock() as rsps:
            rsps.post(
                f'{self.base_url}/api/v1/users/detail',
                json={
                    'id': cast(str, self.faker.uuid4()),
                    'clientId': cast(str, self.faker.uuid4()),
                    'name': self.faker.name(),
                    'email': email,
                },
                status=200,
            )

            repo.find_by_email(email)
            self.assertEqual(rsps.calls[0].request.headers['Authorization'], f'Bearer {token}')
