def register_routes(api, app, root="api"):
    from app.model import register_routes as attach_model

    # Add routes
    attach_model(api, app)
