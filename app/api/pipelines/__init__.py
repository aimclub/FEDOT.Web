BASE_ROUTE = 'pipelines'


def register_routes(api, app):
    from .controller import api as pipelines_api

    api.add_namespace(pipelines_api, path=f"/{BASE_ROUTE}")
