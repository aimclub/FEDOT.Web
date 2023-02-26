import json
import random

import numpy as np
from flask import Blueprint
from flask import render_template
from flask_login import login_required, current_user

random.seed(1)
np.random.seed(1)

main = Blueprint('main', __name__, url_prefix="/")


@main.route('/', defaults={'path': ''})
@main.route('/<path:path>')
def index(path):
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)
