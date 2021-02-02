import json
import random

import numpy as np
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, send
from flask_swagger_ui import get_swaggerui_blueprint

from app import socketio
from app.mod_base.service import start_compose

random.seed(1)
np.random.seed(1)


def custom_callback(pop):
    data = {'chains': []}
    for chain in pop:
        data['chains'].append([])
        for node in chain.nodes:
            data['chains'][-1].append(node.descriptive_id)
    print('json', json.dumps(data))
    send(json.dumps(data))


main = Blueprint('main', __name__, url_prefix="/")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.register_blueprint(swaggerui_blueprint)

socketio = SocketIO(app, async_mode='threading')

models_list = ['model_1', 'model_2', 'model_3']


@app.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    socketio.send('received message: ' + data)
    if data == 'start_compose':
        start_compose(custom_callback)
