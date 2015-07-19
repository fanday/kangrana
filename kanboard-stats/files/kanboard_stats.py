#coding=utf-8

import requests
import logging
import json
import sys
import os
from influxdb import InfluxDBClient
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger("kanboard")

class RPCRequest:
    def __init__(self, host_url, auth_user, auth_key):
        self.host_url = host_url
        self.auth_user = auth_user
        self.auth_key = auth_key
        self.headers = {"content-type": "application/json"}
    def doRequest(self,payload):
        response = requests.post(
        self.host_url,
        data=json.dumps(payload),
        headers= self.headers,
        auth=(self.auth_user, self.auth_key)
        )

        if response.status_code == 401:
            logger.warning("Authentication failed")
            return None
        else:
            result = response.json()
            return result
        
def getTaskTimeSpent(tasks, task_id):
    for task in tasks:
        if(task["id"] == task_id ):
            return task["time_spent"]
    return 0


def kanboard_stats(host_url,auth_user,auth_key,project_id,project_name,db_client):
    
    req = RPCRequest(host_url, auth_user, auth_key)

    payload = {
        "method":"getBoard",
        "jsonrpc":"2.0",
        "id":1,
        "params":[
        project_id
        ]
    }
    
    rsp_board = req.doRequest(payload)
    
   
        
    payload = {
        "method":"getActiveSwimlanes",
        "jsonrpc":"2.0",
        "id":1,
        "params": [
        project_id
        ]
    }

    rsp_sw = req.doRequest(payload)
    
        
    payload = {
        "method":"getAllTasks",
        "jsonrpc":"2.0",
        "id":1,
        "params":{
        "project_id":project_id,
        "status_id":1
        }
    }

    rsp_tasks = req.doRequest(payload)
    
    #计算每列的复杂度
    sws = rsp_board["result"]
    for sw in sws :
        logger.debug("swimlane is:%s",sw["name"])
        for colum in sw["columns"] :
            logger.debug("column name:%s",colum["title"])
            logger.debug("column score:%s",colum["score"])
            time_remain = 0.0
            for task in colum["tasks"]:
                est = float(task["time_estimated"])
                spent = float(getTaskTimeSpent(rsp_tasks["result"], task["id"]))
                remain = est-spent
                time_remain += remain
            logger.debug("total remain is:%s",time_remain)
	    json_body = [
    	        {
                  "measurement": project_name,
                  "tags": {
                     "swimlane": sw["name"],
		     "column":colum["title"]
                  },
                  
                  "fields": {
                  "score": colum["score"],
                  "time_remain":time_remain
                  }
                }
            ]
    	    
            db_client.write_points(json_body)
    
	
          
def quote_send_sh_job(): 
    host_url = os.environ.get('HOSTURL')
    if host_url ==None:
        logger.warn("can not get host url")
        return
    logger.info("host url is:%s", host_url)

    auth_key = os.environ.get('AUTHKEY')
    if auth_key ==None:
        logger.warn("can not get auth key")
        return
    logger.info("auth key is:%s", auth_key)

    db_host = os.environ.get('DATABASEHOST')
    if db_host == None:
        logger.warn("can not get database host")
        return
    logger.info("database host is:%s", db_host)
    
    db_port = os.environ.get('DATABASEPORT')
    if db_port == None:
        logger.warn("can not get database port")
        return
    logger.info("database port is:%s", db_port)

    db_user = os.environ.get("DATABASEUSER")
    if db_user == None:
        logger.warn("can not get database user")
        return
    logger.info("database user is:%s", db_user)

    db_pwd = os.environ.get("DATABASEPWD")
    if db_pwd == None:
        logger.warn("can not get database password")
        return
    logger.info("database password is:%s", db_pwd)
    auth_user =  "jsonrpc"
    database = 'kanboard'
    client = InfluxDBClient(db_host, db_port, db_user, db_pwd, database)
    databases = client.get_list_database()
    is_db_exist = False
    logger.debug(databases)
    for db in databases:
	if(db['name'] == database):
            is_db_exist = True
            break;
    if is_db_exist == False:
        client.create_database(database)

    payload = {
        "method": "getAllProjects",
        "jsonrpc": "2.0",
        "id": 1,
    }
    req = RPCRequest(host_url, auth_user, auth_key)
    rsp = req.doRequest(payload)
    
    projects = rsp['result']
    
    for project in projects:
        kanboard_stats(host_url,auth_user,auth_key,project['id'],project['name'],client)
        
    
        

if __name__ == "__main__":
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',)  
    file_handler = logging.FileHandler("kanboard.log")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stderr)  
    logger.addHandler(file_handler)  
    logger.addHandler(stream_handler)
    logger.debug("debug message") 
    interval = os.environ.get("INTERVAL")
    if interval == None:
	logger.warn("can not get interval so user default time interval")
        interval = 10
    sc=BlockingScheduler()
    sc.add_job(quote_send_sh_job, "interval",minutes=int(interval))
    sc.start()
    #quote_send_sh_job()
