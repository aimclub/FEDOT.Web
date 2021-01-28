from fedot_app import create_app, db
from fedot_app.server import socketio

app = create_app()
db.create_all(app=create_app())

if __name__ == "__main__":
    socketio.run(app, debug=True)