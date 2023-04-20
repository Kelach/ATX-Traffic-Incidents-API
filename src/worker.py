from jobs import queue, update_job_status, get_job_by_id
import json
import requests
import os
import redis
redis_host = os.environ.get('REDIS_HOSTNAME', '127.0.0.1')
rd_image_client = redis.Redis(host=redis_host, port=6379, db=3, decode_responses=True)
access_token = os.environ.get("IMAGUR_ACCESS_TOKEN", "967ffa0d6f32d43b44578bac270e080f506ae998")
imagur_auth = "Bearer " + access_token
imagur_image_endpoint = "https://api.imgur.com/3/image"
# worker.py
@queue.worker # decorator keeps function "live" and always reading new messages from the queue
def execute_job(jid):
    """
    Retrieve a job id from the task queue and execute the job.
    Monitors the job to completion and updates the database accordingly.
    """
    job = get_job_by_id(jid)
    update_job_status(jid, "in-progress")
    if job:
        job_type = job.get("type")
        if job_type == "plot-timeseries":
            try:
                pass # insert plot-timeseries function here
            except:
                update_job_status(jid, "failed")
            pass
        elif job_type == "plot-dotmap":
            try:
                pass # insert plot-dotmap function here
            except:
                update_job_status(jid, "failed")
            pass
        elif job_type == "plot-heatmap":
            try:
                pass # insert plot-heatmap function here
            except:
                update_job_status(jid, "failed")
            pass
        elif job_type == "post-data":
            try:
                pass # insert post-data function here
            except:
                update_job_status(jid, "failed")
            pass
        else:
            print("Unable to read job_type")
            update_job_status(jid, "failed")
            return
    update_job_status(jid, "completed", job)
    # fill in ...
    # the basic steps are:
    # 1) get job id from message and update job status to indicate that the job has started
    # 2) start the analysis job and monitor it to completion.
    # 3) update the job status to indicate that the job has finished.

def upload_image(path:str) -> dict:
    # may need to implement time limits
    """
    Description
    -----------
        - Helper function to easily upload host images using the Imagur API.
    Args
    -----------
        - path: string denoting the path of the file to be uploaded. NOTE: Only png and jpg images can be uploaded to imagur

    Returns
    -----------
        - Dictionary object containing the following:
            - deletehash(str): *key used to later delete the image*.
            - link(str): *public link to image*
            - success(bool): *True if successful else false*. 
            - datetime(int): *denotes time (Epoch in seconds) of image upload. 
    Function to upload images to imgur. 
    Returns dictionary object including link to uploaded image
    """
    # retrieving and payload to send to imagur API
    
    payload = {}
    # try to read input file, else print error
    try:
        with open(path, "rb") as f:
            payload["image"] = f.read()
    except Exception as e:
        print(f"EXCEPTION CAUGHT...while trying to read file {path}: {e}")   
        return
    # retrieving clientID, endpoint to make post request to imagur API
    header = {"Authorization": imagur_auth}
    # try to upload image to imagur, else print errors
    try:
        response = requests.post(imagur_image_endpoint, headers=header, data=payload)
    except Exception as e:
        print(f"EXCEPTION CAUGHT...while trying to upload file {path} onto imagur: {e}")
    if response.status_code == 200:
        content = json.loads(response.content.decode("utf-8"))
        return {
                "id": content["data"]["id"],
                "link": content["data"]["link"], 
                "deletehash": content["data"]["deletehash"],
                "datetime": content["data"]["datetime"]
                }
    else:
        print(f"An error has occured uploading image to imagur. check header: {header}")
        return
def save_image(image:dict) -> bool:
    """
    Description
    -----------
        - Saves image onto the redis database for images
    Args
    -----------
        - image(dict): expects dictionary with same keys as that returned in post_plot()

    Returns
        - Boolean; True image was succesfully saved 
    -----------
    """    
    key = f'{image.get("id"):image.get("link")}'
    try:
        return rd_image_client.hset(key, mapping=image) 
    except Exception as e:
        print(f"ERROR CAUGHT...while trying to save image onto redis: {e}")
        return False
    # returns True if successful else an exception is raise


# this is what's returned from 'response' varible (nested dictionary with link, and delete)
"""
{'data': {'id': 'NdzPeVv', 'title': None, 'description': None, 'datetime': 1681784690, 'type': 'image/png', 'animated': False, 'width': 640, 'height': 480, 'size': 14169, 'views': 0, 'bandwidth': 0, 'vote': None, 'favorite': False, 'nsfw': None, 'section': None, 'account_url': None, 'account_id': 170252845, 'is_ad': False, 'in_most_viral': False, 'has_sound': False, 'tags': [], 'ad_type': 0, 'ad_url': '', 'edited': '0', 'in_gallery': False, 'deletehash': 'nMaeXvR53tg8fki', 'name': '', 'link': 'https://i.imgur.com/NdzPeVv.png'}, 'success': True, 'status': 200}
"""

def delete_images() -> bool:
    '''
    Description
    -----------
        - Deletes all images from redis database and imagur
    Args
    -----------
        - None
    Returns
    -----------
        - Boolean True is deletion was successful else False
    '''
    # test for possible data payload requirements 
    for key in rd_image_client.keys():
        image = rd_image_client.get(key)
        if image.get("deletehash") != None:
            header = {"Authorization": imagur_auth}
            deletehash = image['deletehash']
            try:
                requests.delete(f"{imagur_image_endpoint}/{deletehash}", headers=header)
            except:
                print("ERROR deleting image from imagur. Maybe check header, and payload requirements?")
                return False
        else:
            print(f"no delete hash attribute found in image: {image}")
            return False
    
    return True