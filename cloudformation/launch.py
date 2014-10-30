__author__ = 'dkonidena'

import argparse
from utils.accesskeys import getAccessPropertiesFromConfigService
from boto.cloudformation import CloudFormationConnection
from boto.regioninfo import  RegionInfo
from utils.locallogging import debug
from cloudformation.launch_cluster_setup import *

# parse the arguments
parser = argparse.ArgumentParser(description="inome's solrcloud infrastructure installer. Sets up people, location and organization clusters given a zookeeper quorum to talk to and a s3 location to pull data from")
parser.add_argument("--zk-quorum", dest="zkquorum", action="store", help="specify the zookeeper quorum that solrcloud cluster talks to. format node1:port,node2:port,node3:port,...",required=True)
parser.add_argument("--s3base", dest="s3base", action="store", help="the s3base location is where the solrcores are stored. eg. s3://inome-helix/helix-3.4-20140908/solr-cores",required=True)
parser.add_argument("--launch", dest="clustertype", action="store", help="specify the cluster type whose infrastructure is about to be launched",required=True)
parser.add_argument("--deployment-type", dest="deployment", action="store_true", help="the deployment type (dev/prod) indicates whether this deployment is for dev or for production")
parser.add_argument("--monitoring", dest="monitoring", action="store_true", help="0/1 to indicate whether you need monitoring turned off (0) or turned on (1) for this setup")
args = vars(parser.parse_args())
debug(args)

# retrieve teh access information from configuration service (http://config.vs.intelius.com:8080/configuration)
# Note: eventually, pull thsi from IAM
accessProperties = getAccessPropertiesFromConfigService()
if accessProperties is None:
    print("UNABLE TO CONTINUE - NOT ABLE TO RETRIEVE CONFIGURATION DETAILS")
    exit(1)


#create a region instance and pass it to CloudFormationConnection constructor as a parameter
region = RegionInfo(name='us-west-2',endpoint='cloudformation.us-west-2.amazonaws.com')

#connection to CloudFormation
connection = CloudFormationConnection(aws_access_key_id=accessProperties["aws_access_key"],
                                      aws_secret_access_key=accessProperties["aws_secret_access_key"],
                                      region=region)

#get the zk_quorum, and s3base values
zk_quorum = args["zk-quorum"]
s3base = args["s3base"]

#determine which type of setup we're trying to launch here
if args["launch"]  == "people":
   launch_people_cluster(connection,zk_quorum,s3base)
elif args["launch"] == "locations":
    launch_locations_cluster(connection,zk_quorum,s3base)
elif args["launch"] == "organizations":
    launch_org_cluster(connection,zk_quorum,s3base)
else:
    raise Exception("Invalid launch (clustertype). Valid options -> people/locations/organizations")