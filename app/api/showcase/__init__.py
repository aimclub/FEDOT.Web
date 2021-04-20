BASE_ROUTE = 'showcase'


def register_routes(api, app):
    from .controller import api as showcase_api

    api.add_namespace(showcase_api, path=f"/{BASE_ROUTE}")
