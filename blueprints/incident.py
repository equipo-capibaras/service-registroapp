from dataclasses import field, dataclass
from typing import Any

import marshmallow
from dependency_injector.wiring import Provide
from flask import Blueprint, Response, request
from flask.views import MethodView
import marshmallow_dataclass
from marshmallow import ValidationError

from containers import Container
from models import Channel, Incident, Role
from repositories import IncidentRepository, UserRepository

from .util import class_route, json_response, requires_token, error_response, validation_error_response

blp = Blueprint('Incidents', __name__)

JSON_VALIDATION_ERROR = 'Request body must be a JSON object.'

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

@class_route(blp, '/api/v1/incidents/web')
class WebRegistrationIncident(MethodView):
    init_every_request = False

    def _validate_authorization(self, token: dict[str, Any]) -> None:
        if token['role'] not in [Role.ADMIN.value, Role.AGENT.value]:
            raise PermissionError('Forbidden: You do not have access to this resource.')

        if token['cid'] is None:
            raise PermissionError('Unauthorized: You do not belong to any client.')

    @requires_token
    def post(
        self,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
        user_repo: UserRepository = Provide[Container.user_repo],
    ) -> Response:
        try:
            self._validate_authorization(token)

            # Parse request body
            incident_schema = marshmallow_dataclass.class_schema(IncidentRegistrationBody)()
            req_json = request.get_json(silent=True)
            if req_json is None:
                raise ValueError(JSON_VALIDATION_ERROR)

            data: IncidentRegistrationBody = incident_schema.load(req_json)

            # Validate User
            user = user_repo.find_by_email(data.email)
            if user is None:
                raise ValueError('Invalid value for email: User does not exist.')

            if user.client_id != token['cid']:
                raise ValueError('Unauthorized: User does not belong to your client.')

        except ValueError as err:
            return error_response(str(err), 400)

        except PermissionError as err:
            return error_response(str(err), 401)

        # Create incident
        incident = Incident(
            client_id=token['cid'],
            name=data.name,
            channel=Channel.WEB,
            reported_by=user.id,
            created_by=token['sub'],
            description=data.description,
        )

        incident_repo.create(
            client_id=incident.client_id,
            name=incident.name,
            channel=incident.channel,
            reported_by=incident.reported_by,
            created_by=incident.created_by,
            description=incident.description,
        )

        return json_response(incident_to_dict(incident), 201)


