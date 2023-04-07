import pytest
import time
from atx_traffic import get_seconds, is_in_bounds

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
    
    # Testing for address inputs (may not need)
    # test_incident["address"] = "3900-3923 Southwest Pkwy"
    # assert is_in_bounds(check_address=True, incident=test_incident, radius_range=5.7, address="W 24th Street") == True
    # assert is_in_bounds(check_address=True, incident=test_incident, radius_range=5.6, address="W 24th Street") == False
    
##############################
# Test Function Tingies here #
##############################