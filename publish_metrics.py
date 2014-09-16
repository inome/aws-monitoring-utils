# sudo apt-get install python-dev python-pip
# sudo pip install --upgrade boto psutil argparse requests

import boto.ec2
import argparse
from librato.metrics_publisher import MetricsPublisher
from librato.inode_metrics_publisher import INodeMetricsPublisher
from librato.solrcloud_metrics_publisher import SOLRCloudMetricsPublisher
from utils.locallogging import debug
from utils.ec2instancedetails import getInstanceId, getInstanceName
from utils.accesskeys import getAccessPropertiesFromConfigService

# Parse all arguments, display help if required
parser = argparse.ArgumentParser(description="inome's metrics publisher for librato. Gathers all metrics from the specific metrics collector and publishes them all to librato")
parser.add_argument("--inode-metrics", dest="inodemetrics", action="store_true", help="Computes and publishes all metrics for one of inome's 'inodes'")
parser.add_argument("--solrcloud-metrics", dest="solrcloudmetrics", action="store_true", help="Computes and publishes all metrics for one of inome's solrcloud nodes")
parser.add_argument("--verify", dest="verify", action="store_true", help="Prints out metrics but does not send to Librato - use prior to installing as a cron to ensure proper values are being returned")
parser.add_argument("--dev-mode", dest="devmode", action="store_true", help="Whether to run in 'development' mode or not (hard-coded instance values)")
args = parser.parse_args()
debug(args)

# Retrieve all access information from the configuration service (http://config.vs.intelius.com:8080/configuration)
accessProperties = getAccessPropertiesFromConfigService()
if accessProperties is None:
    print("UNABLE TO CONTINUE - NOT ABLE TO RETRIEVE CONFIGURATION DETAILS")
    exit(1)

# connect to ec2 and pull down the instance name based on the instance id we are running from
conn = boto.ec2.connect_to_region(accessProperties["aws_regions"], aws_access_key_id=accessProperties["aws_access_key"], aws_secret_access_key=accessProperties["aws_secret_access_key"])
instanceid = getInstanceId(args.devmode)
if instanceid is None:
    print("UNABLE TO CONTINUE - NOT ABLE TO IDENTIFY INSTANCE RUNNING")
    exit(1)
instancename = getInstanceName(ec2Connection=conn, instance_id=instanceid, devmode=args.devmode)

# Determine which type of node we're running on and initialize the appropriate metrics publisher
metrics_publisher = None
instancename = "test"
if args.inodemetrics:
    metrics_publisher = INodeMetricsPublisher(instancename)
elif args.solrcloudmetrics:
    metrics_publisher = SOLRCloudMetricsPublisher(instancename)
else:
    metrics_publisher = MetricsPublisher(instancename)

# Call out to publish metrics - this will do the work of collecting metrics and publishing them
metrics_publisher.publish_metrics(None, args.verify)