BASE_ROUTE = 'composer'


def register_routes(api, app):
    from .controller import api as composer_api
    from .controller import async_composer as async_composer_api

    api.add_namespace(composer_api, path=f"/{BASE_ROUTE}")
    app.register_blueprint(async_composer_api)
