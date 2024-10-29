from dataclasses import field, dataclass
from typing import Any

import marshmallow
from dependency_injector.wiring import Provide
from flask import Blueprint, Response
from flask.views import MethodView

from containers import Container
from models import Channel, Incident
from repositories import IncidentRepository

from .util import class_route, json_response, requires_token

blp = Blueprint('Incidents', __name__)

def incident_to_dict(incident: Incident) -> dict[str, Any]:
    return {
        'client_id': incident.client_id,
        'name': incident.name,
        'channel': incident.channel.value,
        'reported_by': incident.reported_by,
        'created_by': incident.created_by,
        'description': incident.description,
    }

# Incident validation class
@dataclass
class IncidentRegistrationBody:
    email: str = field(metadata={'validate': [marshmallow.validate.Email(), marshmallow.validate.Length(min=1, max=60)]})
    name: str = field(metadata={'validate': [marshmallow.validate.Length(min=1, max=90)]})
    description: str = field(metadata={'validate': [marshmallow.validate.Length(min=1, max=5000)]})

@class_route(blp, '/api/v1/users/me/incidents')
class UserIncidents(MethodView):
    init_every_request = False

    @requires_token
    def post(
        self,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        incident_repo.create(
            client_id=token['cid'],
            name='Test Incident',
            channel=Channel.MOBILE,
            reported_by=token['sub'],
            created_by=token['sub'],
            description='This is a test incident',
        )

        return json_response({'id': '753f5554-c545-447d-8a4d-4eccda9e952a'}, 201)

