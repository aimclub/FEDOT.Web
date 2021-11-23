import json
import random

import numpy as np
from flask import Blueprint
from flask import render_template
from flask_login import login_required, current_user
from flask_socketio import send

from app import socketio

random.seed(1)
np.random.seed(1)


def custom_callback(pop):
    data = {'pipelines': []}
    for pipeline in pop:
        data['pipelines'].append([])
        for node in pipeline.nodes:
            data['pipelines'][-1].append(node.descriptive_id)
    print('json', json.dumps(data))
    send(json.dumps(data))


main = Blueprint('main', __name__, url_prefix="/")


@main.route('/', defaults={'path': ''})
@main.route('/<path:path>')
def index(path):
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    socketio.send('received message: ' + data)
    # if data == 'start_compose':
    # start_compose(custom_callback)
