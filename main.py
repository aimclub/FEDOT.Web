import os

from app import create_app, socketio, db
from app.ssl.ssl_config import SslConfig

app = create_app(os.getenv("FLASK_ENV") or "dev")

ssl_config = SslConfig()
ssl_config.get_config("app/ssl/cert")

if __name__ == "__main__":
    db.create_all(app=app)
    socketio.run(app, ssl_context=ssl_config.get_context())
