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

### Files

 This project contains the following: 
 
 1. Docker (2)
    * Dockerfile
    * docker-compose.yml

 2. kubernetes/test (7)
   * py-debug-deployment.yml
   * test-api-deployment.yml
   * test-api-service.yml
   * test-redis-deployment.yml
   * test-redis-pvc.yml
   * test-redis-service.yml
   * test-wrk-deployment.yml
 
 3. src (5)
   * testing (1)
     * test_atx_traffic.py
   * atx_traffic.py
   * config.yaml
   * jobs.py
   * map.png
   * worker.py
 
 4. help-route.txt

 5. README

## Running the Application
**note: before running this project, please make sure this GitHub repository
has been cloned: 
```
git clone git@github.com:Kelach/ATX-Traffic-Incidents-API.git .
```


### Flask **are we using flask?**

**empty.........**

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

**insert sc of code**

In addition to the status of each of the pods, the above command should also return
the identication series of each pod. 

Please `exec` into the python debug deployment file to use the k8s cluster:
```
$ kubectl exec -it <**file_name**> -- /bin/bash
```
This will redirect you into a terminal where you may now curl each of the routes. 

## Routes

| Routes | Methods | Description |
|-------| ------|-------|
|`/` | `GET` | returns a welcoming message(string) |
|`/help` | `GET` | returns description of each route (string) | 
| `/incidents`| `POST` `GET` `DELETE` | posts, retrieves, or deletes data depending on method used (list of dictionaries) |
| `/epochs` | `GET` | returns epochs (list) |
| `/ids` | `GET` | returns incident IDs (list) |
| `/issues`| `GET` | returns incident type (list)|
| `/published-range` | `GET` | earliest and latest published dates (string) |
| `/updated-range` | `GET` | what's the diff btwn this one and published-range?? |
| `/coordinates-range` | `GET` | minimum and maximum coordinates (dict) |
| `/jobs/plot` | `GET` | ...... |
| `/jobs/plot/<jid>` | `GET` | ....... | 

## Results
