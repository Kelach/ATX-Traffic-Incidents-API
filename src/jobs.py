import uuid
from hotqueue import HotQueue
import redis
import os
# jobs.py
redis_host = os.environ.get('REDIS_HOSTNAME', '127.0.0.1')
queue = HotQueue('queue', host=redis_host, port=6379, db=1)
rd = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

def _generate_jid():
    """
    Generate a pseudo-random identifier for a job.
    """
    return str(uuid.uuid4())

def _generate_job_key(jid):
    """
    Generate the redis key from the job id to be used when storing, retrieving or updating
    a job in the database.
    """
    return 'job.{}'.format(jid)

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

def _save_job(job_key, job_dict):
    global rd
    """Save a job object in the Redis database."""
    rd.hset(job_key, mapping=job_dict)

def _queue_job(jid):
    """Add a job to the redis queue."""
    queue.put(jid)

def add_job(start, job_type, end, status="submitted"):
    """Add a job to the redis queue."""
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, job_type, status, start, end)
    _save_job(job_dict['id'], job_dict)
    _queue_job(job_dict['id'])
    return job_dict

def update_job_status(jid, status, results:dict=None):
    """Update the status of job with job id `jid` to status `status`."""
    job = get_job_by_id(jid)
    if job:
        job['status'] = status
        if results: # adding results to job update
            job['results'] = results
        _save_job(_generate_job_key(jid), job)
    else :
        raise Exception("No Job was found in the database with the following job ID '{jid}'")
def get_job_by_id(jid):
    """"Returns Job dictionary object from redis database"""
    global rd
    return rd.hget(jid)

