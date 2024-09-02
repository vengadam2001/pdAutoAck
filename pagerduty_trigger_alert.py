#Project by Thiruvengadam.S
#About:
# This prioject was created since it we were getting many auto resolving alerts which were not an actual problem. so based on the time an alert was triggered. it will categorise the alert in to 4 states.
# First state is acknowledged in white color (initial 15 mins default) 
# Next 1 hr will be in yellow color 
# Then it will move to red until the alert is resolved.
# Finally when the alert is resolved it will move to green state.

import os
import requests
import time
import playsound
from tabulate import tabulate
from threading import Thread
import threading
import datetime
import json
import pickle as pk
from pd_cred import pd_user_id, headers
import sys
import time

YELLOW_TIME = 15  # after this duration of time in minutes alert moves to yellow state.
RED_TIME = 60 # after this duration of time in minutes alerts moves to red state.
GREEN =   "\033[38;2;0;255;150m"
RED =     "\033[38;2;255;0;0m"
ORANGE =  "\033[38;2;255;150;0m"     
END =     "\033[0m"

url = "https://fourkites-inc.pagerduty.com/api/v1/incidents/count?statuses[]=triggered&statuses[]=acknowledged&user_ids[]={}&date_range=all&urgencies[]=high&with_suppressed=true".format(pd_user_id)
url_incidents = "https://fourkites-inc.pagerduty.com/api/v1/incidents?statuses[]=triggered&user_ids[]={}&date_range=all&urgencies[]=high&with_suppressed=true".format(pd_user_id)

payload = {}
incident_dict = {}

autoAcknowledge = False
kill = False 

def print_l(a,endl):
  file = open("pd_logs.txt",mode='a')
  # file. (threading.current_thread(),a)
  print(threading.current_thread(), a, endl= endl)
  file.close()
  
def print_l(a):
  file = open("pd_logs.txt",mode='a')
  file.write(str(threading.current_thread()))
  file.write(str(a))
  print(threading.current_thread(), a)
  file.close()

def convert_time_to_ist(utc_time_str):
  utc_time = datetime.datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S%z")
  ist_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
  ist_time = utc_time.astimezone(ist_timezone)
  return ist_time

def get_time_from_str(ist_time_str):
  ist_time = datetime.datetime.strptime(ist_time_str, "%d-%m-%Y %I:%M %p")
  return ist_time

def get_time_in_str(ist_time):
  return ist_time.strftime("%d-%m-%Y %I:%M %p")

def get_time_difference(ist_time):
  current_ist_time = datetime.datetime.now()
  # Calculate the time difference
  return current_ist_time - ist_time

# def acknowledge_incident(pd_incident_ids, titles, created_ats):
#     global incident_dict
#     url = "https://fourkites-inc.pagerduty.com/api/v1/incidents"
#     payload = {"requester_id": pd_user_id, "incidents": [{"id": pd_incident_id, "type": "incident_reference", "status": "acknowledged"}for pd_incident_id in pd_incident_ids]}
#     response = requests.request("PUT", url, headers=headers, json=payload)
#     print(response.json())
#     if response.status_code != 200:
#           print_l(f"FAILED to auto acknowledge for incident id: {pd_incident_ids}")
#           return 
#     for title, pd_incident_id,created_at in zip(titles, pd_incident_ids,created_ats):
#       if pd_incident_id in incident_dict:
#           incident_dict[pd_incident_id]["count"] += 1
#           incident_dict[pd_incident_id]["status"] = "Re-acknowledged"
#       else:
#           incident_dict[pd_incident_id] = {}
#           incident_dict[pd_incident_id]["title"] = title
#           incident_dict[pd_incident_id]["url"] = "https://fourkites-inc.pagerduty.com/incidents/" + pd_incident_id
#           incident_dict[pd_incident_id]["count"] = 1
#           incident_dict[pd_incident_id]["status"] = "acknowledged"
#           incident_dict[pd_incident_id]["created_at"] = get_time_in_str(convert_time_to_ist(created_at))
#       save_dict()
        
def get_acknowledged_incidents():
  global incident_dict
  url = "https://fourkites-inc.pagerduty.com/api/v1/incidents?&statuses[]=acknowledged&user_ids[]={}&date_range=all&urgencies[]=high&with_suppressed=true".format(pd_user_id)
  response = requests.request("GET", url, headers=headers)
  if response.status_code == 200:
    for i in response.json()["incidents"]:
      pd_incident_id = i["id"]
      title = i["title"]
      created_at = i["created_at"]
      if pd_incident_id in incident_dict:
          incident_dict[pd_incident_id]["count"] =1
          incident_dict[pd_incident_id]["status"] = "acknowledged"
      else:
          incident_dict[pd_incident_id] = {}
          incident_dict[pd_incident_id]["title"] = title
          incident_dict[pd_incident_id]["url"] = "https://fourkites-inc.pagerduty.com/incidents/" + pd_incident_id
          incident_dict[pd_incident_id]["count"] = 1
          incident_dict[pd_incident_id]["status"] = "acknowledged"
          incident_dict[pd_incident_id]["created_at"] = get_time_in_str(convert_time_to_ist(created_at))
  else:
    print(f"failed to get acknowledged incidents.") 
     
        
