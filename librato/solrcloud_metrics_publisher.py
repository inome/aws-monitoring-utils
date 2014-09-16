from metrics_publisher import MetricsPublisher

class SOLRCloudMetricsPublisher(MetricsPublisher):
    def get_metrics(self, metrics_to_publish={}):
        metrics_to_publish = MetricsPublisher.get_metrics(self, metrics_to_publish)
        return metrics_to_publish