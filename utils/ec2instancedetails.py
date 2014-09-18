import requests

def getInstanceId(devmode=False):
    url = "http://169.254.169.254/latest/meta-data/instance-id"
    instance_id = None
    try:
        data = requests.get(url)
        if data.status_code == 200:
             instance_id = data.text
    except:
        print("ERROR retrieving instance details")
        if devmode:
            instance_id = "i-xxxxxxx"
        # Populate test instance id

    return instance_id

def getLocalHostname(devmode=False):
    url = "http://169.254.169.254/latest/meta-data/local-hostname"
    hostname = None
    try:
        data = requests.get(url)
        if data.status_code == 200:
             hostname = data.text
    except:
        print("ERROR retrieving instance details")
        if devmode:
            hostname = "ip-172-31-47-211.us-west-2.compute.internal"
        # Populate test instance id
    return hostname

def getInstanceName(ec2Connection, instance_id, devmode=False):
    if devmode:
        return "coil-2.2.33.1-2"
    else:
        reservations = ec2Connection.get_all_reservations(instance_ids=[instance_id])
        if reservations is not None and len(reservations) == 1:
            if len(reservations[0].instances) == 1 and "Name" in reservations[0].instances[0].tags:
                return reservations[0].instances[0].tags['Name']
        return None