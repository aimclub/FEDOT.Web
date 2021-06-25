import os

from app import create_app, socketio, db
from app.ssl.ssl_config import SslConfig

# example?
# FLASK_ENV=dev
# FLASK_HOST=10.9.14.122
# FLASK_PORT=5000

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
