import os.path

from werkzeug.serving import make_ssl_devcert


class SslConfig(object):

    def __init__(self):
        self.ssl_cert = None
        self.ssl_key = None

    def create_dummy(self, name):
        make_ssl_devcert(name, host='localhost')
        self.ssl_cert = name + ".crt"
        self.ssl_key = name + ".key"
        print(f"Dummy certificate with name '{name}' created")

    def get_config(self, name):
        cert_file = name + ".crt"
        key_file = name + ".key"
        if os.path.exists(key_file) and os.path.exists(cert_file):
            self.ssl_cert = cert_file
            self.ssl_key = key_file
            print(f"Certificate with name '{name}' already exists")
            return self
        else:
            self.create_dummy(name)
            return self

    def get_context(self):
        return self.ssl_cert, self.ssl_key
