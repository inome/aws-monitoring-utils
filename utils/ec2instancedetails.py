__author__ = 'mhuff'
import requests

def getInstanceId():
    url = "http://169.254.169.254/latest/meta-data/instance-id"
    try:
        data = requests.get(url)
        if data.status_code == 200:
             instance_id = data.text
    except:
        print("ERROR")
        # Populate test instance id
        instance_id = "i-0437650f"

    return instance_id

def getInstanceName(ec2Connection, instance_id):
    reservations = ec2Connection.get_all_reservations(instance_ids=[instance_id])
    if reservations is not None and len(reservations) == 1:
        if len(reservations[0].instances) == 1 and "Name" in reservations[0].instances[0].tags:
            return reservations[0].instances[0].tags['Name']
    return None