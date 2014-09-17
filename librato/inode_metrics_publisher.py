from metrics_publisher import MetricsPublisher
import psutil
from utils.locallogging import debug

# Other metrics to possibly get:
# Lots of options: http://cloudera-manager-server:7180/static/apidocs/
# RegionServer metrics: http://CLOUDERA-MANAGER-SERVER:7180/api/v5/clusters/PRODUCTION-07242014/services/hbase2/roles
# Perhaps count number of region servers and number of masters, report as metric
# HBase metrics: http://CLOUDERA-MANAGER-SERVER:7180/api/v5/clusters/PRODUCTION-07242014/services/hbase2/metrics?from=2014-09-17T19:00:00.000Z&to=now (make sure this gets a single value -- repeat query until we get one?)
# (optional): metrics=read_requests_count_regionserver_avg_rate&metrics=fs_read_latency_histogram_95th_percentile_regionserver_avg

# Cloudera notes on regionserver metrics: http://www.cloudera.com/content/cloudera-content/cloudera-docs/CM4Ent/4.8.2/Cloudera-Manager-Metrics/regionserver_metrics.html
# Cloudera notes on hbase metrics: http://www.cloudera.com/content/cloudera-content/cloudera-docs/CM4Ent/4.8.2/Cloudera-Manager-Metrics/hbase_metrics.html
# Cloudera notes on hdfs metrics: http://www.cloudera.com/content/cloudera-content/cloudera-docs/CM4Ent/4.8.2/Cloudera-Manager-Metrics/hdfs_metrics.html

class INodeMetricsPublisher(MetricsPublisher):
    def get_metrics(self, metrics_to_publish={}):
        metrics_to_publish = MetricsPublisher.get_metrics(self, metrics_to_publish)
        data_mount_count = 0
        log_mount_count = 0
        for disk in psutil.disk_partitions(all=True):
            debug("inodemetrics.disk = " + str(disk))
            if "data" in disk.mountpoint:
                data_mount_count += 1
                debug("Marking disk mount %s as data drive" % disk.mountpoint)
            if "logs" in disk.mountpoint:
                log_mount_count += 1
                debug("Marking disk mount %s as log drive" % disk.mountpoint)

        metrics_to_publish[MetricsPublisher.METRICS_INODE_DATA_MOUNTS_COUNT] = MetricsPublisher.wrap_value_type(self, data_mount_count, MetricsPublisher.GAUGE)
        metrics_to_publish[MetricsPublisher.METRICS_INODE_LOG_MOUNTS_COUNT] = MetricsPublisher.wrap_value_type(self, log_mount_count, MetricsPublisher.GAUGE)
        return metrics_to_publish