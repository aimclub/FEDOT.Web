def register_routes(api, app, root="app"):
    from app.api.model import register_routes as attach_model
    from app.api.meta import register_routes as attach_meta
    from app.api.chains import register_routes as attach_chains
    from app.api.composer import register_routes as attach_composer
    from app.api.data import register_routes as attach_data
    from app.api.auth import register_routes as attach_token
    from app.api.showcase import register_routes as attach_showcase
    from app.api.sandbox import register_routes as attach_sandbox
    from app.api.analytics import register_routes as attach_analytics

    # Add routes
    attach_model(api, app)
    attach_meta(api, app)
    attach_chains(api, app)
    attach_composer(api, app)
    attach_data(api, app)
    attach_token(api, app)
    attach_showcase(api, app)
    attach_sandbox(api, app)
    attach_analytics(api, app)
