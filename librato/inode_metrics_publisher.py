from metrics_publisher import MetricsPublisher
import psutil
from utils.locallogging import debug

class INodeMetricsPublisher(MetricsPublisher):
    def get_metrics(self, metrics_to_publish={}):
        metrics_to_publish = MetricsPublisher.get_metrics(self, metrics_to_publish)
        data_mount_count = 0
        log_mount_count = 0
        for disk in psutil.disk_partitions(all=True):
            debug("inodemetrics.disk = " + str(disk))
            if "data" in disk.mountpoint and "noatime" in disk.opts and "nodiratime" in disk.opts:
                data_mount_count += 1
                debug("Marking disk mount %s as data drive" % disk.mountpoint)
            if "logs" in disk.mountpoint:
                log_mount_count += 1
                debug("Marking disk mount %s as log drive" % disk.mountpoint)

        metrics_to_publish["data-mounts-count"] = MetricsPublisher.wrap_value_type(self, data_mount_count, MetricsPublisher.GAUGE)
        metrics_to_publish["log-mounts-count"] = MetricsPublisher.wrap_value_type(self, log_mount_count, MetricsPublisher.GAUGE)
        return metrics_to_publish