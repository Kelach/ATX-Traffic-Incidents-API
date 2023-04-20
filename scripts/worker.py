from jobs import queue, rd, update_job_status, get_job_by_id
from datetime import datetime
import matplotlib.pyplot as plt

# worker.py
@queue.consume # decorator keeps function "live" and always reading new messages from the queue
def execute_job(jid):
    """
    Retrieve a job id from the task queue and execute the job.
    Monitors the job to completion and updates the database accordingly.
    """
    global rd # Get the Redis client
    job = get_job_by_id(jid)
    update_job_status(jid, "in-progress")
    if job:
        job_type = job.get("type")
        if job_type == "plot-timeseries":
            try:
                issue_reported = job.get('issue_reported"')
                years = []
                counts = []
                for key in rd.keys():
                    try:
                        unix_time = int(rd.hget(key, 'published_date'))
                        val = rd.hget(key, 'issue_reported"')
                        year = datetime.utcfromtimestamp(unix_time).strftime('%Y')
                        # Either val is the constrained issue_reported
                        # Or issue_reported is left blank
                        # In which case count everything
                        if val == issue_reported \
                                or issue_reported == "" \
                                or issue_reported is None:
                            # Either increase the count bin for a year
                            # Or create a new year bin with a count of 1
                            if year in years:
                                ind = years.index(year)
                                counts[ind] = counts[ind] + 1
                            else:
                                years.append(year)
                                counts.append(1)
                    except:
                        continue
                fig, ax = plt.subplots()
                ax.bar(years, counts)
                ax.title(f'{issue_reported} Cases over Time')
                plt.savefig('plot.png') # temporarily saves in worker directory
                with open('plot.png') as f:
                    img = f.read()
                update_job_status(jid, 'completed', img) # upload data to redis to return
                #@TODO replace with web link?    
            except:
                update_job_status(jid, "failed")
            pass
        elif job_type == "plot-dotmap":
            try:
                for key in rd.keys():
                    lat = rd.hget(key, 'latitude')
                    lon = rd.hget(key, 'longitude')
                    try:
                        lat = float(lat)
                        lon = float(lon)
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
                plt.savefig('plot.png') # temporarily saves in worker directory
                with open('plot.png') as f:
                    img = f.read()
                update_job_status(jid, 'completed', img) # upload data to redis to return
                #@TODO replace with web link?
            except:
                update_job_status(jid, "failed")
            pass
        elif job_type == "plot-heatmap":
            try:
                for key in rd.keys():
                    lat = rd.hget(key, 'latitude')
                    lon = rd.hget(key, 'longitude')
                    try:
                        lat = float(lat)
                        lon = float(lon)
                        lats.append(lat)
                        lons.append(lon)
                    except:
                        continue
                BBox = (-98.9,-97.0, 30.0, 31.1)
                mp = plt.imread('map.png')
                fig, ax = plt.subplots()
                ax.hist2d(lons, lats, zorder=1, alpha= 0.2 \
                        bins=[int((BBox[1]-BBox[0])/0.01), \
                        int((BBox[3]-BBox[2])/0.01)] \
                        range=[[BBox[0], BBox[1]], \
                        [BBox[2], BBox[3]]])
                ax.set_xlim(BBox[0],BBox[1])
                ax.set_ylim(BBox[2],BBox[3])
                ax.imshow(mp, zorder=0, extent = BBox, aspect= 'equal')
                plt.savefig('plot.png') # temporarily saves in worker directory
                with open('plot.png') as f:
                    img = f.read()
                update_job_status(jid, 'completed', img) # upload data to redis to return
                #@TODO replace with web link?
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
    ### update_job_status(jid, "completed", job) # THIS NESTS JOB WITHIN JOB

def post_plot():
    # may need to implement time limits
    '''
    Function to upload images to imgur. 
    Returns dictionary object including link to uploaded image
    '''
