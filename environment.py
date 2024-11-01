import os

from gcp_microservice_utils import GcpAuthToken

from containers import Container


def configure_environment_variables(container: Container) -> None:
    # Configure user service
    if 'USER_SVC_URL' in os.environ:  # pragma: no cover
        container.config.svc.user.url.from_env('USER_SVC_URL')

        if 'USER_SVC_TOKEN' in os.environ:
            container.config.svc.user.token_provider.from_value(
                type('TokenProvider', (object,), {'get_token': lambda: os.environ['USER_SVC_TOKEN']})
            )
        elif 'USE_CLOUD_TOKEN_PROVIDER' in os.environ:
            container.config.svc.user.token_provider.from_value(GcpAuthToken(os.environ['USER_SVC_URL']))

    # Configure client service
    if 'CLIENT_SVC_URL' in os.environ:  # pragma: no cover
        container.config.svc.client.url.from_env('CLIENT_SVC_URL')

        if 'CLIENT_SVC_TOKEN' in os.environ:
            container.config.svc.client.token_provider.from_value(
                type('TokenProvider', (object,), {'get_token': lambda: os.environ['CLIENT_SVC_TOKEN']})
            )
        elif 'USE_CLOUD_TOKEN_PROVIDER' in os.environ:
            container.config.svc.client.token_provider.from_value(GcpAuthToken(os.environ['CLIENT_SVC_URL']))

    # Configure incident modify service
    if 'INCIDENTMODIFY_SVC_URL' in os.environ:  # pragma: no cover
        container.config.svc.incidentmodify.url.from_env('INCIDENTMODIFY_SVC_URL')

        if 'INCIDENTMODIFY_SVC_TOKEN' in os.environ:
            container.config.svc.incidentmodify.token_provider.from_value(
                type('TokenProvider', (object,), {'get_token': lambda: os.environ['INCIDENTMODIFY_SVC_TOKEN']})
            )
        elif 'USE_CLOUD_TOKEN_PROVIDER' in os.environ:
            container.config.svc.incidentmodify.token_provider.from_value(GcpAuthToken(os.environ['INCIDENTMODIFY_SVC_URL']))
