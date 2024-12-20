from dataclasses import dataclass, field
from typing import Any

import marshmallow
import marshmallow_dataclass
from dependency_injector.wiring import Provide
from flask import Blueprint, Response, request
from flask.views import MethodView

from containers import Container
from models import Channel, Incident, IncidentResponse, Role
from repositories import EmployeeRepository, IncidentRepository, UserRepository

from .util import class_route, error_response, json_response, requires_token, validation_error_response

blp = Blueprint('Incidents', __name__)

JSON_VALIDATION_ERROR = 'Request body must be a JSON object.'


def incident_to_dict(incident: IncidentResponse) -> dict[str, Any]:
    return {
        'id': incident.id,
        'client_id': incident.client_id,
        'name': incident.name,
        'channel': incident.channel,
        'reported_by': incident.reported_by,
        'created_by': incident.created_by,
        'assigned_to': incident.assigned_to,
    }


# Incident validation class
@dataclass
class IncidentRegistrationBody:
    email: str = field(metadata={'validate': [marshmallow.validate.Email(), marshmallow.validate.Length(min=1, max=60)]})
    name: str = field(metadata={'validate': [marshmallow.validate.Length(min=1, max=60)]})
    description: str = field(metadata={'validate': [marshmallow.validate.Length(min=1, max=1000)]})


# Incident validation class for mobile
@dataclass
class IncidentMobileRegistrationBody:
    name: str = field(metadata={'validate': [marshmallow.validate.Length(min=1, max=60)]})
    description: str = field(metadata={'validate': [marshmallow.validate.Length(min=1, max=1000)]})


@class_route(blp, '/api/v1/users/me/incidents')
class UserIncidents(MethodView):
    init_every_request = False

    @requires_token
    def post(
        self,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        incident = Incident(
            client_id=token['cid'],
            name='Test Incident',
            channel=Channel.MOBILE,
            reported_by=token['sub'],
            created_by=token['sub'],
            description='This is a test incident',
            assigned_to=token['sub'],
        )
        incident_repo.create(incident)

        return json_response({'id': '753f5554-c545-447d-8a4d-4eccda9e952a'}, 201)


@class_route(blp, '/api/v1/incidents/web')
class WebRegistrationIncident(MethodView):
    init_every_request = False

    def validate_token_info(self, token: dict[str, Any]) -> tuple[str | None, int | None]:
        error_message = None
        error_code = None

        if token['role'] not in [Role.ADMIN.value, Role.AGENT.value]:
            error_message = 'Forbidden: You do not have access to this resource.'
            error_code = 403
        if token['cid'] is None:
            error_message = 'Unauthorized: You do not belong to any client.'
            error_code = 401

        return error_message, error_code

    @requires_token
    def post(
        self,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
        user_repo: UserRepository = Provide[Container.user_repo],
    ) -> Response:
        # Validate employee
        error_message, error_code = self.validate_token_info(token)

        # Return error response if any
        if error_message and error_code:
            return error_response(error_message, error_code)

        # Parse request body
        incident_schema = marshmallow_dataclass.class_schema(IncidentRegistrationBody)()
        req_json = request.get_json(silent=True)
        if req_json is None:
            return error_response(JSON_VALIDATION_ERROR, 400)

        try:
            data: IncidentRegistrationBody = incident_schema.load(req_json)
        except marshmallow.ValidationError as err:
            return validation_error_response(err)

        # Get and validate user
        user = user_repo.find_by_email(data.email)

        if user is None or user.client_id != token['cid']:
            return error_response('Invalid value for email: User does not exist.', 404)

        # Return error response if any
        if error_message and error_code:
            return error_response(error_message, error_code)

        incident = Incident(
            client_id=token['cid'],
            name=data.name,
            channel=Channel.WEB,
            reported_by=user.id,
            created_by=token['sub'],
            description=data.description,
            assigned_to=token['sub'],
        )

        incident_response = incident_repo.create(incident)

        return json_response(incident_to_dict(incident_response), 201)


@class_route(blp, '/api/v1/incidents/mobile')
class MobileRegistrationIncident(MethodView):
    init_every_request = False

    @requires_token
    def post(
        self,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
        employee_repo: EmployeeRepository = Provide[Container.employee_repo],
    ) -> Response:
        # Validate user
        if token['role'] != Role.USER.value:
            return error_response('Forbidden: You do not have access to this resource.', 403)

        # Parse request body
        incident_schema = marshmallow_dataclass.class_schema(IncidentMobileRegistrationBody)()
        req_json = request.get_json(silent=True)
        if req_json is None:
            return error_response(JSON_VALIDATION_ERROR, 400)

        try:
            data: IncidentMobileRegistrationBody = incident_schema.load(req_json)
        except marshmallow.ValidationError as err:
            return validation_error_response(err)

        # Get an assignee
        assignee = employee_repo.get_random_agent(token['cid'])

        if assignee is None:
            return error_response('No agents available to assign the incident.', 404)

        incident = Incident(
            client_id=token['cid'],
            name=data.name,
            channel=Channel.MOBILE,
            reported_by=token['sub'],
            created_by=token['sub'],
            description=data.description,
            assigned_to=assignee.id,
        )

        incident_response = incident_repo.create(incident)

        return json_response(incident_to_dict(incident_response), 201)
