import requests
import json
from metrics_publisher import MetricsPublisher
from utils.ec2instancedetails import getLocalHostname
from utils.locallogging import debug

class SOLRCloudMetricsPublisher(MetricsPublisher):
    def get_metrics(self, metrics_to_publish={}):
        metrics_to_publish = MetricsPublisher.get_metrics(self, metrics_to_publish)
        # localhostname="ip-172-31-47-211.us-west-2.compute.internal"
        localhostname = getLocalHostname(True)

        clusterstate = self.getClusterStateForHost(localhostname)
        debug(clusterstate)

        self.populateMetrics(localhostname=localhostname, metrics=metrics_to_publish, hosts=clusterstate["leaders"])
        self.populateMetrics(localhostname=localhostname, metrics=metrics_to_publish, replicas=True, hosts=clusterstate["replicas"])

        return metrics_to_publish

    def populateMetrics(self, localhostname, metrics={}, replicas=False, hosts=None):
        for host in hosts:
            solr_stats_url = host["base_url"].replace(localhostname, "localhost") + "/" + host["core"] + "/admin/mbeans?cat=QUERYHANDLER&key=/select&stats=true&wt=json"
            debug(solr_stats_url)
            stats = requests.get(solr_stats_url).json()
            #requests_per_second = stats["solr-mbeans"][1]["/select"]["stats"]["avgRequestsPerSecond"]
            avg_time_per_request = stats["solr-mbeans"][1]["/select"]["stats"]["avgTimePerRequest"]
            median_time_per_request = stats["solr-mbeans"][1]["/select"]["stats"]["medianRequestTime"]
            pct95_time_per_request = stats["solr-mbeans"][1]["/select"]["stats"]["95thPcRequestTime"]
            min5_req_rate_per_second = stats["solr-mbeans"][1]["/select"]["stats"]["5minRateReqsPerSecond"]
            if not replicas:
                metrics[MetricsPublisher.METRICS_SOLRCLOUD_LEADER_AVG_REQUEST_TIME] = MetricsPublisher.wrap_value_type(self, avg_time_per_request, MetricsPublisher.GAUGE)
                metrics[MetricsPublisher.METRICS_SOLRCLOUD_LEADER_MEDIAN_REQUEST_TIME] = MetricsPublisher.wrap_value_type(self, median_time_per_request, MetricsPublisher.GAUGE)
                metrics[MetricsPublisher.METRICS_SOLRCLOUD_LEADER_95PCT_REQUEST_TIME] = MetricsPublisher.wrap_value_type(self, pct95_time_per_request, MetricsPublisher.GAUGE)
                metrics[MetricsPublisher.METRICS_SOLRCLOUD_LEADER_5MIN_REQ_RATE] = MetricsPublisher.wrap_value_type(self, min5_req_rate_per_second, MetricsPublisher.GAUGE)
            else:
                metrics[MetricsPublisher.METRICS_SOLRCLOUD_REPLICA_AVG_REQUEST_TIME] = MetricsPublisher.wrap_value_type(self, avg_time_per_request, MetricsPublisher.GAUGE)
                metrics[MetricsPublisher.METRICS_SOLRCLOUD_REPLICA_MEDIAN_REQUEST_TIME] = MetricsPublisher.wrap_value_type(self, median_time_per_request, MetricsPublisher.GAUGE)
                metrics[MetricsPublisher.METRICS_SOLRCLOUD_REPLICA_95PCT_REQUEST_TIME] = MetricsPublisher.wrap_value_type(self, pct95_time_per_request, MetricsPublisher.GAUGE)
                metrics[MetricsPublisher.METRICS_SOLRCLOUD_REPLICA_5MIN_REQ_RATE] = MetricsPublisher.wrap_value_type(self, min5_req_rate_per_second, MetricsPublisher.GAUGE)

    '''
    Reads in from the localhost zookeeper clusterstate.json file to understand what roles this particular instance
    is playing in the overall SOLRCloud arena. Returns a set of leader roles and replica roles for this instance.
    '''
    def getClusterStateForHost(self, localhostname):
        cluster_state_for_host = {"leaders": [], "replicas": []}

        clusterstate = requests.get("http://localhost:8080/solr/zookeeper?detail=true&path=/clusterstate.json").json()
        cloudstate = json.loads(clusterstate["znode"]["data"])
        for index in cloudstate:
            print index
            for shard in cloudstate[index]["shards"]:
                for replica in cloudstate[index]["shards"][shard]["replicas"]:
                    replica_details = cloudstate[index]["shards"][shard]["replicas"][replica]
                    if localhostname in replica_details["base_url"]:
                        if "leader" in replica_details and replica_details["leader"] == "true":
                            debug("Adding a leader: " + str(replica_details))
                            cluster_state_for_host["leaders"].append(replica_details)
                        else:
                            debug("Adding a replica: " + str(replica_details))
                            cluster_state_for_host["replicas"].append(replica_details)
        return cluster_state_for_host
