__author__ = 'dkonidena'

from urllib.request import *
import simplejson
import boto.ec2.cloudwatch
import sys
import traceback

'''
The script aims to publish a set of Solr metrics (custom metrics) to AWS Cloudwatch.
'''

#Amazon Cloudwatch API
#rejects values less than 8.515920e-108 or greater than 1.174271e+107
#So we need normalized the values returned by solr to be within that range
def normalize_value(val):
    float_lower_bound = 8.515920e-108
    float_upper_bound = 1.174271e+107
    float_val = float(val)
    if float_val < float_lower_bound:
        return str(float(8.515920e-108))
    elif float_val > float_upper_bound:
        return str(float(1.174271e+107))
    else:
        return float_val

#
#A function to publish metrics to amazon cloudwatch. The function
#throws an exception if it can't successfully publish metrics to cloudwatch
#
def put_metrics(connection, namespace,name, value, unit, dimensions):
    try:
        connection.put_metric_data(namespace=namespace, name=name, value=normalize_value(value), unit=unit, dimensions=dimensions)
    except Exception:
        print(traceback.format_exc())
        print(sys.exc_info()[0])
        sys.exit(0)


#connection to cloudwatch
cloud_watch_connection =  boto.ec2.cloudwatch.connect_to_region("us-west-2")

instance_id_to_servers=dict()

#TODO: eventually, we need to grab this values from boto's ec2 api
instance_id_to_servers["i-24afdc2f"] = ('ec2-54-191-245-79.us-west-2.compute.amazonaws.com', '8080:SHARD0', '7070:SHARD3')
instance_id_to_servers["i-58afdc53"] = ('ec2-54-191-245-85.us-west-2.compute.amazonaws.com', '8080:SHARD1', '7070:SHARD4')
instance_id_to_servers["i-5fafdc54"] = ('ec2-54-191-245-149.us-west-2.compute.amazonaws.com', '8080:SHARD2', '7070:SHARD0')
instance_id_to_servers["i-5eafdc55"] = ('ec2-54-191-103-170.us-west-2.compute.amazonaws.com', '8080:SHARD3', '7070:SHARD5')
instance_id_to_servers["i-5dafdc56"] = ('ec2-54-191-245-171.us-west-2.compute.amazonaws.com', '8080:SHARD4', '7070:SHARD1')
instance_id_to_servers["i-5cafdc57"] = ('ec2-54-186-22-13.us-west-2.compute.amazonaws.com', '8080:SHARD5', '7070:SHARD2')

#solrcloud location servers
instance_id_to_servers["i-7993e072"] = ('ec2-54-191-220-179.us-west-2.compute.amazonaws.com', '8080:SHARD0', '7070:SHARD3')
instance_id_to_servers["i-7893e073"] = ('ec2-54-191-222-154.us-west-2.compute.amazonaws.com', '8080:SHARD1', '7070:SHARD4')
instance_id_to_servers["i-7f93e074"] = ('ec2-54-191-220-109.us-west-2.compute.amazonaws.com', '8080:SHARD2', '7070:SHARD0')
instance_id_to_servers["i-7e93e075"] = ('ec2-54-191-222-4.us-west-2.compute.amazonaws.com', '8080:SHARD3', '7070:SHARD5')
instance_id_to_servers["i-7d93e076"] = ('ec2-54-191-82-17.us-west-2.compute.amazonaws.com', '8080:SHARD4', '7070:SHARD1')
instance_id_to_servers["i-7c93e077"] = ('ec2-54-191-220-252.us-west-2.compute.amazonaws.com', '8080:SHARD5', '7070:SHARD2')

#solrcloud org servers
instance_id_to_servers["i-6ea1d265"] = ('ec2-54-191-63-45.us-west-2.compute.amazonaws.com', '8080:SHARD0', '')
instance_id_to_servers["i-6da1d266"] = ('ec2-54-186-237-60.us-west-2.compute.amazonaws.com', '8080:SHARD0', '')

for key in instance_id_to_servers:
    instance_id = key
    host_url = instance_id_to_servers[key][0]
    leader_shardname = instance_id_to_servers[key][1].split(":")[1]
    leader_shardport = instance_id_to_servers[key][1].split(":")[0]

    dimensions=dict()
    dimensions["InstanceId"] = instance_id

    #make the query to get stats
    leader_stats = "http://"+host_url+":"+leader_shardport+"/solr/"+leader_shardname+"/admin/mbeans?cat=QUERYHANDLER&key=/select&stats=true&wt=json"

    #connection
    leader_connection = urlopen(leader_stats)
    leader_stats_json = simplejson.load(leader_connection)

    #stats
    leader_avg_requests_per_second = leader_stats_json["solr-mbeans"][1]["/select"]["stats"]["avgRequestsPerSecond"]
    leader_avg_time_per_request =  leader_stats_json["solr-mbeans"][1]["/select"]["stats"]["avgTimePerRequest"]
    leader_5min_req_rate_per_second = leader_stats_json["solr-mbeans"][1]["/select"]["stats"]["5minRateReqsPerSecond"]

    #use boto to publish custom metrics
    #mon-put-data --metric-name "SolrCloudAvgRequestsPerSec" --namespace "System/Linux" --dimensions "InstanceId=i-24afdc2f" --value "$SolrCloudAvgRequestsPerSec" --unit "Count/Second"

    put_metrics(cloud_watch_connection, "System/Linux", "SolrCloudLeaderAvgRequestsPerSec", leader_avg_requests_per_second, "Count/Second", dimensions)
    put_metrics(cloud_watch_connection, "System/Linux", "SolrCloudLeader5minRateReqsPerSecond", leader_5min_req_rate_per_second, "Count/Second", dimensions)
    put_metrics(cloud_watch_connection, "System/Linux", "SolrCloudLeaderAvgTimePerRequest", leader_avg_time_per_request, "Milliseconds", dimensions)

    #org cores don't have replicas. don't do this for them
    is_org = True if (key == 'i-6ea1d265' or key == 'i-6da1d266') else False

    if not is_org:
        replica_shardname = instance_id_to_servers[key][2].split(":")[1]
        replica_shardport = instance_id_to_servers[key][2].split(":")[0]

        replica_stats = "http://"+host_url+":"+replica_shardport+"/solr/"+replica_shardname+"/admin/mbeans?cat=QUERYHANDLER&key=/select&stats=true&wt=json"

        replica_connection = urlopen(replica_stats)
        replica_stats_json = simplejson.load(replica_connection)

        replica_avg_requests_per_second = replica_stats_json["solr-mbeans"][1]["/select"]["stats"]["avgRequestsPerSecond"]
        replica_avg_time_per_request =  replica_stats_json["solr-mbeans"][1]["/select"]["stats"]["avgTimePerRequest"]
        replica_5min_req_rate_per_second = replica_stats_json["solr-mbeans"][1]["/select"]["stats"]["5minRateReqsPerSecond"]

        put_metrics(cloud_watch_connection, "System/Linux", "SolrCloudReplicaAvgRequestsPerSec", replica_avg_requests_per_second, "Count/Second", dimensions)
        put_metrics(cloud_watch_connection, "System/Linux", "SolrCloudReplica5minRateReqsPerSecond", replica_5min_req_rate_per_second, "Count/Second", dimensions)
        put_metrics(cloud_watch_connection, "System/Linux", "SolrCloudReplicaAvgTimePerRequest", replica_avg_time_per_request, "Milliseconds", dimensions)

