import redis
import requests
from flask import Flask, request
import time
from geopy.geocoders import Nominatim
import geopy.distance


########################
### GLOBAL VARIABLES ###
########################
source_url = 'https://data.austintexas.gov/api/views/dx9v-zd7x/rows.json?accessType=DOWNLOAD'
redis_url = '127.0.0.1'
redis_port = 6379
redis_db = 0
flask_url = '0.0.0.0'
flask_port = 5000
EARTH_RADIUS = 3958.8 # miles


########################
### HELPER FUNCTIONS ###
########################
def message_payload(msg:str, success:bool=True, stat_code=200):
    '''
        Description:
        ------------
            - Pretty payload to return string messages in
        
        Args
        ------------
            - msg: output message for user (string)
            - success: output status of request (boolean)
            - stat_code: HTTP Status Code
        
        Returns
        ------------
            - Dictionary with debugging information
    '''
    return {"message": msg, "success":success, "status code":stat_code}

def get_redis_client(the_url: str, the_port: int, the_db: int) -> redis:
    """Returns the Redis database client.
    This function returns a Redis object permitting access to a Redis client
    via 127.0.0.1:6379. The object specifically manipulates database 0. It is
    set to decode responses from the client from bytes to Python strings.
    """
    return redis.Redis(host = the_url, port = the_port, db = the_db, \
            decode_responses = True)

def get_seconds(time_string) -> float:
    '''
    Description:
    -----------
        - Takes in a human readable string in the form "YYYY-MM-DDThh:mm:ss" and converts
            it into seconds
    
    Args:
    -----------
        - time_string: string representing human readable time in the form "YYYY-MM-DDThh:mm:ss"

    Returns:
    -----------
        - Time in seconds (float)
    
    '''
    default_time = "T00:00:00"
    # appending default time string to input time_string if
    # time is left unspecified
    offset = len(time_string) - 10
    time_string += default_time[offset:]

    return time.mktime(time.strptime(time_string, '%Y-%m-%dT%H:%M:%S'))

def is_in_bounds(**kwargs)->bool:
    '''
    Description:
    -----------
        - Checks if a given incident is within specified radius and returns a Boolean True or False
            as a result. (True if incident is within radius of a given point). Uses the haversine formula
            to calculate distance between two points.

    Args:
    -----------
        **kwargs: dict object that contains the following keys:
            - check_address: Boolean. If true, sets lat and lng equal to the ones associated with the input address 
            - inc: incident (dict)
            - radius_range (float): radius of circle boundary at which incident will be checked to be within
            - lng: longitude (float)
            - lat: lattitude (float)

    Returns:
    -----------
        - Boolean. True if input incident is within the boundary of a region having 
            a given radius (in miles) and having the center at a given
            point (longitude + lattitude or a single human readable address)
    '''
    
    # @TODO write defensive code logic for types/values inputted into function
    if kwargs["radius_range"] == float("inf"): return True # saves us some computation

    ####### MAY NEED TO REMOVE THIS CODE BELOW ###########
    if kwargs["check_address"]:
        address = kwargs["address"]  + " Austin TX" # specifying address for geopy 
        locator = Nominatim(user_agent="atx_traffic")
        location = locator.geocode(address) # obtains the locator corresponding to input address
        # retrive long + lat of location
        kwargs["lat"] = location.latitude
        kwargs["lng"] = location.longitude
    ######## MAY NEED TO REMOVE THIS CODE ABOVE ###########

    
    incident = kwargs["incident"]
    # calculating great circle distance using geopy
    coords_1 = (kwargs["lat"], kwargs["lng"])
    coords_2 = (incident["latitude"], incident["longitude"])
    try:
        distance = geopy.distance.geodesic(coords_1, coords_2).miles
    except Exception as e:
        print("Error calculating distance between two points: {e}")
        raise(e)
    return distance <= kwargs["radius_range"]


