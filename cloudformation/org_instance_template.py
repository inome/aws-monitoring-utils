__author__ = 'dkonidena'

from collections import OrderedDict
from cloudformation.commonutils import *

'''get the cloudformation template for org clusters'''
def get_instance_template_org(instance_num, zk_quorum, s3location, coretype, collection):
    instance = OrderedDict()

    #Instance type
    instance["Type"] = "AWS::EC2::Instance"

    #Instance Properties
    instance_properties = OrderedDict()
    instance_properties["ImageId"] = "ami-79196349"
    instance_properties["SubnetId"] = "subnet-4b83612e"
    instance_properties["KeyName"] =  "inome_helix_production_cluster"
    instance_properties["InstanceType"] = "m3.large"

    #Block device mappings
    block_device_mappings = list()
    block_device_mapping1 = OrderedDict()

    block_device_mapping1["DeviceName"] = "/dev/sdb"
    block_device_mapping1["Ebs"] = OrderedDict()
    block_device_mapping1["Ebs"]["VolumeSize"] = "30"
    block_device_mapping1["Ebs"]["VolumeType"] = "gp2"

    block_device_mappings.append(block_device_mapping1)

    instance_properties["BlockDeviceMappings"] = block_device_mappings

    #SecurityGroupIds
    security_group_ids = list()
    security_group_ids.append("sg-eeca1a8b")

    instance_properties["SecurityGroupIds"] = security_group_ids

    #Tags
    tags = list()
    tag = OrderedDict()
    tag["Key"] = "Name"
    tag["Value"] = get_instance_name(coretype,"dev") + str(instance_num)
    tags.append(tag)

    instance_properties["Tags"] = tags

    #UserData
    user_data = OrderedDict()
    fn_base64 = OrderedDict()
    fn_join = list()

    fn_join.append("")
    fn_join_sublist = list()

    fn_join_sublist.append("#!/bin/bash -ex")
    fn_join_sublist.append("\n")

    #create directories for storing shards and replicas, attach filesystems to block devices, mount block devices to directories created
    fn_join_sublist.append("sudo mkdir /mnt/shards; sudo mkfs -t ext4 /dev/xvdb ; sudo mount /dev/xvdb /mnt/shards; sudo chown -R ubuntu:ubuntu /mnt/shards; df -hT")
    fn_join_sublist.append("\n")

    #download appropriate scripts and setup tomcat configuration files
    fn_join_sublist.append("/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/setup_tomcat_org.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts")
    fn_join_sublist.append("\n")
    fn_join_sublist.append("bash -x setup_tomcat_org.sh " + zk_quorum)
    fn_join_sublist.append("\n")

    #download shards and replicas to their respective locations from s3
    fn_join_sublist.append("/opt/s3cmd/s3cmd --config /opt/s3cfg get " + get_shard_location(s3location,coretype,instance_num,"leader") + " " + "/mnt/shards")
    fn_join_sublist.append("\n")
    fn_join_sublist.append("cd /mnt/shards; tar xzvf SHARD0.tar.gz")
    fn_join_sublist.append("\n")

    #upload configs to zookeeper, link the configs with the appropriate collection
    #run this only on the first instance
    if instance_num == 1:
        fn_join_sublist.append("/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/setup_zk.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts")
        fn_join_sublist.append("\n")
        fn_join_sublist.append("bash -x setup_zk.sh " + zk_quorum + " " + get_solr_config_name(coretype) + " " + "/mnt/shards/SHARD0/conf" + " " + collection)
        fn_join_sublist.append("\n")

    #setup solr configuration files
    fn_join_sublist.append("/opt/s3cmd/s3cmd --config /opt/s3cfg get --force s3://inome-solrcloud/scripts/setup_solr.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts")
    fn_join_sublist.append("\n")
    if instance_num == 1:
        fn_join_sublist.append("bash -x setup_solr.sh leader 0 1 SHARD0 shard1 " + collection + " core_node0")
    elif instance_num == 2:
        fn_join_sublist.append("bash -x setup_solr.sh leader 0 1 SHARD0 shard1 " + collection + " core_node1")
    fn_join_sublist.append("\n")

    #finally start both leader and replica tomcat instances
    fn_join_sublist.append("sudo sh -x /opt/solrcloud/shard-leader/tomcat/bin/catalina.sh start")
    fn_join_sublist.append("\n")

    fn_join.append(fn_join_sublist)
    fn_base64["Fn::Join"] = fn_join
    user_data["Fn::Base64"] = fn_base64

    instance_properties["UserData"] = user_data

    instance["Properties"] = instance_properties

    #add DependsOn
    if instance_num > 1:
        instance["DependsOn"] = "Instance1"

    return instance