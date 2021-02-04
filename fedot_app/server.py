import json
import random

import numpy as np
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, send
from flask_swagger_ui import get_swaggerui_blueprint

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


SWAGGER_URL = '/app/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "FEDOT web"
    }
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.register_blueprint(swaggerui_blueprint)

socketio = SocketIO(app, async_mode='threading')

models_list = ['model_1', 'model_2', 'model_3']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/models', methods=['GET'])
def models():
    return jsonify(models_list)


@app.route('/models/<int:id>', methods=['GET'])
def modelById(id):
    return jsonify(models_list[id])


@app.route('/add_model', methods=['POST'])
def addModelByName():
    data = request.get_json(force=True)
    models_list.append(data['name'])
    return jsonify({'result': 'ok'})


@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    socketio.send('received message: ' + data)
    if data == 'start_compose':
        start_compose(custom_callback)
