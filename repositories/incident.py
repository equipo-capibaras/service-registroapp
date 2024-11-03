from models import Incident, IncidentResponse


class IncidentRepository:
    def create(self, incident: Incident) -> IncidentResponse:
        raise NotImplementedError  # pragma: no cover
