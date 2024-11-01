import os

from flask import Flask
from gcp_microservice_utils import setup_apigateway, setup_cloud_logging, setup_cloud_trace

from blueprints import BlueprintHealth, BlueprintIncident
from containers import Container
from environment import configure_environment_variables


class FlaskMicroservice(Flask):
    container: Container


def create_app() -> FlaskMicroservice:
    if os.getenv('ENABLE_CLOUD_LOGGING') == '1':
        setup_cloud_logging()  # pragma: no cover

    app = FlaskMicroservice(__name__)
    app.container = Container()

    configure_environment_variables(app.container)

    if os.getenv('ENABLE_CLOUD_TRACE') == '1':  # pragma: no cover
        setup_cloud_trace(app)

    setup_apigateway(app)

    app.register_blueprint(BlueprintHealth)
    app.register_blueprint(BlueprintIncident)

    return app
