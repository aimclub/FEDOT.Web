from werkzeug.serving import make_ssl_devcert

from app import db, create_app

if __name__ == "__main__":
    db.create_all(app=create_app())
    make_ssl_devcert('./ssl', host='localhost')
