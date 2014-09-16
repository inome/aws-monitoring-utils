from utils.locallogging import debug
from utils.accesskeys import getAccessPropertiesFromConfigService
from librato.metrics_publisher import MetricsPublisher
from librato.inode_metrics_publisher import INodeMetricsPublisher
from librato.solrcloud_metrics_publisher import SOLRCloudMetricsPublisher
import boto.ec2
import argparse
from utils.ec2instancedetails import getInstanceId, getInstanceName

# Parse all arguments, display help if required
parser = argparse.ArgumentParser(description="inome EC2 monitoring librato publisher")
parser.add_argument("--inode-metrics", dest="inodemetrics", action="store_true", help="Computes and publishes all metrics for one of inome's 'inodes'")
parser.add_argument("--solrcloud-metrics", dest="solrcloudmetrics", action="store_true", help="Computes and publishes all metrics for one of inome's solrcloud nodes")
parser.add_argument("--verify", dest="verify", action="store_true", default=False, help="Prints out metrics but does not send to Librato - use prior to installing as a cron")
args = parser.parse_args()
debug(args)

# Retrieve all access information from the configuration service (http://config.vs.intelius.com:8080/configuration)
accessProperties = getAccessPropertiesFromConfigService()
if accessProperties is None:
    print "UNABLE TO CONTINUE - NOT ABLE TO RETRIEVE CONFIGURATION DETAILS"
    exit(1)

conn = boto.ec2.connect_to_region(accessProperties["aws_regions"], aws_access_key_id=accessProperties["aws_access_key"], aws_secret_access_key=accessProperties["aws_secret_access_key"])
instanceid = getInstanceId()
instancename = getInstanceName(ec2Connection=conn, instance_id=instanceid)

# Determine which type of node we're running on and initialize the appropriate metrics publisher
metrics_publisher = None
if args.inodemetrics:
    metrics_publisher = INodeMetricsPublisher(instancename)
elif args.solrcloudmetrics:
    metrics_publisher = SOLRCloudMetricsPublisher(instancename)
else:
    metrics_publisher = MetricsPublisher(instancename)

# Call out to publish metrics - this will do the work of collecting metrics and publishing them
metrics_publisher.publish_metrics(accessProperties, args.verify)