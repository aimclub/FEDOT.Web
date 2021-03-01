BASE_ROUTE = 'model'


def register_routes(api, app):
    from .controller import api as model_api

    api.add_namespace(model_api, path=f"/{BASE_ROUTE}")
