Inome AWS Utilities
===================

Collection of python scripts to perform various management tasks on AWS. Currently, only a metrics publishing
framework is in-use. Other tools have been developed but are not yet mainstream.

publish_metrics.py
------------------

This is a utility that allows for direct publishing of metrics from any AWS instance out to the Librato service.
The utility queries the system's meta-data URL and publishes metrics accordingly based on parameters passed in.

Available modes for this script:

  * Standard - only reports CPU and Memory usage. CPU is computed by looking at average load over a 30-second period of time. Memory is based on current point in time.
  * INode (--inode-metrics) - checks for not only CPU and Memory as in the standard mode but also number of disks mounted at /dataX and /logs
  * SOLRCloud (--solrcloud-metrics) - checks for not only CPU and Memory as in the standard mode but also queries SOLRCloud to understand metrics about responsiveness for this node (and all of its shards)

It is intended that this python script be run as a cron ON the AWS instances themselves. The metrics retrieved and the methods used
to query AWS will only work from an actual AWS instance and not from an external source.

Currently, metrics should be reported no more frequently than once every minute. The cron will report different metrics for the same
time-frame if the cron is run more frequently than that. All metrics published are rounded down to the minute to ensure that
multiple metrics can all be correlated with each other by time.

The frequency at which metrics are reported is controlled by how often the cron is run. Each invocation of the cron will publish
a set of metrics (depending on the mode) out to Librato at the specified time-frame. For pricing information on Librato,
[refer to here](https://metrics.librato.com/pricing/grid)