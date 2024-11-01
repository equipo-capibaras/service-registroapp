from repositories import EmployeeRepository

from .base import RestBaseRepository
from .util import TokenProvider


class RestEmployeeRepository(EmployeeRepository, RestBaseRepository):
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        RestBaseRepository.__init__(self, base_url, token_provider)
