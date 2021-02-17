import os


class Auth:
    CLIENT_ID = os.getenv("CLIENT_ID", "Client ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "Client secret")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    AUTH_URI = os.getenv("AUTH_URI")
    TOKEN_URI = os.getenv("TOKEN_URI")
    USER_INFO = os.getenv("USER_INFO")
    SCOPE = ['profile', 'email']
