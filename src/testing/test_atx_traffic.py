import pytest
import time
import json
from atx_traffic import get_seconds, is_in_bounds, app

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
    
def test_handle_jobs():
    payload = {"start": "wewewe", "end": ""}
    assert app.test_client().post("/jobs/incidents", data=json.dumps(payload)).status_code == 404
    assert app.test_client().post("/jobs/plot/timeseries", data=json.dumps(payload)).status_code == 404
    assert app.test_client().post("/jobs/plot/dotmap", data=json.dumps(payload)).status_code == 404
    assert app.test_client().post("/jobs/plot/heatmap", data=json.dumps(payload)).status_code == 404
    
    payload["start"] = "2019-12-30"
    payload["end"] = "2020-12-30"
    
    assert app.test_client().post("/jobs/incidents", data=json.dumps(payload)).status_code == 200
    assert app.test_client().post("/jobs/plot/timeseries", data=json.dumps(payload)).status_code == 200
    assert app.test_client().post("/jobs/plot/dotmap", data=json.dumps(payload)).status_code == 200
    assert app.test_client().post("/jobs/plot/heatmap", data=json.dumps(payload)).status_code == 200

    assert app.test_client().get("/jobs/incidents/in-progress").data.decode("utf-8") == "incidents"
    assert app.test_client().get("/jobs/plot/heatmap/in-progress").data.decode("utf-8") == "heatmap"
    assert app.test_client().get("/jobs/plot/timeseries/in-progress").data.decode("utf-8") == "timeseries"
    assert app.test_client().get("/jobs/plot/dotmap/in-progress").data.decode("utf-8") == "dotmap"
    



##############################
# Test Function Tingies here #
##############################