BASE_ROUTE = 'token'


def register_routes(api, app):
    from .controller import api as token_api

    api.add_namespace(token_api, path=f"/{BASE_ROUTE}")