import os

from app import create_app, db, socketio
from app.ssl.ssl_config import SslConfig

app = create_app(os.getenv("FLASK_ENV") or "dev")

ssl_config = SslConfig()
ssl_config.get_config("app/ssl/cert")

if __name__ == "__main__":
    db.create_all(app=app)
    host = os.getenv("FLASK_HOST")
    port = os.getenv("FLASK_PORT")
    if not host:
        socketio.run(app, ssl_context=ssl_config.get_context(), use_reloader=False)
    else:
        socketio.run(app, ssl_context=ssl_config.get_context(), use_reloader=False, host=host, port=port)
