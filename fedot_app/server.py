import json
import random

import numpy as np
from flask import Flask, jsonify
from flask import render_template
from flask_socketio import SocketIO
from flask_socketio import send

from fedot_app.basic_functions import start_compose

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


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/models', methods=['GET'])
def models():
    return jsonify()


@app.route('/models/<int:id>', methods=['GET'])
def modelById(id):
    return jsonify({})


@app.route('/model/<string:name>', methods=['POST'])
def addModelByName(name):
    # modesList.append(name)
    return jsonify({'message': 'New model added'})


@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    socketio.send('received message: ' + data)
    if data == 'start_compose':
        start_compose(custom_callback)