def get_query_params() -> dict:
    '''
        Description:
        -----------
            - Helper function to conveniently get all possible query parameters from a given search. 
                Include defensive programming by rejecting invalid query inputs. Lastly, 
                converst long, lat, and radius input parameters into floats, and limit + offset input
                parameters into integers.

        Args:
        -----------
            - None

        Returns:
        -----------
            - Dictionary object that pairs each query_parameter (key) with its associated value (inputted by the user).
                The dictionary keys are as follows: 
                    - "incident_type", "status", "radius", "date_range", "time_range"
                      "address", "longitude", "latitude", "limit", "offest"
    '''
    # Query Parameters
    # incident type and status don't need input checks (based on how they are currently implemented)
    incident_type = request.args.get("type", "all") # default to all incident_types
    status = request.args.get("status", "both") # defualt to both statues

    # radius
    try:
        radius = float(request.args.get("radius", float("inf"))) # default radius is infinity
        if radius < 0:
            return (message_payload("radius must be a positive number only", False, 404), 404)
    except Exception as e:
        return (message_payload(f"invalid radius parameter input: {e}", False, 404), 404)
    # start + end dates
    try:
        start_date = request.args.get("start", "1971-01-01") # default to several years in past
        get_seconds(start_date) # using get_seconds functions to check formatting of date
    except Exception as e:
        return (message_payload(f"Invalid 'start' input parameter: {e}", False, 404), 404)
    try:
        end_date = request.args.get("end", "2037-12-30") # default to several years in future
        get_seconds(end_date) # using get_seconds function to check formatting of date
    except Exception as e:
        return (message_payload(f"Invalid 'end' input parameter: {e}", False, 404), 404)
    # longitude + latitude
    try:
        longitude = float(request.args.get("lgt", -97.8961686)) # default to longitude
        lattitude = float(request.args.get("lat", 30.3079823)) # defualt to lattitude   
    except ValueError:
        return (message_payload(f"Error: longitude and latitude coordinates must be numbers only.", False, 404), 404)
    except Exception as e:
        return (message_payload(f"Error getting longitude and latitude parameters: {e}", False, 404), 404)
    finally:
        if (not -90 <= lattitude <= 90
            or not -180 <= longitude <= 180):
            msg = f"Error: longitude and latitude coordinates must be within the ranges -90 <-> 90 and -180 <-> 180 respectively"
            return (message_payload(msg, False, 404), 404)
    # offset + limit
    try:
        offset = int(request.args.get("offset", 0)) # default to no offset
        limit = int(request.args.get("limit", 2**32 - 1)) # default to no limit (max int value)
    except ValueError:
        return (message_payload(f"Error: limit and offset input parameters must be positive integers only",False, 404), 404)
    except Exception as e:
        return (message_payload(f"Error getting limit and offset parameters: {e}", False, 404), 404)
    finally:
        if offset < 0 or limit < 0:
            return (message_payload(f"Error: limit and offset input parameters must be positive integers only",False, 404), 404)
        
    # need to check address, but may not include addresses at all
    address = request.args.get("address", None) # default None address
    
    

    return {"incident_type":incident_type,
            "status":status,
            "radius":radius,
            "start_date":start_date,
            "end_date":end_date,
            "address":address,
            "longitude":longitude,
            "lattitude":lattitude,
            "offset":offset,
            "limit":limit
    }

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
        params = get_query_params()
        if len(params) == 2: return params # params is only of length 2 if an error as occured.
        try:
            data = []
            keys = rd.keys()
            for key in keys:
                incident = rd.hgetall(key)
                # query parameter filtering

                # filter by offest
                if params["offset"] > 0:
                    params["offset"] -= 1
                    continue
                # filtering by incident type
                if params["incident_type"].lower() != "all" and incident["issue_reported"].lower() != params["incident_type"].lower():
                    continue
                # filtering by incident status
                elif params["status"].lower() != "both" and incident["traffic_report_status"].lower() != params["status"].lower():
                    continue
                # filtering by time range
                elif not (get_seconds(params["start_date"]) <= float(incident["created_at"]) <= get_seconds(params["end_date"])):
                    continue
                # filtering by location/boundary (long and lat only)
                elif is_in_bounds(check_address=False, 
                                  incident=incident, 
                                  radius_range=params["radius"], 
                                  lng=params["longitude"], 
                                  lat=params["lattitude"], 
                                  addr=params["address"]) == False: 
                    continue
                #  "filtering" by limit
                elif len(data) >= params["limit"]:
                    break
                data.append(rd.hgetall(key))
            return data 
        except Exception as e:
            print(f'ERROR: unable to get data\n{e}')
            return f'ERROR: unable to get data\n', 400
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
            return 'Data successfully posted\n', 200
        except Exception as e:
            print(f'ERROR: unable to post data\n{e}')
            return f'ERROR: unable to post data\n', 400
    elif request.method == 'DELETE':
        try:
            rd.flushdb()
            return 'Data successfully deleted', 200
        except Exception as e:
            print(f'ERROR: unable to delete data\n{e}')
            return f'ERROR: unable to delete data\n', 400





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
