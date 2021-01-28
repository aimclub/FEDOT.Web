from fedot_app import create_app
from fedot_app.server import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True, ssl_context=('fedot_app\ssl.crt', 'fedot_app\ssl.key'))