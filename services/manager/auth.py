from app.db.driver import DriverJSON


def auth_required(func):
    """ Decorator for functions using login.  """

    async def wrapped(self, connection, data_json):
        is_identified = connection.fileno in self.connections
        is_authenticated = is_identified #and self.usernames[connection.fileno] == data_json['username']

        return await func(self, connection, data_json) if is_identified and is_authenticated else None

    return wrapped


def _check_password(user, password_md5, pass_storage):
    return pass_storage.read().get(user) == password_md5


def authenticate(data_json, auth_mode=None):
    pass_storage = DriverJSON('app/data/passwords.json')

    if auth_mode == 'password':
        username = data_json.get('username')
        password_md5 = data_json.get('password')
        auth_status = 'ok' if _check_password(username, password_md5, pass_storage) else 'authentication error'
    elif auth_mode == 'username':
        username = data_json.get('username')
        auth_status = 'ok' if pass_storage.read().get(username) else 'authentication error'
    else:
        auth_status = 'ok'

    return auth_status
