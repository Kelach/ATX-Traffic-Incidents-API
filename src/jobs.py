import uuid
from hotqueue import HotQueue
import redis
import os
import json
# jobs.py
# JUST TO CLARIFY
# REDIS DB'S
# 0: traffic data
# 1: job queue (ids only)
# 2: job details and results (job id, status, parameters)
redis_host = os.environ.get('REDIS_HOSTNAME', '127.0.0.1')
queue = HotQueue('queue', host=redis_host, port=6379, db=1)
rd = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
rd_details = redis.Redis(host = redis_host, port = 6379, db = 2, decode_responses = False)

def _generate_jid():
    """
    Generate a pseudo-random identifier for a job.
    """
    return str(uuid.uuid4())

def _instantiate_job(jid, job_type, status, start, end):
    """
    Create the job object description as a python dictionary. Requires the job id, status,
    start and end parameters.
    """
    if type(jid) == str:
        return {'id': jid,
                'status': status,
                'job_type': job_type,
                'start': start,
                'end': end
        }
    return {'id': jid.decode('utf-8'),
            'status': status.decode('utf-8'),
            'job_type': job_type.decode("utf-8"),
            'start': start.decode('utf-8'),
            'end': end.decode('utf-8')
    }

def _save_job(job_key:str, job_dict:str):
    global rd_details
    """Save a job object in the Redis database."""
    if type(job_dict) == str:
        return rd_details.set(job_key, job_dict)
def _queue_job(jid):
    """Add a job to the redis queue."""
    queue.put(jid)

def add_job(start, end, job_type, status="submitted"):
    """Add a job to the redis queue."""
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, job_type, status, start, end)
    print(f"now saving job to redis: {job_dict}")
    _save_job(job_dict['id'], json.dumps(job_dict))
    _queue_job(job_dict['id'])
    return job_dict

def update_job_status(jid, status, results:dict=None):
    """Update the status of job with job id `jid` to status `status`."""
    print("updating job with jid:", jid)
    job = get_job_by_id(jid)
    if job:
        job['status'] = status
        if results: # adding results to job update
            job["results"] = results
        _save_job(jid, json.dumps(job))
    else :
        raise Exception(f"No Job was found in the database with the following job ID '{jid}'")
def clear_queue():
    """ Removes all items from hotqueue redis database"""
    queue.clear()
    return True

def get_job_by_id(jid):
    """"Returns Job dictionary object from redis database"""
    global rd_details
    print("gettting job using id:", jid)
    return json.loads(rd_details.get(jid)) 
def delete_all_jobs():
    """ Delete all memory in rd_details db"""
    print("now deleting jobs database")
    return rd_details.flushdb()