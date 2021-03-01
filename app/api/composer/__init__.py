BASE_ROUTE = 'composer'


def register_routes(api, app):
    from .controller import api as composer_api

    api.add_namespace(composer_api, path=f"/{BASE_ROUTE}")
