def register_routes(api, app, root="api"):
    from app.model import register_routes as attach_model
    from app.meta import register_routes as attach_meta
    from app.chains import register_routes as attach_chains
    from app.composer import register_routes as attach_composer
    from app.data import register_routes as attach_data

    # Add routes
    attach_model(api, app)
    attach_meta(api, app)
    attach_chains(api, app)
    attach_composer(api, app)
    attach_data(api, app)
