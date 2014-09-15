__author__ = 'mhuff'
import requests
import boto.ec2
from awsutils.accesskeys import getAccessPropertiesFromConfigService
from awsutils.locallogging import debug
import psutil

def getInstanceId():
    url = "http://169.254.169.254/latest/meta-data/instance-id"
    try:
        data = requests.get(url)
        if data.status_code == 200:
            instance_id = data.text
    except requests.packages.urllib3.exceptions.ProtocolError as e:
        # Populate test instance id
        instance_id = "i-0437650f"

    return instance_id

def getInstanceName(ec2Connection, instance_id):
    reservations = ec2Connection.get_all_reservations(instance_ids=[instance_id])
    if reservations is not None and len(reservations) == 1:
        if len(reservations[0].instances) == 1 and "Name" in reservations[0].instances[0].tags:
            return reservations[0].instances[0].tags['Name']
    return None

accessProperties = getAccessPropertiesFromConfigService()
debug(accessProperties)
conn = boto.ec2.connect_to_region(accessProperties["aws_regions"], aws_access_key_id=accessProperties["aws_access_key"], aws_secret_access_key=accessProperties["aws_secret_access_key"])

instance_id = getInstanceId()
print(instance_id)
instance_name = getInstanceName(ec2Connection=conn, instance_id=instance_id)
print(instance_name)
print(psutil.cpu_percent())