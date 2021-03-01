from app.api.auth.service import find_user_by_email, generate_token, save_changes
from app.web.auth.model import User


def clear_db():
    User.query.filter(User.email == "test_user").delete()
    save_changes()


def test_sing_up_endpoint(client):
    body = {
        'email': "test_user",
        'password': "test_user_password"
    }

    response = client.post(f'api/token/signup', json=body)
    data = response.json
    assert response.status_code == 200
    assert data['message'] == "registration successful"

    response = client.post(f'api/token/signup', json=body)
    data = response.json
    assert response.status_code == 400
    assert data['message'] == "user already exists"


def test_get_token_endpoint(client):
    body = {
        'email': "test_user",
        'password': "test_user_password"
    }

    response = client.post(f'api/token/get_token', json=body)
    data = response.json
    user = find_user_by_email(body['email'])
    token = generate_token(user.id)
    assert response.status_code == 200
    assert data['token_value'] == token

    invalid_body = {
        'email': "test_user_invalid",
        'password': "test_user_password"
    }
    response = client.post(f'api/token/get_token', json=invalid_body)
    data = response.json
    assert response.status_code == 401
    assert data['message'] == "check login data"

    clear_db()
