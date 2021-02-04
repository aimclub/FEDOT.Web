BASE_ROUTE = 'meta'


def register_routes(api, app, root="api"):
    from .controller import api as meta_api

    api.add_namespace(meta_api, path=f"/{root}/{BASE_ROUTE}")
