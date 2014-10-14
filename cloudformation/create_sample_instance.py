__author__ = 'dkonidena'

"""
create a sample ec2 instance with the following properties:
    - Create an instance with the following attributes:
	- use the AMI : ami-79196349
	- InstaceType : r3.large
	- Instance Details:
		- Number of instances -> 1
		- Network - vpc-3700e552 (172.31.0.0/16) (default)
		- Subnet - subnet-4b83612e (172.31.32.0/20) (default in us-west-2b)
		- Placement group - production-cluster
		- IAM role - none
		- Shutdown behavior - stop
		- Tenancy - Shared tenancy  (multi-tenant hardware)

	- Add Storage:
		- EBS (SSD) /dev/sdb 10GB , Delete on Termination
		- Tag instance - Name:Solrcloud-Sample

	- Security group:
		- security-group-id: sg-eeca1a8b (production-cluster)
"""
from boto.cloudformation import CloudFormationConnection
from boto.regioninfo import  RegionInfo

#create a region instance and pass it to CloudFormationConnection constructor as a parameter
region = RegionInfo(name='us-west-2',endpoint='cloudformation.us-west-2.amazonaws.com')

#connection to CloudFormation
connection = CloudFormationConnection(aws_access_key_id="AKIAJODA7YBLIAWDFJJA",
                                      aws_secret_access_key="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",
                                      region=region)
#delete teh stack
connection.delete_stack("cf-test-stack")

#create a simple stack  using the following attributes
stack_name="cf-test-stack"

#shards to download from s3
#TODO: Add wait handlers to long running scripts
#TODO: chmod the permissions to ubuntu:ubuntu . For some reason, all the scripts run under UserData as root.
#TODO: Add the part that creates core.properties, sets up solr cores, etc.
#TODO: Add the part that uploads/links config files to zookeeper
#TODO: Add the part where we setup monitoring on the box

leader_shard_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD0.tar.gz"
replica_shard_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD3.tar.gz"
zk_quorum="ip-172-31-40-92.us-west-2.compute.internal,ip-172-31-40-91.us-west-2.compute.internal,ip-172-31-40-93.us-west-2.compute.internal"

template_body="""{
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "A sample cloudformation stack with a single ec2 instance",
    "Resources": {
        "Ec2Instance": {
            "Type": "AWS::EC2::Instance",
            "Properties": {
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/sdb",
                        "Ebs": {
                            "VolumeSize": "75",
                            "VolumeType": "gp2"
                        }
                    },
                    {
                        "DeviceName": "/dev/sdc",
                        "Ebs": {
                            "VolumeSize": "75",
                            "VolumeType": "gp2"
                        }
                    }
                ],
                "ImageId": "ami-79196349",
                "SubnetId": "subnet-4b83612e",
                "KeyName": "inome_helix_production_cluster",
                "InstanceType": "r3.large",
                "PlacementGroupName": "production-cluster",
                "SecurityGroupIds": [
                    "sg-eeca1a8b"
                ],
                "UserData": {
                    "Fn::Base64": {
                        "Fn::Join": [
                            "",
                            [
                                "#!/bin/bash -ex",
                                "\\n",

                                "sudo mkdir /mnt/shards; sudo mkfs -t ext4 /dev/xvdb ; sudo mount /dev/xvdb /mnt/shards; sudo chown -R ubuntu:ubuntu /mnt/shards; df -hT",
                                "\\n",
                                "sudo mkdir -p /mnt1/replicas; sudo mkfs -t ext4 /dev/xvdc ; sudo mount /dev/xvdc /mnt1/replicas; sudo chown -R ubuntu:ubuntu /mnt1/replicas; df -hT",
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/setup_tomcat.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x setup_tomcat.sh """ + zk_quorum + """",
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/download_solr_cores.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x download_solr_cores.sh """ + leader_shard_s3 + """ """ + replica_shard_s3 + """ SHARD0 SHARD3",
                                "\\n"
                            ]
                        ]
                    }
                }
            }
        }
    }
}
"""
tag={"Name":"cf-test-stack-instance"}

#validate template
connection.validate_template(template_body=template_body)

#Now, create stack
connection.create_stack(stack_name=stack_name,template_body=template_body,tags=tag)




