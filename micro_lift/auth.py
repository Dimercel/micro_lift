from datetime import datetime as dt
from hashlib import sha3_256
import hmac


def gen_token(secret_key, uid, timestamp):
    hash_key = f'{uid}{timestamp}'.encode('utf-8')

    return hmac.new(secret_key.encode('utf-8'), hash_key, sha3_256).hexdigest()


def is_expired_token(timestamp, token_delay):
    now = dt.utcnow()
    timedelta = abs((timestamp - now).total_seconds())

    return timedelta > token_delay


def is_valid_auth(data, secret_key):
    args = [
        secret_key,
        data['uid'],
        data['timestamp']
    ]

    if data['token'] == gen_token(*args):
        return True

    return False
