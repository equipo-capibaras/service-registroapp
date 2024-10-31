from models import Employee


class EmployeeRepository:
    def get_employee(self, client_id: str, employee_id: str) -> Employee | None:
        raise NotImplementedError  # pragma: no cover
