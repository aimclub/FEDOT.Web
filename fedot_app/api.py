from flask import jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
api = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "FEDOT web"
    }
)

models_list = ['model_1', 'model_2', 'model_3']


@api.route('/models', methods=['GET'])
def models():
    return jsonify(models_list)


@api.route('/models/<int:id>', methods=['GET'])
def modelById(id):
    return jsonify(models_list[id])


@api.route('/add_model', methods=['POST'])
def addModelByName():
    data = request.get_json(force=True)
    models_list.append(data['name'])
    return jsonify({'result': 'ok'})
