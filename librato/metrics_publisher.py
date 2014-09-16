import psutil
from utils.locallogging import debug
import datetime as dt
import requests
import json

'''
Base class for all metrics to be published from different instance types.
All instances will at a minimum report their CPU utilization % and the Memory utilization %
'''
class MetricsPublisher (object):
    GAUGE = "guage"
    COUNTER = "counter"

    METRICS_MACHINE_CPU = "cpu-used-percent"
    METRICS_MACHINE_MEMORY = "memory-used-percent"

    METRICS_SOLRCLOUD_LEADER_AVG_REQUEST_TIME = "solrcloud-leader-avg-request-time"
    METRICS_SOLRCLOUD_LEADER_5MIN_REQ_RATE = "solrcloud-leader-5min-request-rate"
    METRICS_SOLRCLOUD_REPLICA_AVG_REQUEST_TIME = "solrcloud-leader-avg-request-time"
    METRICS_SOLRCLOUD_REPLICA_5MIN_REQ_RATE = "solrcloud-leader-5min-request-rate"

    CPU_INTERVAL = 30.0

    instance_name = None
    measure_time = int(dt.datetime.now().replace(second=0, microsecond=0).strftime("%s"))

    def __init__(self, instance_name, measure_time=None):
        self.instance_name = instance_name
        if measure_time is not None:
            self.measure_time = measure_time

    def get_metrics(self, metrics_to_publish={}):
        metrics_to_publish[MetricsPublisher.METRICS_MACHINE_MEMORY] = self.wrap_value_type(psutil.virtual_memory().percent, MetricsPublisher.GAUGE)
        metrics_to_publish[MetricsPublisher.METRICS_MACHINE_CPU] = self.wrap_value_type(psutil.cpu_percent(interval=self.CPU_INTERVAL), MetricsPublisher.GAUGE)
        return metrics_to_publish

    def publish_metrics(self, accessProperties=None, verifyonly=False):
        if accessProperties is None or "librato_username" not in accessProperties or "librato_api_key" not in accessProperties:
            print "ERROR - unable to publish metrics without proper authentication credentials"
            return False

        metrics = self.get_metrics()

        request = {
            "source": self.instance_name,
            "measure_time": self.measure_time,
            "counters": [],
            "gauges": []
        }

        for metric_name in metrics:
            metric = metrics[metric_name]
            if metric["type"] == MetricsPublisher.COUNTER:
                request["counters"].append({"name": metric_name, "value": metric["value"]})
            if metric["type"] == MetricsPublisher.GAUGE:
                request["gauges"].append({"name": metric_name, "value": metric["value"]})

        debug(request)

        url = "https://metrics-api.librato.com/v1/metrics"
        debug(url)
        if verifyonly is False:
            response = requests.post(url, data=json.dumps(request),
                                     headers={'content-type': 'application/json'},
                                     auth=(accessProperties["librato_username"], accessProperties["librato_api_key"])
                                     )
            debug(response)

    def wrap_value_type(self, value=None, type=None):
        if value is not None and type is not None:
            if type in [MetricsPublisher.COUNTER, MetricsPublisher.GAUGE]:
                return {"type": type, "value": value}
        return None