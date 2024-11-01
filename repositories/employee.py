from models import Employee


class EmployeeRepository:
    def get_random_agent(self, client_id: str) -> Employee | None:
        raise NotImplementedError  # pragma: no cover
