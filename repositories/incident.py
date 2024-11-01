from models import Incident, IncidentResponse


class IncidentRepository:
    def create(self, incident: Incident) -> IncidentResponse | None:
        raise NotImplementedError  # pragma: no cover
