import json
import random

import numpy as np
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, send
from flask_swagger_ui import get_swaggerui_blueprint

from fedot_app.basic_functions import get_metrics, get_model_types, start_compose, task_type_from_id

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


@app.route('/meta/model_types/<string:task_id>', methods=['GET'])
def model_type_for_task(task_id):  # TODO add task_id
    task_type = task_type_from_id(task_id)
    model_types, _ = get_model_types(task_type)
    return jsonify(model_types)


@app.route('/meta/metrics/<string:task_id>', methods=['GET'])
def metrics_for_task(task_id):
    task_type = task_type_from_id(task_id)
    metrics = get_metrics(task_type)
    return jsonify(metrics)


@app.route('/data/datasets/all', methods=['GET'])
def datasets():
    # replace to table
    datasets = ['scoring']
    return jsonify(datasets)


@app.route('/composer/history/<string:dataset_id>', methods=['GET'])
def composer_history_for_experiment(dataset_id):  # TODO add task_id, user_key
    with open('./data/mocked_jsons/evo_history.json') as f:
        evo_history = json.load(f)
        evo_history['dataset_id'] = dataset_id
    return jsonify(evo_history)


@app.route('/chains/<string:uid>', methods=['GET'])
def chain_by_uid(uid):
    chain_json = None
    with open('./data/mocked_jsons/chain.json') as f:
        chain_json = json.load(f)
        chain_json['uid'] = uid
    if chain_json:
        return jsonify(chain_json)
    else:
        jsonify({'result': 'Failed'})


@app.route('/chains/add/{graph_structure}', methods=['POST'])
def create_chain_from_graph():
    graph = request.get_json(force=True)

    # TODO convert graph to Chain

    is_exists = True  # TODO search chain with same structure and data in database

    if is_exists:
        with open('./data/mocked_jsons/chain.json') as f:
            model = json.load(f)
            uid = model['uid']
    else:
        raise NotImplementedError('Cannot create new chain')
        # TODO save chain to database

    return jsonify({'result': 'ok', 'chain_uid': uid})


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
