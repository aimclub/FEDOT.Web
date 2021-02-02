class Auth:
    CLIENT_ID = ('873413267506-f6cnts3qkgg544gknufkrk6iambpgunl.apps.googleusercontent.com')
    CLIENT_SECRET = '05lRL4aRv8gXOWsdYaz7ns-r'
    REDIRECT_URI = 'https://localhost:5000/login/callback'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']