from jobs import queue, update_job_status, get_job_by_id

# worker.py
@queue.consume # decorator keeps function "live" and always reading new messages from the queue
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

    def post_plot():
        # may need to implement time limits
        '''
        Function to upload images to imgur. 
        Returns dictionary object including link to uploaded image
        '''