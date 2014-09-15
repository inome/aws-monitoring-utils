# machine requirements:
# sudo apt-get install python-dev python-pip
# sudo pip install --upgrade requests psutil argparse boto

__author__ = 'mhuff'
import json
import requests
import boto.ec2
from awsutils.accesskeys import getAccessPropertiesFromConfigService
from awsutils.locallogging import debug
import psutil
import argparse

def getInstanceId():
    url = "http://169.254.169.254/latest/meta-data/instance-id"
    try:
        data = requests.get(url)
        if data.status_code == 200:
             instance_id = data.text
    except:
        print("ERROR")
        # Populate test instance id
        #instance_id = "i-0437650f"

    return instance_id

def getInstanceName(ec2Connection, instance_id):
    reservations = ec2Connection.get_all_reservations(instance_ids=[instance_id])
    if reservations is not None and len(reservations) == 1:
        if len(reservations[0].instances) == 1 and "Name" in reservations[0].instances[0].tags:
            return reservations[0].instances[0].tags['Name']
    return None

def publishMetrics(accessProperties, source, metrics):
    request = {
        "source": source,
        "counters": [],
        "gauges": []
    }
    if ("data-mounts-count" in metrics):
        request["counters"].append({"name": "data-mounts-count", "value": metrics["data-mounts-count"]})
    if ("log-mounts-count" in metrics):
        request["counters"].append({"name": "log-mounts-count", "value": metrics["log-mounts-count"]})
    if ("memory-used-percent" in metrics):
        request["gauges"].append({"name": "memory-used-percent", "value": metrics["memory-used-percent"], "source": source})
    if ("cpu-used-percent" in metrics):
        request["gauges"].append({"name": "cpu-used-percent", "value": metrics["cpu-used-percent"], "source": source})
    debug(request)

    url = "https://metrics-api.librato.com/v1/metrics"
    debug(url)
    response = requests.post(url, data=json.dumps(request), headers={'content-type': 'application/json'}, auth=(accessProperties["librato_username"], accessProperties["librato_api_key"]))
    debug(response)

accessProperties = getAccessPropertiesFromConfigService()
debug(accessProperties)
conn = boto.ec2.connect_to_region(accessProperties["aws_regions"], aws_access_key_id=accessProperties["aws_access_key"], aws_secret_access_key=accessProperties["aws_secret_access_key"])

parser = argparse.ArgumentParser(description="inome EC2 monitoring librato publisher")
parser.add_argument("--data-mounts-count", dest="datamountscount", action="store_true", help="Outputs a metric called 'data-mounts-count' with count of how many drives are mounted at /dataX")
parser.add_argument("--log-mounts-count", dest="logmountscount", action="store_true", help="Outputs a metric called 'log-mounts-count' with count of how many drives are mounted at /logs")
parser.add_argument("--memory-percentage", dest="memorypercentage", action="store_true", default=True, help="Outputs a metric called 'memory-used-percent' with percentage count of how much memory is used")
parser.add_argument("--cpu-percent-used", dest="cpupercentused", action="store_true", default=True, help="Outputs a metric called 'cpu-used-percent' with percentage count of how much of the CPU is utilized")
parser.add_argument("--verify", dest="verify", action="store_true", default=False, help="Prints out metrics but does not send to Librato - use prior to installing as a cron")
args = parser.parse_args()
debug(args)

instanceid = getInstanceId()
instancename = getInstanceName(ec2Connection=conn, instance_id=instanceid)
debug("%s - %s" % (instanceid, instancename))

metrics_to_publish = {}
data_mount_count = 0
log_mount_count = 0
for disk in psutil.disk_partitions(all=True):
    debug(disk)
    if args.datamountscount and "data" in disk.mountpoint and "noatime" in disk.opts and "nodiratime" in disk.opts:
        data_mount_count += 1
        debug("Marking disk mount %s as data drive" % disk.mountpoint)
    if args.logmountscount and "logs" in disk.mountpoint:
        log_mount_count += 1
        debug("Marking disk mount %s as log drive" % disk.mountpoint)

if args.datamountscount:
    metrics_to_publish["data-mounts-count"] = data_mount_count
if args.logmountscount:
    metrics_to_publish["log-mounts-count"] = data_mount_count
if args.memorypercentage:
    metrics_to_publish["memory-used-percent"] = psutil.virtual_memory().percent
if args.cpupercentused:
    metrics_to_publish["cpu-used-percent"] = psutil.cpu_percent()

debug(metrics_to_publish)

publishMetrics(accessProperties, instancename, metrics_to_publish)