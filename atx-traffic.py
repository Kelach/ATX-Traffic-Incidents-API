import redis
import requests
from flask import Flask, request




########################
### GLOBAL VARIABLES ###
########################
source_url = 'https://data.austintexas.gov/api/views/dx9v-zd7x/rows.json?accessType=DOWNLOAD'
redis_url = '127.0.0.1'
redis_port = 6379
redis_db = 0
flask_url = '0.0.0.0'
flask_port = 5000





def get_redis_client(the_url: str, the_port: int, the_db: int) -> redis.Redis:
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
    Description
    -----------

    Thus function returns the default endpoint.

    Args:
    -----------
        None

    Returns:
    -----------
        An welcome string.
    """
    return 'Welcome to atx-traffic!'





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
    
    Description
    -----------
    This function either returns incident data, subject to certain query
    parameters, updates the database with the latest source data, or clears
    the database, depending on if the HTTP request method is GET, POST, or
    DELETE, respectively.

    Args:
    -----------
        None

    Returns:
    -----------
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
                    if datum[ii] == None:
                        datum[ii] = ''
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
@app.route('/ids', methods = ['GET'])
def ids():
    """/ids endpoint
    Description
    -----------
    This function returns a list of all incident IDs in the database. If there
    is an error, a descriptive string will be returned with a 404 status code.

    Args:
    -----------
        None

    Returns:
    -----------
        A list of all incident IDs as strings.
    """
    global rd
    try:
        result = []
        keys = rd.keys()
        for key in keys:
            result.append(rd.hget(key, 'traffic_report_id'))
        return result
    except Exception as e:
        print(f'ERROR: unable to get IDs\n{e}')
        return f'ERROR: unable to get IDs', 400





# /issues
@app.route('/issues', methods = ['GET'])
def issues():
    """/issues endpoint

    Description
    -----------
    This function returns a list of all unique issues reported in the
    database. If there is an error, a descriptive string will be returned with
    a 404 status code. 

    Args:
    -----------
        None

    Returns:
        A list of all incident issues as strings.
    """
    global rd
    try:
        result = []
        keys = rd.keys()
        for key in keys:
            value = rd.hget(key, 'issue_reported')
            if value not in result:
                result.append(value)
        return result
    except Exception as e:
        print(f'ERROR: unable to get IDs\n{e}')
        return f'ERROR: unable to get IDs', 400





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
