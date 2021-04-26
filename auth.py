from hashlib import sha3_256
import hmac


def gen_token(secret_key, uid, timestamp):
    hash_key = f'{uid}{timestamp}'.encode('utf-8')

    return hmac.new(secret_key.encode('utf-8'), hash_key, sha3_256).hexdigest()
