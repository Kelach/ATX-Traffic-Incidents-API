import redis
import requests
from flask import Flask, request





source_url = 'TBD'
redis_url = 'TBD'
redis_port = 6379
redis_db = 0
flask_url = '0.0.0.0'
flask_port = 5000





def get_redis_client(the_url: str, the_port: int, the_db: int) -> Redis:
    """Returns the Redis database client.
    This function returns a Redis object permitting access to a Redis client
    via 127.0.0.1:6379. The object specifically manipulates database 0. It is
    set to decode responses from the client from bytes to Python strings.
    """
    return redis.Redis(host = the_url, port = the_port, db = the_db, \
            decode_responses = True)





app = Flask(__name__)
rd = get_redis_client(redis_url, redis_port, redis_db)





#################
### ENDPOINTS ###
#################





@app.route('/', methods = ['GET'])
def nil():
    """/ endpoint

    Thus function returns the default endpoint.

    Args:
        None

    Returns:
        An empty string.
    """
    return '';





####################
### STARTUP CODE ###
####################





if __name__ == '__main__':
    app.run(host = flask_url, debug = True)