def update_incidents():
  try:
    url = "https://fourkites-inc.pagerduty.com/api/v1/incidents?limit=100&offset=0&user_ids={}&statuses%5B%5D=acknowledged&statuses%5B%5D=triggered&statuses%5B%5D=resolved&date_range=all&include%5B%5D=privileges&include%5B%5D=priorities&exclude%5B%5D=subscriber_requests&sort_by=urgency%3Adesc%2Ccreated_at%3Adesc&with_suppressed=true".format(pd_user_id)
    response = requests.request("GET", url, headers=headers, data=payload)
    global incident_dict
    incidents_dict = incident_dict.copy()
    if response.status_code == 200:
      for ins in response.json()["incidents"]:
          if "status" in ins:
            if ins["id"] not in incidents_dict.keys():
                pd_incident_id = ins["id"]
                title = ins["title"]
                created_at = ins["created_at"]
                if pd_incident_id not in incidents_dict:
                    incidents_dict[pd_incident_id]["count"] += 1
                    incidents_dict[pd_incident_id]["status"] = "acknowledged"
                else:
                    incidents_dict[pd_incident_id] = {}
                    incidents_dict[pd_incident_id]["title"] = title
                    incidents_dict[pd_incident_id]["url"] = "https://fourkites-inc.pagerduty.com/incidents/" + pd_incident_id
                    incidents_dict[pd_incident_id]["count"] = 1
                    incidents_dict[pd_incident_id]["status"] = "acknowledged"
                    incidents_dict[pd_incident_id]["created_at"] = get_time_in_str(convert_time_to_ist(created_at))      
            i = ins["id"]
            tim_diff = get_time_difference(get_time_from_str(incidents_dict[i]["created_at"]))
            if ins["status"] == "resolved":
              incidents_dict[i]["status"] = "resolved"
              if ORANGE in incidents_dict[i]["title"] or RED in incidents_dict[i]["title"]:
                incidents_dict[i]["title"]=incidents_dict[i]["title"].replace(RED,GREEN).replace(ORANGE,GREEN)
              else:
                incidents_dict[i]["title"] = GREEN + incidents_dict[i]["title"] + END
            elif (tim_diff.total_seconds()>600 and tim_diff.total_seconds()<3600):
              if ORANGE not in incidents_dict[i]["title"]:
                incidents_dict[i]["title"] = ORANGE +incidents_dict[i]["title"] + END
            elif (tim_diff.total_seconds()>3600):
              if RED not in incidents_dict[i]["title"] and ORANGE not in incidents_dict[i]["title"]: 
                incidents_dict[i]["title"] = RED +incidents_dict[i]["title"] + END
              elif RED not in incidents_dict[i] and ORANGE in incident_dict[i]["title"]:
                incidents_dict[i]["title"]=incidents_dict[i]["title"].replace(ORANGE,RED)
            try:
              incident_dict.update(incidents_dict)        
            except Exception as e:
              print_l("multithreading error:")
              print_l(e)
    display()          
    save_dict()
  except Exception as e:
    print_l(e)
    time.sleep(5)
  time.sleep(10)
  
def acknowledge_incident(pd_incident_id, title, created_at):
  global incident_dict
  url = "https://fourkites-inc.pagerduty.com/api/v1/incidents"
  payload = {"requester_id": pd_user_id, "incidents": [{"id": pd_incident_id, "type": "incident_reference", "status": "acknowledged"}]}
  response = requests.request("PUT", url, headers=headers, json=payload)
  print(response.json())
  if response.status_code != 200:
        print_l(f"FAILED to auto acknowledge for incident id: {pd_incident_id}")
        return 
  if pd_incident_id in incident_dict:
      incident_dict[pd_incident_id]["count"] += 1
      incident_dict[pd_incident_id]["status"] = "Re-acknowledged"
  else:
      incident_dict[pd_incident_id] = {}
      incident_dict[pd_incident_id]["title"] = title
      incident_dict[pd_incident_id]["url"] = "https://fourkites-inc.pagerduty.com/incidents/" + pd_incident_id
      incident_dict[pd_incident_id]["count"] = 1
      incident_dict[pd_incident_id]["status"] = "acknowledged"
      incident_dict[pd_incident_id]["created_at"] = get_time_in_str(convert_time_to_ist(created_at))
  save_dict()

def display():
  global incident_dict
  table_data = []
  try:
    clear_screen()
    incidents_dict = incident_dict.copy()
    for i in incidents_dict:
      table_row = {}
      for key, value in incident_dict[i].items():
          table_row[key] = value
      table_data.append(table_row)
    if (len(table_data)>0):
      print_l(tabulate(table_data, headers="keys", tablefmt="grid"))
  except Exception as e:
    print_l(e)
    time.sleep(1)

