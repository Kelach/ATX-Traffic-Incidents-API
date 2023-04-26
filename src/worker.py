import matplotlib.pyplot as plt
from jobs import queue, update_job_status, get_job_by_id, add_job, delete_all_jobs, rd_details
from atx_traffic import post_incidents_data,rd
import datetime
import json
import requests
import os
access_token = os.environ.get("IMAGUR_ACCESS_TOKEN", "967ffa0d6f32d43b44578bac270e080f506ae998")
imagur_auth = f'Bearer {access_token}'
imagur_image_endpoint = "https://api.imgur.com/3/image"
# worker.py
@queue.worker # decorator keeps function "live" and always reading new messages from the queue
def _execute_job(jid:str) -> None:
    """
    Retrieve a job id from the task queue and execute the job.
    Monitors the job to completion and updates the database accordingly.
    """
    job = get_job_by_id(jid)
    update_job_status(jid, "in-progress")
    print("retrieved job:", job)
    if job:
        job_type = job.get("job_type")
        if job_type == "plot-timeseries":
            try:
                try:
                    start = int(job.get('start'))
                    end = int(job.get('end'))
                    start_string = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d')
                    end_string = datetime.datetime.fromtimestamp(end).strftime('%Y-%m-%d')
                except:
                    start = None
                    end = None
                    start_string = None
                    end_string = None
                years = []
                counts = []
                for key in rd.keys():
                    try:
                        unix_time = int(rd.hget(key, 'published_date'))
                        val = rd.hget(key, 'issue_reported"')
                        year = datetime.datetime.fromtimestamp(unix_time).strftime('%Y')
                        if (start is None \
                                or start <= unix_time) \
                                and (end is None \
                                or end >= unix_time):
                            # Either increase the count bin for a year
                            # Or create a new year bin with a count of 1
                            if year in years:
                                ind = years.index(year)
                                counts[ind] = counts[ind] + 1
                            else:
                                years.append(year)
                                counts.append(1)
                    except Exception as e:
                        print(e)
                        continue
                fig, ax = plt.subplots()
                counts = [count for _, count in sorted(zip(years, counts))] # sort counts by year
                years = sorted(years) # now sort years
                ax.bar(years, counts)
                if start is None or end is None:
                    plt.title('Cases over Time')
                else:
                    plt.title(f'Cases from {start_string} to {end_string}')
                plt.savefig('plot.png') # temporarily saves in worker directory
                # now upload image to imagur, then update job status and return
                image_dict = upload_image('plot.png')
                if image_dict:
                    update_job_status(jid, 'completed', image_dict)
                else:
                    print("ERROR Uploading image to imagur, adding job back into the queue")
                    add_job(job["start"], job["end"], job["type"])
                    return 
                # with open('plot.png') as f:
                #     img = f.read()
                # update_job_status(jid, 'completed', img) # upload data to redis to return
                #@TODO replace with web link?
            except Exception as e:
                print(f"An error occcured while trying to make timeseries plot: {e}")
                update_job_status(jid, "failed")
            pass
        elif job_type == "plot-dotmap":
            try:
                try:
                    start = int(job.get('start'))
                    end = int(job.get('end'))
                    start_string = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d')
                    end_string = datetime.datetime.fromtimestamp(end).strftime('%Y-%m-%d')
                except:
                    start = None
                    end = None
                    start_string = None
                    end_string = None
                lats = []
                lons = []
                for key in rd.keys():
                    try:
                        unix_time = int(rd.hget(key, 'published_date'))
                        lat = rd.hget(key, 'latitude')
                        lon = rd.hget(key, 'longitude')
                        lat = float(lat)
                        lon = float(lon)
                        if (start is None \
                                or start <= unix_time) \
                                and (end is None \
                                or end >= unix_time):
                                    lats.append(lat)
                                    lons.append(lon)
                    except:
                        continue
                BBox = (-98.9,-97.0, 30.0, 31.1)
                mp = plt.imread('map.png')
                fig, ax = plt.subplots()
                ax.scatter(lons, lats, zorder=1, alpha= 0.2, c='b', s=10)
                ax.set_xlim(BBox[0],BBox[1])
                ax.set_ylim(BBox[2],BBox[3])
                ax.imshow(mp, zorder=0, extent = BBox, aspect= 'equal')
                if start is None or end is None:
                    plt.title('Cases over Time')
                else:
                    plt.title(f'Cases from {start_string} to {end_string}')
                plt.savefig('plot.png') # temporarily saves in worker directory
                image_dict = upload_image('plot.png')
                if image_dict:
                    update_job_status(jid, 'completed', image_dict)
                else:
                    print("ERROR Uploading image to imagur, adding job back into the queue")
                    add_job(job["start"], job["end"], job["type"])
                    return 
                # with open('plot.png') as f:
                #     img = f.read()
                # update_job_status(jid, 'completed', img) # upload data to redis to return
                #@TODO replace with web link?
            except Exception as e:
                print(f"An error occcured while trying to make dotmap plot: {e}")
                update_job_status(jid, "failed")
            pass
        elif job_type == "plot-heatmap":
            try:
                try:
                    start = int(job.get('start'))
                    end = int(job.get('end'))
                    start_string = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d')
                    end_string = datetime.datetime.fromtimestamp(end).strftime('%Y-%m-%d')
                except:
                    start = None
                    end = None
                    start_string = None
                    end_string = None
                lats = []
                lons = []
                for key in rd.keys():
                    try:
                        unix_time = int(rd.hget(key, 'published_date'))
                        lat = rd.hget(key, 'latitude')
                        lon = rd.hget(key, 'longitude')
                        lat = float(lat)
                        lon = float(lon)
                        if (start is None \
                                or start <= unix_time) \
                                and (end is None \
                                or end >= unix_time):
                                    lats.append(lat)
                                    lons.append(lon)
                    except:
                        continue
                BBox = (-98.9,-97.0, 30.0, 31.1)
                mp = plt.imread('map.png')
                fig, ax = plt.subplots()
                counts, xedges, yedges, im = ax.hist2d(lons, lats, zorder=1, alpha=0.5, cmin=1, \
                        bins=[int((BBox[1]-BBox[0])/0.01), \
                        int((BBox[3]-BBox[2])/0.01)], \
                        range=[[BBox[0], BBox[1]], \
                        [BBox[2], BBox[3]]])
                ax.set_xlim(BBox[0],BBox[1])
                ax.set_ylim(BBox[2],BBox[3])
                ax.imshow(mp, zorder=0, extent = BBox, aspect= 'equal')
                fig.colorbar(im, ax=ax)
                if start is None or end is None:
                    plt.title('Cases over Time')
                else:
                    plt.title(f'Cases from {start_string} to {end_string}')
                plt.savefig('plot.png') # temporarily saves in worker directory
                # now upload image to imagur, then update job status and return
                image_dict = upload_image('plot.png')
                if image_dict:
                    update_job_status(jid, 'completed', image_dict)
                else:
                    print("ERROR Uploading image to imagur, adding job back into the queue")
                    add_job(job["start"], job["end"], job["type"])
                    return 
                # with open('plot.png') as f:
                #     img = f.read()
                # update_job_status(jid, 'completed', img) # upload data to redis to return
                #@TODO replace with web link?
            except Exception as e:
                print(f"An error occcured while trying to make heatmap plot {e}")
                update_job_status(jid, "failed")
            pass
        elif job_type == "incidents":
            try:
                post_incidents_data()
                update_job_status(jid, "complete", {"message": "Data uploaded!"})
            except Exception as e:
                print(f"and error occured while trying to post incidents data: {e}")
                update_job_status(jid, 'failed')
            pass
        elif job_type == "delete":
            print("Recived request to delete job")
            # first we delete the images from imagur
            for jid in rd_details.keys():
                try:
                    delete_image(jid)
                except Exception as e:
                    print(f"ERROR: Unable to delete image with jid: {jid}. Error: {e}")
            # then we delete the jobs from the redis database
            try:
                delete_all_jobs()
            except Exception as e:
                print(f"ERROR: Unable to delete all jobs from rd_details: {e}")
                update_job_status(jid, 'failed')
        else:
            print('Unable to read job_type:', job_type)
            update_job_status(jid, 'failed')
            return
    ### update_job_status(jid, "completed", job)
    # fill in ...
    # the basic steps are:
    # 1) get job id from message and update job status to indicate that the job has started
    # 2) start the analysis job and monitor it to completion.
    # 3) update the job status to indicate that the job has finished.

