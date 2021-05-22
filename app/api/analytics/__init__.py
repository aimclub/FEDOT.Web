BASE_ROUTE = 'analytics'


def register_routes(api, app):
    from .controller import api as analytics_api

    api.add_namespace(analytics_api, path=f"/{BASE_ROUTE}")
