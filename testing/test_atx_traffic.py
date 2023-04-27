import pytest
import time
import json
from atx_traffic import get_seconds, is_in_bounds, app
from jobs import add_job, delete_all_jobs, clear_queue

def test_get_seconds():
    assert get_seconds("2037-12-30") == float(2145765600)
    assert get_seconds("1971-01-01") == float(31557600)
    assert get_seconds("2023-01-12T09:55") == float(1673538900)
    assert get_seconds("2023-01-12T09:5") == float(1673538600)
    assert get_seconds("2023-01-12T09") == float(1673535600)

def test_is_in_bounds():
    lat = 30.286020
    lng = -97.738037
    test_incident = {"longitude": -97.822568,
                     "latitude": 30.236481, 
                     "address": None}
    assert is_in_bounds(check_address=False, incident=test_incident, radius_range=7, lng=lng, lat=lat) == True
    assert is_in_bounds(check_address=False, incident=test_incident, radius_range=5, lng=lng, lat=lat) == False
    
def test_add_job():
    assert len(add_job("12-12-2021", "12-12-2022", "incidents")) == 5
def test_delete_all_jobs():
    assert delete_all_jobs() == True

def test_clear_queue():
    assert clear_queue() == True



def test_handle_jobs():
    payload = {"start": "wewewe", "end": ""}
    assert app.test_client().post("/jobs/incidents", data=json.dumps(payload)).status_code == 404
    assert app.test_client().post("/jobs/plot/timeseries", data=json.dumps(payload)).status_code == 404
    assert app.test_client().post("/jobs/plot/dotmap", data=json.dumps(payload)).status_code == 404
    assert app.test_client().post("/jobs/plot/heatmap", data=json.dumps(payload)).status_code == 404
    
    payload["start"] = "2019-12-30"
    payload["end"] = "2020-12-30"
    
    # assert app.test_client().post("/jobs/incidents", data=json.dumps(payload)).status_code == 200
    # assert app.test_client().post("/jobs/plot/timeseries", data=json.dumps(payload)).status_code == 200
    # assert app.test_client().post("/jobs/plot/dotmap", data=json.dumps(payload)).status_code == 200
    # assert app.test_client().post("/jobs/plot/heatmap", data=json.dumps(payload)).status_code == 200

    # assert app.test_client().delete("/jobs", data=json.dumps(payload)).status_code == 200

    job_incidents = json.loads(app.test_client().post("/jobs/incidents", data=json.dumps(payload)).data.decode("utf-8"))
    job_timeseries = json.loads(app.test_client().post("/jobs/plot/timeseries", data=json.dumps(payload)).data.decode("utf-8"))
    job_dotmap = json.loads(app.test_client().post("/jobs/plot/dotmap", data=json.dumps(payload)).data.decode("utf-8"))
    job_heatmap = json.loads(app.test_client().post("/jobs/plot/heatmap", data=json.dumps(payload)).data.decode("utf-8"))

    assert job_incidents["job_type"] == "incidents"
    assert job_timeseries["job_type"] == "plot-timeseries"
    assert job_dotmap["job_type"] == "plot-dotmap"
    assert job_heatmap["job_type"] == "plot-heatmap"

    assert len(json.loads(app.test_client().get("/jobs").data)) >= 4
    assert len(json.loads(app.test_client().get("/jobs/incidents").data)) >= 1
    assert len(json.loads(app.test_client().get("/jobs/plot/timeseries").data)) >= 1
    assert len(json.loads(app.test_client().get("/jobs/plot/dotmap").data)) >= 1
    assert len(json.loads(app.test_client().get("/jobs/plot/heatmap").data)) >= 1
    assert len(json.loads(app.test_client().get("/jobs/plot").data)) >= 3

    # assert app.test_client().delete("/jobs").status_code == 200
    # assert len(json.loads(app.test_client().get("/jobs").data)) == 0 

##############################
# Test Function Tingies here #
##############################