from flask import Flask, request
from jobs import add_job, get_job_by_id, rd_details, delete_all_jobs
from typing import List
import redis
import requests
import time
import geopy.distance
import os
import json

########################
### GLOBAL VARIABLES ###
########################
source_url = 'https://data.austintexas.gov/api/views/dx9v-zd7x/rows.json?accessType=DOWNLOAD'
redis_url = os.environ.get('REDIS_HOSTNAME', '127.0.0.1')
redis_port = 6379
redis_db = 0
flask_url = '0.0.0.0'
flask_port = 5000
AUSTIN_LAT = 30.2672
AUSTIN_LON = -97.7431
LAT_TOL = 5
LON_TOL = 5
PLOT_LAT_MIN = 30.0
PLOT_LAT_MAX = 31.1
PLOT_LON_MIN = -98.9
PLOT_LON_MAX = -97.0

########################
### HELPER FUNCTIONS ###
########################
def message_payload(msg:str, success:bool=True, stat_code=200):
    """
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
    """
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
    """
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
    
    """
    default_time = "T00:00:00"
    # appending default time (Hours:Minutes:Seconds) string to input time_string if
    # time is left unspecified
    offset = len(time_string) - 10
    time_string += default_time[offset:]

    return time.mktime(time.strptime(time_string, '%Y-%m-%dT%H:%M:%S'))



def is_in_bounds(**kwargs)->bool:
    """
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
    """
    
    # @TODO write defensive code logic for types/values inputted into function
    if kwargs["radius_range"] == float("inf"): return True # saves us some computation

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
    """
        Description:
        -----------
            - Helper function to conveniently get all possible query parameters from a given search. 
                Uses defensive programming by rejecting invalid query inputs. Lastly, 
                converts long, lat, and radius input parameters into floats, and limit + offset input
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
            - If an error has occured a tuple of length two is returned containing an error message and a status code
    """
    # Query Parameters
    # incident type and status don't need input checks (based on how they are currently implemented)
    incident_type = request.args.get("type", "all") # default to all incident_types
    status = request.args.get("status", "all") # defualt to all statuses
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
            "limit":limit,
    }


def filter_jobs(params:dict) -> List[dict]:
    """
    Description:
    -----------
    This helper function gathers all jobs using the rd_details redis client
    and returns a list containing all the retrieved jobs

    Args:
    -----------
        type(str): One of the 4 job types currently supported by the worker.py module. 
            Namely: "incidents", "plot-timeseries", "plot-heatmap", "plot-dotmap"   
        status(str):  Status of job ("in-progress", "completed", "failed", or "submitted")

    Returns:
    -----------
        List of dictionaries (each dictionary being a job 'object')
    """
    # Lambda functions defined below help filter jobs by job_type and status
    is_type = lambda job : params['job_type'].lower() in job.get("job_type").lower() or params['job_type'].lower() == "all"
    is_status = lambda job : job.get("status").lower() == params['status'].lower() or params['status'].lower() == "all"
    print(f"found keys: {rd_details.keys()}")
    # first retrieve all jobs 
    try:
        all_jobs = [json.loads(rd_details.get(key)) 
                    for key in rd_details.keys()[params["offset"]: params["offset"] + params["limit"]]]
    except Exception as e:
        print("ERROR retrieving all jobs from redis database: {e}")
        return 
    print("retrieved jobs:", all_jobs)
    # then filter jobs by type and status and return 
    return [job for job in all_jobs if is_type(job) and is_status(job)]




def post_incidents_data()-> None:
    """
    Description:
    -----------
    Helper function to save the entire Austin traffic incidents dataset
    into the redis database

    Args:
    -----------
    
    Returns:
    -----------
    None
    """
    global rd, source_url, AUSTIN_LAT, AUSTIN_LON, LAT_TOL, LON_TOL
    the_json = requests.get(url = source_url).json()
    cols = []
    flags = []
    for col_json in the_json['meta']['view']['columns']:
        cols.append(col_json['fieldName'].replace(':', ''))
        flags.append(col_json.get('flags'))
    data = the_json['data']
    jj = 0 # Only for indexing purposes
    for datum in data:
        key = datum[cols.index('traffic_report_id')]
        for ii in range(0, len(cols)):
            if datum[ii] == None:
                datum[ii] = ''
            # Data cleaning
            if (cols[ii] == 'latitude' \
                    and datum[ii].replace('.', '').isnumeric()) \
                    and abs(float(datum[ii]) - AUSTIN_LAT) > LAT_TOL:
                        datum[ii] = ''
                        try:
                            ind = datum.index('longitude')
                            datum[ind] = ''
                            rd.hset(key, cols[ind], datum[ind])
                        except:
                            pass
            elif (cols[ii] == 'longitude' \
                    and datum[ii].replace('.', '').isnumeric()) \
                    and abs(float(datum[ii]) - AUSTIN_LON) > LON_TOL:
                        datum[ii] = ''
                        try:
                            ind = datum.index('latitude')
                            datum[ind] = ''
                            rd.hset(key, cols[ind], datum[ind])
                        except:
                            pass
            # Restrict columns to non-hidden ones
            if flags[ii] is None or 'hidden' not in flags[ii]:
                rd.hset(key, cols[ii], datum[ii])
        jj = jj + 1
        if jj % 1000 == 0:
            print(f'{jj} entries posted')




