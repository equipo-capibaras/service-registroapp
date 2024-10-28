class IncidentRepository:
    def create(self, *, client_id: str, name: str, channel: str, reported_by: str, created_by: str, description: str) -> None:  # noqa: PLR0913
        raise NotImplementedError  # pragma: no cover