def upload_image(path:str) -> dict:
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
    """
    # retrieving and payload to send to imagur API
    
    payload = {}
    # try to read input file, else print error
    try:
        with open(path, 'rb') as f:
            payload['image'] = f.read()
    except Exception as e:
        print(f'EXCEPTION CAUGHT...while trying to read file {path}: {e}')   
        return
    header = {'Authorization': imagur_auth}
    # try to make post request to imagur, else print errors
    try:
        response = requests.post(imagur_image_endpoint, headers=header, data=payload)
    except Exception as e:
        print(f'EXCEPTION CAUGHT...while trying to upload file {path} onto imagur: {e}')
        return
    if response.status_code == 200:
        content = json.loads(response.content.decode('utf-8'))
        return {
                'id': content['data']['id'],
                'link': content['data']['link'], 
                'deletehash': content['data']['deletehash'],
                'datetime': content['data']['datetime']
                }
    else:
        print(f'An error has occured uploading image to imagur. check header: {header}')
        return



def delete_image(jid:str) -> bool:
    '''
    Description
    -----------
        - Deletes image from imagur
    Args
    -----------
        - jid(str): Job id that can be used to retrieve job image results
    Returns
    -----------
        - Boolean True is deletion was successful else False
    '''
    # deletes each image from image db from imagur
    job = get_job_by_id(jid)
    image = job.get("results").get("image")
    print(f"successfully retrieved job: {job} with jid: {jid}")
    if image and image.get("deletehash") != None:
        header = {"Authorization": imagur_auth}
        deletehash = image.get('deletehash')
        try:
            requests.delete(f"{imagur_image_endpoint}/{deletehash}", headers=header)
        except Exception as e:
            print("ERROR deleting image from imagur: {e}")
            return False
    else:
        print(f"No delete hash attribute found in image: {image}. \
               Or the image attribute for this job: {job} does not exist")
        return False

    return True

_execute_job()
