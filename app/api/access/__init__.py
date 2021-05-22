BASE_ROUTE = 'access'


def register_routes(api, app):
    from .controller import api as access_api

    api.add_namespace(access_api, path=f"/{BASE_ROUTE}")
