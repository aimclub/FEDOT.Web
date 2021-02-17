import os

from app import create_app, socketio, ssl_config, db

app = create_app(os.getenv("FLASK_ENV") or "test")
if __name__ == "__main__":
    db.create_all(app=create_app())
    socketio.run(app, ssl_context=ssl_config.get_context())
