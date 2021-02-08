BASE_ROUTE = 'chains'


def register_routes(api, app):
    from .controller import api as chains_api

    api.add_namespace(chains_api, path=f"/{BASE_ROUTE}")
