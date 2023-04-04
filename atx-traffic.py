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
        An welcome string.
    """
    return 'Welcome to atx-traffic!';





# /incidents GET POST DELETE with optional query refinement parameters
#     OR/AND toggle???
#     id (string)
#     issue (string)
#     published (date range -- strings?)
#     reported (date range -- strings?)
#     latitude/longitude ranges (double)
#     latitude/longitude center and radius (double)
#     address contains (string)
#     status (string)
@app.route('/incidents', methods = ['GET', 'POST', 'DELETE'])
def incidents():
    """/incidents endpoint

    This function either returns incident data, subject to certain query
    parameters, updates the database with the latest source data, or clears
    the database, depending on if the HTTP request method is GET, POST, or
    DELETE, respectively.

    Args:
        None

    Returns:
        If the method is GET, a list of dictionaries representing each entry in
            the database. If there is an error, a descriptive string will be
            returned with a 404 status code. Note that sparse attributes are
            excluded.
        If the method is SET, a text message informing the user of success. If
            there is an error, a descriptive string will be returned with a 404
            status code.
        If the method is DELETE, a text message informing the user of success.
            If there is an error, a descriptive string will be returned with a
            404 status code.
    """
    global rd, source_url
    if request.method == 'GET':
        try:
            data = []
            keys = rd.keys()
            for key in keys:
                # @TODO implement query parameters 
                data.append(rd.hgetall(key))
            return data
        except Exception as e:
            print(f'ERROR: unable to get data\n{e}')
            return f'ERROR: unable to get data', 400
    elif request.method == 'POST':
        try:
            the_json = requests.get(url = source_url).json()
            cols = []
            for col_json in the_json['meta']['view']['columns']:
                cols.append(col_json['fieldName'].replace(':', ''))
            data = the_json['data']
            for datum in data:
                key = datum[cols.index('traffic_report_id')]
                for ii in range(0, len(cols)):
                    rd.hset(key, cols[ii], datum[ii])
            return 'Data successfully posted', 200
        except Exception as e:
            print(f'ERROR: unable to post data\n{e}')
            return f'ERROR: unable to post data', 400
    elif request.method == 'DELETE':
        try:
            rd.flushdb()
            return 'Data successfully deleted', 200
        except Exception as e:
            print(f'ERROR: unable to delete data\n{e}')
            return f'ERROR: unable to delete data', 400





# routes to help people form queries
# /ids
# /issues
# /published-range
# /reported-range
# /coordinates-range
# /addresses ... way they're recorded is irrecular
# /statuses
# /plot/dotmap
#     issue (string)
#     published (date range -- strings?)
#     reported (date range -- strings?)
#     latitude/longitude ranges (double)
#     status (string)
#     colorby (string...none, issue, or status)
# /plot/heatmap
#     issue (string)
#     published (date range -- strings?)
#     reported (date range -- strings?)
#     latitude/longitude ranges (double)
#     status (string)
# /plot/timeseries
# aaaaaaaaaaaaaaa
# /help
# Can write a text file that Python displays





####################
### STARTUP CODE ###
####################





if __name__ == '__main__':
    app.run(host = flask_url, debug = True)
