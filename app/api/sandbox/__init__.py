BASE_ROUTE = 'sandbox'


def register_routes(api, app):
    from .controller import api as sandbox_api

    api.add_namespace(sandbox_api, path=f"/{BASE_ROUTE}")
