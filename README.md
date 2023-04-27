# Austin Traffic Incident Tracker
### Tracking the Austin Traffic as Trackers do... 

*by Ashton Cole, Kelechi Emeruwa, and Carel Soney*

## Overview of Project

### Description

This project is utilizes a real-time public traffic incident dataset from
the Austin traffic reports RSS feed to build a Flask Web API project. Users
can query information regarding live incidents in the Travis County area and view
graphs ** explain what kind of graphs ** for the month. This project uses a
pesistent Redis database for data storage and can also be deployed into a 
Kubernetes cluster. 

### Dataset

The [dataset](https://data.austintexas.gov/resource/dx9v-zd7x.json)
used for this project is updated at a regular interval of five minutes
and contains information such as:
 - incident id
 - publication date: YYYY-MM-DDTHH:MM:SSSZ
 - incident type
 - location of incident: (latitude, longitude)
 - latitude
 - longitude
 - street address: approximate location of incident
 - incident status: active vs archived

Here is a snippet of what the dataset looks like: 
```
{
  "traffic_report_id":"EBF5283D22437BB974F4248BA0EC4E90F26D32CB_1520152566000",
  "published_date":"2018-03-04T08:36:00.000Z",
  "issue_reported":"LOOSE LIVESTOCK",
  "location":"(30.256997,-97.611818)",
  "latitude":"30.256997",
  "longitude":"-97.611818",
  "address":"N Fm 973 Rd & Fm 969 Rd", 
  "traffic_report_status":"ARCHIVED",
   "traffic_report_status_date_time":"1970-01-18T14:16:00.000Z"
}
```

### File Organization

 Below is a overview of the file structure this project is comprised of: 
 
    ATX-Traffic-Incidents-API/
        ├── Docker
        │   ├── Dockerfile
        │   └── docker-compose.yaml
        ├── Kubernetes
        │   ├── prod
        │   │   ├── prod-api-deployment.yml
        │   │   ├── prod-api-service.yml
        │   │   ├── py-debug-deployment.yml
        │   │   ├── db-pvc.yml
        │   │   ├── db-service.yml
        │   │   └── wrk-deployment.yml
        │   └── test
        │       ├── test-api-deployment.yml
        │       ├── test-api-service.yml
        │       ├── test-redis-deployment.yml
        │       ├── test-redis-pvc.yml
        │       ├── test-redis-service.yml
        │       └── test-wrk-deployment.yml
        ├── README.md
        ├── help-route.txt
        └── src
            ├── atx_incidents.py
            ├── config.yaml
            ├── worker.py
            ├── jobs.py
            ├── worker.py
            └── testing
                ├── __init__.py
                └── test_atx_incidents.py

          

## Running the Application
**note: before running this project, please make sure this GitHub repository
has been cloned: 
```
git clone git@github.com:Kelach/ATX-Traffic-Incidents-API.git .
```


### Flask **are we using flask?**

To run this code on Flask, first `cd` into the directory containing the scripts, `/src`. 
Then use the following command: 
```
flask --app atx_traffic --debug run
```

In another terimnal, different routes can be called using
```
curl localhost:5000/<route_name>
```

### Docker Hub
This app has already been pushed to Docker Hub. To run, please pull the image
using the command
```
$ docker pull **whoever pushed it**/**file_name** 
```
Run the image using 
```
$ docker run -it --rm **name/file** .
```

### Dockerfile
Another way to run this project is to build your own image using the Dockerfile
provided in this repository. Use the command
```
$ docker build -t <username>/<desired_image_name> .
```
Replace <username> with your Docker Hub username.

Run the image using 
```
$ docker run -it --rm -p 5000:5000 <username>/<image_name> . 
```

### docker-compose
To launch the app using Redis, use the command 
```
$ docker-compose up -d --build flask-app
```
To terminate the app, use 
```
$ docker-compose down
```
### Kubernetes
To run the app on Kubernetes, please use the following command: 
```
$ kubectl apply -f <file_name>
```
Replace <file_name> with the deployment/pvc/service file. Please ensure each `.yml`
file has been applied. 

To confirm that the pods are running, use the command 
```
$ kubectl get pods
```
The result should be similar to the one below: 

```
test-flask-deployment-66f84d5d65-5cgpt          1/1     Running   0              97mtest-redis-deployment-7cd9bd866c-p9kq8          1/1     Running   0              114m
test-worker-deployment-5688559647-jdrtt         1/1     Running   2 (114m ago)   114m
```
In addition to the status of each of the pods, the above command should also return
the identification series of each pod. 

Please `exec` into the python debug deployment file to use the k8s cluster:
```
$ kubectl exec -it <**file_name**> -- /bin/bash
```
This will redirect you into a terminal where you may now curl each of the routes. 
```
$ kubectl exec -it py-debug-deployment-84c7b596c6-459lz -- bin/bash
root@py-debug-deployment-84c7b596c6-459lz:/#
```
Please use the following command to curl: 
```
curl flask-service:5000/<routes>
```
## Routes

| Routes | Methods | Description |
|-------| ------|-------|
|`/` | `GET` | returns a welcoming message(string) |
|`/help` | `GET` | returns description of each route (string) | 
| `/incidents`| `DELETE` `GET` | posts, retrieves, or deletes data depending on method used (list of dictionaries) |
| `/incidents/published_dates` | `GET` | returns published_dates (list) |
|`/incidents/published_dates/<published_date>`| `GET` | returns incident at a given published_date (list) | 
| `/incidents/ids` | `GET` | returns incident IDs (list) |
| `/incidents/issues`| `GET` | returns incident type (list)|
| `/incidents/published-range` | `GET` | earliest and latest published dates (string) |
| `/incidents/updated-range` | `GET` | returns range at which incidents have been updated (dict)  |
| `incidents/coordinates-range` | `GET` | minimum and maximum coordinates (dict) |
| `/jobs/plot/<jid>` | `GET` | returns job with a given job id (dict) | 
|`/jobs`| `GET` | returns all jobs listed in the redis database (dicts) |
|`/jobs/plot/heatmap`| `GET` `POST` | returns all heatmap jobs (dicts) |
|`/jobs/plot/dotmap`| `GET``POST` | returns all dotmap jobs (dicts) |
|`/jobs/plot/timeseries`| `GET` `POST`| returns all timeseries jobs (dicts) | 
|`jobs/incidents`| `GET` `POST` | returns all incidents jobs (dicts) | 
|`/jobs/plot`| `GET` | returns all plot jobs (dicts) | 

  ### Query Parameters
  | **Name**           | **Type**              | **Description**                               |
  |----------------|-------------------|-------------------------------------------------------|
  | `incident_type` | `string`          | The type of incident being reported                   |
  | `status`       | `string`          | The current status of the incident                     |
  | `radius`       | `float`           | The distance from a given point to search for incidents|
  | `start_date`   | `string` | The start date to search for incidents                 |
  | `end_date`     | `string` | The end date to search for incidents                   |
  | `longitude`    | `float`           | The longitude of the location to search for incidents  |
  | `latitude`     | `float`           | The latitude of the location to search for incidents   |
  | `limit`        | `positive integer`| The maximum number of incidents to return              |
  | `offset`       | `positive integer`| The number of incidents to skip before returning results |

## Results
using the command 
```
curl localhost:5000/incidents
```
returns the following output:
```
 {
    "address": "2500-2544 N Lamar Blvd",
    "issue_reported": "Traffic Hazard",
    "latitude": "30.290347",
    "location": "(30.290347,-97.751778)",
    "longitude": "-97.751778",
    "published_date": "1676849336",
    "traffic_report_id": "F971BD2CEB1CA67127B574C0C2BCA9B64EC0A25A_1676849336",
    "traffic_report_status": "ARCHIVED",
    "traffic_report_status_date_time": "1676850303"
  },
  {
    "address": "900-924 E St Elmo Rd",
    "issue_reported": "Crash Urgent",
    "latitude": "30.214084",
    "location": "(30.214084,-97.755602)",
    "longitude": "-97.755602",
    "published_date": "1548307003",
    "traffic_report_id": "8DA83CCF430EE7EEF2D965C4218617950BAD70AF_1548307003",
    "traffic_report_status": "ARCHIVED",
    "traffic_report_status_date_time": "1548307503"
  }
```

command:
```
curl localhost:5000/incidents/published_dates
```
returns:
```
 "1606035451",
  "1538086619",
  "1509299700",
  "1587769000",
  "1542377951",
  "1570306624",
  "1600909638",
  "1548121719",
  "1632170966",
  "1560386960",
  "1667388654",
  "1625363027",
```

command: 
```
curl localhost:5000/incidents/ids
```
return:
```
"29F4D7BD70C46FD3B021272CB02151499CC6FDA1_1600909638",
  "27858A0672AFDADFFF64D26877B49F4F5A9D2471_1548121719",
  "0104CF3B45056589309EFFD4D0889E430018B490_1632170966",
  "9D93F8113D6AC60E97D0769EFD6F167A812F620B_1560386960",
  "BFA2BEBCBE6B2347840887DDAD4A0F2CE22194D9_1667388654",
  "632047E5B2A712A7707F6B28AC722B1E706F1589_1625363027",
  "0BC39B9D01F6D3E81328CDA94EAEFE5005744CEC_1630245918",
```
the command:
```
curl localhost:5000/incidents/ids/0BC39B9D01F6D3E81328CDA94EAEFE5005744CEC_1630245918
```
returns:
```
{
  "address": "E William Cannon Dr & Circle S Rd",
  "issue_reported": "Crash Urgent",
  "latitude": "30.192728",
  "location": "(30.192728,-97.777565)",
  "longitude": "-97.777565",
  "published_date": "1630245918",
  "traffic_report_id": "0BC39B9D01F6D3E81328CDA94EAEFE5005744CEC_1630245918",
  "traffic_report_status": "ARCHIVED",
  "traffic_report_status_date_time": "1630251002"
}
```
command:
```
curl localhost:5000/incidents/issues
```
returns:
```
"Stalled Vehicle",
  "Traffic Impediment",
  "VEHICLE FIRE",
  "TRAFFIC FATALITY",
  "COLLISION/PRIVATE PROPERTY",
  "BLOCKED DRIV/ HWY",
  "FLEET ACC/ INJURY",
  "ICY ROADWAY",
  "BOAT ACCIDENT",
  "AUTO/ PED",
  "OBSTRUCT HWY",
  "HIGH WATER",
  "N / HZRD TRFC VIOL",
  "FLEET ACC/ FATAL",
  "COLLISN / FTSRA"
```
command:
```
curl localhost:5000/incidents/published-range
```
returns:
```
{
  "max": 1682439833,
  "min": 1506442260
}
```
command:
```
curl localhost:5000/incidents/updated-range
```
returns:
```
{
  "max": 1682440203,
  "min": 1520160
}
```
command
```
curl localhost:5000/incidents/coordinates-range
```
returns:
```
{
  "lat": {
    "max": 31.077333,
    "min": 30.003032
  },
  "lon": {
    "max": -97.108986,
    "min": -98.816154
  }
}
```
command
```
curl localhost:5000/incidents/published_dates/1538086619
```
returns:
```
{
  "address": "11600-11613 N Sh 130 Nb",
  "issue_reported": "Crash Urgent",
  "latitude": "30.343885",
  "location": "(30.343885,-97.592577)",
  "longitude": "-97.592577",
  "published_date": "1538086619",
  "traffic_report_id": "C60D81F35D8BE966FA0437E43F1FEFF777C6E121_1538086619",
  "traffic_report_status": "ARCHIVED",
```