def filter_incidents_data(params:dict) -> list:
    """
    Description:
    -----------
    Helper function easily filters through entire dataset
    and returns the resulting filtered list 

    Args:
    -----------
    params(dict): Query parameters returned from the get_query_params() 
        containing the following keys:
            - "incident_type", "status", "radius", "date_range", "time_range"
                        "address", "longitude", "latitude", "limit", "offest"

    Returns:
    -----------
    List of incidents filtered based on their query parameters
    """
    global rd
    # defining lambda function to help filter data in a more readable manner
    is_incident_type = lambda params, incident: (params["incident_type"].lower() == "all" 
                                       or incident["issue_reported"].lower() == params["incident_type"].lower())
    is_incident_status = lambda params, incident: (params["status"].lower() == "all" 
                                         or  incident["traffic_report_status"].lower() == params["status"].lower())
    is_in_time_range = lambda params, incident: (get_seconds(params["start_date"]) <= float(incident["published_date"]) <= get_seconds(params["end_date"]))
    
    in_bounds = lambda params, incident: is_in_bounds(check_address=False, 
                            incident=incident, 
                            radius_range=params["radius"], 
                            lng=params["longitude"], 
                            lat=params["lattitude"], 
                            addr=params["address"])
    # filtering data using list comprehension and defined lambda functions
    print("getting data")
    data = [rd.hgetall(key) for key in rd.keys()[params["offset"]:params["offset"] + params["limit"]] # truncating + offsetting
            if is_incident_type(params, rd.hgetall(key))
             and is_incident_status(params, rd.hgetall(key))
              and is_in_time_range(params, rd.hgetall(key))
               and  in_bounds(params, rd.hgetall(key))]
    print("succcesfully got data!")
    # truncating data based on offset and limit parameters
    return data

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
        A welcome string.
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
@app.route('/incidents', methods = ['GET', 'DELETE'])
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
        If the method is POST, a text message informing the user of success. If
            there is an error, a descriptive string will be returned with a 404
            status code.
        If the method is DELETE, a text message informing the user of success.
            If there is an error, a descriptive string will be returned with a
            404 status code.
    """
    global rd
    if request.method == 'GET':
        print("getting data")
        params = get_query_params()
        if len(params) == 2: return params # params is only of length 2 if an error as occured.
        try:
            print(f"trying to filter incidents by parameters {params}")
            return filter_incidents_data(params)
        except Exception as e:
            print(f'ERROR: unable to get data\n{e}')
            return f'ERROR: unable to get data\n', 400
    elif request.method == 'POST':
        try:
            post_incidents_data()
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
        


##############################################################
##############        NOT DONE YET     #######################
##############################################################
@app.route('/incidents/<epoch>', methods = ['GET'])
def incident_at_epoch(epoch):

 """
 Description
 -----------
 This function returns the incident and all its information at a specified epoch.
 If the epoch is undetected, an error message with a 404 status code will be returned.
 Args
 ----
 epoch: user specified epoch time
 Returns
 -------
 incident: (dict) the incident and its information identified at a specified epoch 
 """
 global rd
 data = incidents()
 output = {}
 try:
  for key in data:
    if key['published_date'] == epoch:
      output.append(rd.hget(key))

  return output

 except Exception as e:
  print(f'ERROR: unable to find epoch/n{e}')
  return f'ERROR: unable to find epoch', 404



# routes to help people form queries
@app.route('/incidents/ids', methods = ['GET'])
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
        params = get_query_params()
        if len(params) == 2: return params # len of params is only 2 if an error has occured
        data = filter_incidents_data(params)
        return [incident['traffic_report_id'] for incident in data]
    except Exception as e:
        print(f'ERROR: unable to get IDs\n{e}')
        return f'ERROR: unable to get IDs', 400




@app.route("/incidents/ids/<id>")
def get_incident_by_id(id):
    global rd

    for key in rd.keys():
        try:
            incident = rd.hgetall(key)
            if incident["traffic_report_id"] == id:
                return incident
        except:
            print("Unable to retrieve ids from redis database")
            return message_payload("Unable to retrieve ids from redis database. Please try again later", False, 500), 500
    
    return message_payload("ERROR: No incident exists with the id: {id}", False, 404), 404
        




# /epochs
@app.route('/incidents/epochs', methods = ['GET'])
def epochs():

 """/epochs endpoint
 Description:
 ------------
 This function returns a list of all listed epochs in the database. If there is an error, 
 a descriptive string will  be returned with a 404 status code.

 Arguments:
 ----------
   none

 Returns:
 --------
   A list of all epochs
 """

 global rd
 params = get_query_params()

 try:
   result = []
   for key in rd.keys():
     incident = rd.hgetall(key)

     # parameter: offset
     if params['offset'] > 0:
       params['offset'] -= 1
       continue

     # parameter: incident type
     elif params['incident_type'].lower() != "all" and incident['issue_reported'].lower() !=  params['incident_type'].lower():
      continue

     # parameter: incident status
     elif params['status'].lower() != "both" and incident['traffic_report_status'].lower() != params['status'].lower():
       continue

     # parameter: limit
     elif len(result) >= params['limit']:
       break

     result.append(rd.hget(key, 'published_date'))
   return result

 except Exception as e:
   print (f'ERROR: unable to retrieve epochs/n{e}')
   return f'ERROR: unable to retrieve epochs', 400




# /issues
@app.route('/incidents/issues', methods = ['GET'])
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
        for key in rd.keys():
            value = rd.hget(key, 'issue_reported')
            if value not in result:
                result.append(value)
        return result
    except Exception as e:
        print(f'ERROR: unable to get IDs\n{e}')
        return f'ERROR: unable to get IDs', 400





# /published-range
@app.route('/incidents/published-range', methods = ['GET'])
def published_range():
    """/published-range endpoint

    Description
    -----------
    This function returns the minimum and maximum published dates in the
    database. If there is an error, a descriptive string will be returned with
    a 404 status code.

    Args:
    ----------
        None

    Returns:
    ----------
        The minimum and maximum published dates as a dictionary, entitled min
        and max, respectively.
    """
    global rd
    try:
        the_min = float('inf')
        the_max = float('-inf')
        for key in rd.keys():
            value = int(rd.hget(key, 'published_date'))
            if value < the_min:
                the_min = value
            if value > the_max:
                the_max = value
        return {'min' : the_min, 'max' : the_max}
    except Exception as e:
        print(f'ERROR: unable to get published range\n{e}')
        return f'ERROR: unable to get published range', 400





# /updated-range
@app.route('/incidents/updated-range', methods = ['GET'])
def updated_range():
    """/updated-range endpoint

    Description
    -----------
    This function returns the minimum and maximum updated dates in the
    database. If there is an error, a descriptive string will be returned with
    a 404 status code.

    Args:
    ----------
        None

    Returns:
    ----------
        The minimum and maximum updated dates as a dictionary, entitled min
        and max, respectively.
    """
    global rd
    try:
        the_min = float('inf')
        the_max = float('-inf')
        for key in rd.keys():
            value = int(rd.hget(key, 'traffic_report_status_date_time'))
            if value < the_min:
                the_min = value
            if value > the_max:
                the_max = value
        return {'min' : the_min, 'max' : the_max}
    except Exception as e:
        print(f'ERROR: unable to get updated range\n{e}')
        return f'ERROR: unable to get updated range', 400





# /coordinates-range
@app.route('/incidents/coordinates-range', methods = ['GET'])
def coordinates_range():
    """/coordinates-range endpoint

    Description
    -----------
    This function returns the minimum and maximum coordinates in the
    database. If there is an error, a descriptive string will be returned with
    a 404 status code.

    Args:
    ----------
        None

    Returns:
    ----------
        The minimum and maximum latitudes and longitudes as a dictionary,
        grouped first by coordinate type, then min or max.
    """
    global rd
    try:
        min_lat = float('inf')
        max_lat = float('-inf')
        min_lon = float('inf')
        max_lon = float('-inf')
        for key in rd.keys():
            lat = rd.hget(key, 'latitude')
            lon = rd.hget(key, 'longitude')
            try:
                lat = float(lat)
                lon = float(lon)
            except:
                continue
            if lat < min_lat:
                min_lat = lat
            if lat > max_lat:
                max_lat = lat
            if lon < min_lon:
                min_lon = lon
            if lon > max_lon:
                max_lon = lon
        return { \
                'lat' : {'min' : min_lat, 'max' : max_lat}, \
                'lon' : {'min' : min_lon, 'max' : max_lon} \
                }
    except Exception as e:
        print(f'ERROR: unable to get coordinates range\n{e}')
        return f'ERROR: unable to get coordinates range', 400




@app.route("/jobs", methods=["GET", "DELETE"])
def jobs():
    """
    Returns all jobs currently listed in rd_details
    """
    if request.method == "GET":
        # try to get params
        try:
            params = get_query_params()
        except Exception as e:
            print(f"Unable to get query parameters: {e}")
            return message_payload("Unable to retrieve any jobs from the database", False, 500), 500           
        params["job_type"] = "all"
        # then try to get filtered jobs and return the jobs if no error has occured
        jobs = filter_jobs(params) 
        if jobs is None:
            return message_payload("Unable to retrieve any jobs from the database", False, 500), 500
        return jobs
    elif request.method == "DELETE":
        try:
            print("trying to delete job...")
            job = add_job("1971-01-01", "2037-12-30", "delete")
        except Exception as e:
            print(f"Unable add job: {e}")
            return message_payload("Unable to delete jobs", False, 500), 500
        if job:
            return message_payload("Deleting all jobs and their results from memory...")
        else:
            return message_payload("Unable to delete jobs", False, 500), 500





# all routes related to getting/posting jobs
@app.route("/jobs/plot/heatmap", methods=["POST", "GET"])
@app.route("/jobs/plot/dotmap", methods=["POST", "GET"])
@app.route("/jobs/plot/timeseries", methods=["POST", "GET"])
@app.route("/jobs/incidents", methods=["POST", "GET"])
@app.route("/jobs/plot", methods=["GET"])
def handle_jobs():
    """
    Description:
    -----------
    Handler function to server all routes related to getting and posting new jobs.
        Supports 'limit', 'offest', 'status' query parameters.

    Args:
    -----------

    Returns:
    -----------
    """
    path = request.path.split("/") # getting path helps decern what type of request is being received
    # if user wants to post a job
    if request.method == "POST":
        # try to get inputted job from user. and check that it's valid
        try:
            job = request.get_json(force=True)
            job['start'] = get_seconds(job.get('start', '1971-01-01'))
            job['end'] = get_seconds(job.get('end', '2037-12-30'))
        # catch invalid end/start string dates
        except ValueError:
            print(f"ERROR: invalid start date: {job['start']} or end date: {job['end']}") 
            return message_payload(f"ERROR: invalid start date: {job['start']} \
or end date: {job['end']}. \
See /help for more assistance", False, 404), 404
        # catch any other unexpected errors
        except Exception as e:
            print(f"ERROR: an unexpected error has occured {e}")
            return message_payload(f"ERROR: Unable to fufill job request: {e}", False, 500), 500
        job_type = path[-1] if path[-2] != "plot" else "plot-" + path[-1] # getting job_type from route path
        # add job to queue based on job_type (aka...path of the request)
        print(f"adding job: {job}")
        return json.dumps(add_job(job["start"], job["end"], job_type))
    # else if user wants to get jobs
    elif request.method == "GET":
        params = get_query_params()
        if len(params) == 2: return params # params is only a length of 2 if an error has occured

        # retriving path to determine job_type
        params["job_type"] = path[-1]
        print("job type is: ", params["job_type"])
        jobs = filter_jobs(params)
        print("found jobs: ", jobs)
        if jobs is not None:
            return jobs
        else:
            return message_payload("Unable get jobs", False, 500), 500





@app.route("/jobs/jids/<jid>", methods=["GET"])
def get_unique_job(jid):
    # try to get job by id
    # then return restults if they exists
    try:
        job = get_job_by_id(jid)
    except Exception as e:
        return message_payload(f"Error: Unable to find job with job id \
                               '{jid}': {e}", True, 404), 404
    if job:
        return job
    else:
        return message_payload(f"Job with jid: {jid} does not exist")





@app.route("/jobs/jids", methods=["GET"])
def get_job_ids():
    try:
        params = get_query_params()
        params["job_type"] = "all"
        jobs = filter_jobs(params)
    except Exception as e:
        print(f"An error has occured while trying to get job ids: {e}")
        return message_payload(f"Unable to get job ids, please try again later: {e}", False, 500)
    return [job["id"] for job in jobs]





@app.route("/help", methods=["GET"])
def help():
    """
    API + jobs help info...
    """
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