def get_and_acknowledge_incidents():
    while not kill and autoAcknowledge:
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.json()["triggered"] > 0:
            res = requests.request("GET", url_incidents, headers=headers, data=payload)
            for i in res.json()["incidents"]:
              acknowledge_incident(i["id"], i["title"], i["created_at"])
            # acknowledge_incident([i["id"] for i in res.json()["incidents"]], [i["title"] for i in res.json()["incidents"]], [i["created_at"] for i in res.json()["incidents"]])
            # update_incidents()
            playsound.playsound("sound.mp3", True)
        time.sleep(10)

def save_dict():
  global incident_dict
  pk.dump(incident_dict, open("./incident_dict", mode ="wb"))

def load_dict():
  try:
    pass
    return pk.load(open("./incident_dict", mode ="rb"))
  except Exception as e:
    print_l(("Error",e))
    print_l(("program will continue. dont worry..."))
  return {}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def update_incidents_status(once = False):
    global incident_dict, RED, ORANGE,GREEN, END, YELLOW_TIME, RED_TIME
    
    YELLOW_TIME_IN_SECS = YELLOW_TIME*60
    RED_TIME_IN_SECS = RED_TIME*60 + YELLOW_TIME*60
    
    while not kill:
      try:
        get_acknowledged_incidents()
        incidents_dict = incident_dict.copy()
        for i in incidents_dict:
            if (incidents_dict[i]["status"] != "resolved"):
                res = requests.request("GET", f"https://fourkites-inc.pagerduty.com/api/v1/incidents/{i}", headers=headers)
                try:
                  json_response = res.json()
                  tim_diff = get_time_difference(get_time_from_str(incidents_dict[i]["created_at"]))
                  if "incident" in json_response and "status" in json_response["incident"]:
                    if json_response["incident"]["status"] == "resolved":
                      incidents_dict[i]["status"] = "resolved"
                      if ORANGE in incidents_dict[i]["title"] or RED in incidents_dict[i]["title"]:
                        incidents_dict[i]["title"]=incidents_dict[i]["title"].replace(RED,GREEN).replace(ORANGE,GREEN)
                      else:
                        incidents_dict[i]["title"] = GREEN + incidents_dict[i]["title"] + END
                    elif (tim_diff.total_seconds()>YELLOW_TIME_IN_SECS and tim_diff.total_seconds()<RED_TIME_IN_SECS):
                      if ORANGE not in incidents_dict[i]["title"]:
                        incidents_dict[i]["title"] = ORANGE +incidents_dict[i]["title"] + END
                    elif (tim_diff.total_seconds()>RED_TIME_IN_SECS):
                      if RED not in incidents_dict[i]["title"] and ORANGE not in incidents_dict[i]["title"]: 
                        incidents_dict[i]["title"] = RED +incidents_dict[i]["title"] + END
                      elif RED not in incidents_dict[i] and ORANGE in incident_dict[i]["title"]:
                        incidents_dict[i]["title"]=incidents_dict[i]["title"].replace(ORANGE,RED)
                      else:
                        pass
                    else:
                      pass
                except json.decoder.JSONDecodeError as e:
                  # Handle the case where the response is not in JSON format or empty
                  print_l("Error: Response is not in JSON format or empty.")
                  print_l((res.status_code,res.text,e))
            display()          
        save_dict()
      except Exception as e:
        print_l(e)
        time.sleep(5)
      if once==True:
        return
      time.sleep(10)
      
def excecute_job_forr_alert(incident_id):
  # get alert service name.
  pass
  
def get_input():
  global kill , autoAcknowledge
  while not kill:
    inp = input("Thread 3: enter q to exit \nThread 3: enter u to update.\nThread 3: enter a to toggle auto acknowledge from on to off. currently set to :"+str(autoAcknowledge))
    if (inp == 'u'):
      update_incidents()
    elif (inp == 'a'):
      print_l("toggling auto acknowledge to"+str(not(autoAcknowledge)))
      autoAcknowledge = not(autoAcknowledge)
    elif (inp =='m'):
      print_l("updating...")
      update()
    elif (inp == 'q'):
      kill =True
      print_l("exiting pls wait.")
      exit(0)
    
def get_remote_content(file_url):
    try:
        return requests.get(file_url).text
    except Exception as e:
        print_l(f"Error fetching remote content: {e}")
        return None

def update():
    file_url = "https://raw.githubusercontent.com/vengadam2001/pdAutoAck/main/pagerduty_trigger_alert.py"

    if get_remote_content(file_url) is not None and get_remote_content(file_url) != open("pagerduty_trigger_alert.py").read():
        os.remove("pagerduty_trigger_alert.py")
        with open("pagerduty_trigger_alert.py", "w") as f:
            f.write(get_remote_content(file_url))
        print_l("Updated to latest version.")
        os.execv(__file__, sys.argv)

if __name__ == "__main__":
    update()
    
    incident_dict = load_dict()
    
    t1 = Thread(target=get_and_acknowledge_incidents) ## comment this line to disable auto acknowledge.
    t2 = Thread(target=update_incidents_status)
    t3 = Thread(target=get_input)
    
    t1.start()
    t2.start()
    t3.start()
    
    t1.join()
    t2.join()
    t3.join()
    
    print_l("exited properly")

#change the color of the alert when a incident is not resolved for more than 30 mins.
