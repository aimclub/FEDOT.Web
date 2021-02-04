from app import create_app

app_url = 'http://127.0.0.1:5000'

app = create_app('test')


# @pytest.fixture(scope="session", autouse=True)
def run_server_before_test():
    app.run(debug=True)
