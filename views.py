def response(issue, data, status='ok'):
    return {
        'type': 'response',
        'issue': issue,
        'status': status,
        'data': data
    }


def error_response(issue, code, message):
    return response(
        issue,
        {'code': code, 'message': message},
        'err'
    )


def notify_response(event, data):
    return {
        'type': 'notify',
        'event': event,
        'data': data
    }


class LiftApp:
    def __init__(self):
        self.ws = None
        self.actor = None

        self._ROUTES = {
            'auth': self._auth_actor,
        }

    def route(self, action):
        return self.ROUTES.get(action)

    def _auth_actor(action, data):
        pass
