import os

from app import create_app, socketio

app = create_app(os.getenv("FLASK_ENV") or "test")
if __name__ == "__main__":
    socketio.run(app, ssl_context=('app/ssl.crt', 'app/ssl.key'))
