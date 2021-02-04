BASE_ROUTE = 'data'


def register_routes(api, app, root="api"):
    from .controller import api as data_api

    api.add_namespace(data_api, path=f"/{root}/{BASE_ROUTE}")
