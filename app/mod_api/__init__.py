BASE_ROUTE = 'model'


def register_routes(api, app, root="api"):
    from .controller import api as model_api

    api.add_namespace(model_api, path=f"/{root}/{BASE_ROUTE}")