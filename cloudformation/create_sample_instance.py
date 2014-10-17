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

instance1_leader_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD0.tar.gz"
instance1_replica_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD3.tar.gz"
instance2_leader_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD1.tar.gz"
instance2_replica_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD4.tar.gz"
instance3_leader_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD2.tar.gz"
instance3_replica_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD0.tar.gz"
instance4_leader_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD3.tar.gz"
instance4_replica_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD5.tar.gz"
instance5_leader_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD4.tar.gz"
instance5_replica_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD1.tar.gz"
instance6_leader_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD5.tar.gz"
instance6_replica_s3="s3://inome-helix/helix-3.4-20140908/solr-cores/locations/zipped/SHARD2.tar.gz"
zk_quorum="ip-172-31-35-46.us-west-2.compute.internal:2181,ip-172-31-35-45.us-west-2.compute.internal:2181,ip-172-31-35-44.us-west-2.compute.internal:2181"

template_body="""{
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "A sample cloudformation stack with a single ec2 instance",
    "Resources": {
        "Instance1": {
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
                                "bash -x setup_tomcat.sh """ + zk_quorum + "\"" + """,
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/download_solr_cores.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x download_solr_cores.sh """ + instance1_leader_s3 + " " + instance1_replica_s3 + """ SHARD0 SHARD3",
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/setup_zk.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x setup_zk.sh """ + zk_quorum + " " + "personcore" + " " + "/mnt/shards/SHARD0/conf" + " " + "helix-people" +  "\"" + """,
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get --force s3://inome-solrcloud/scripts/setup_solr.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x setup_solr.sh leader 0 6 SHARD0 shard1 helix-people core_node1 && bash -x /opt/solrcloud/scripts/setup_solr.sh replica 3 6 SHARD3 shard4 helix-people core_node10",
                                "\\n",

                                "sudo sh -x /opt/solrcloud/shard-leader/tomcat/bin/catalina.sh start; sudo sh -x /opt/solrcloud/shard-replicas/tomcat1/bin/catalina.sh start",
                                "\\n"
                            ]
                        ]
                    }
                }
            }
        },
        "Instance2": {
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
                                "bash -x setup_tomcat.sh """ + zk_quorum + "\"" + """,
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/download_solr_cores.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x download_solr_cores.sh """ + instance2_leader_s3 + " " + instance2_replica_s3 + """ SHARD1 SHARD4",
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get --force s3://inome-solrcloud/scripts/setup_solr.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x setup_solr.sh leader 1 6 SHARD1 shard2 helix-people core_node2 && bash -x /opt/solrcloud/scripts/setup_solr.sh replica 4 6 SHARD4 shard5 helix-people core_node11",
                                "\\n",

                                "sudo sh -x /opt/solrcloud/shard-leader/tomcat/bin/catalina.sh start; sudo sh -x /opt/solrcloud/shard-replicas/tomcat1/bin/catalina.sh start",
                                "\\n"
                            ]
                        ]
                    }
                }
            },
            "DependsOn" : "Instance1"
        },
        "Instance3": {
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
                                "bash -x setup_tomcat.sh """ + zk_quorum + "\"" + """,
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/download_solr_cores.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x download_solr_cores.sh """ + instance3_leader_s3 + " " + instance3_replica_s3 + """ SHARD2 SHARD0",
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get --force s3://inome-solrcloud/scripts/setup_solr.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x setup_solr.sh leader 2 6 SHARD2 shard3 helix-people core_node3 && bash -x /opt/solrcloud/scripts/setup_solr.sh replica 0 6 SHARD0 shard1 helix-people core_node7",
                                "\\n",

                                "sudo sh -x /opt/solrcloud/shard-leader/tomcat/bin/catalina.sh start; sudo sh -x /opt/solrcloud/shard-replicas/tomcat1/bin/catalina.sh start",
                                "\\n"
                            ]
                        ]
                    }
                }
            },
            "DependsOn" : "Instance1"
        },
        "Instance4": {
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
                                "bash -x setup_tomcat.sh """ + zk_quorum + "\"" + """,
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/download_solr_cores.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x download_solr_cores.sh """ + instance4_leader_s3 + " " + instance4_replica_s3 + """ SHARD3 SHARD5",
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get --force s3://inome-solrcloud/scripts/setup_solr.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x setup_solr.sh leader 3 6 SHARD3 shard4 helix-people core_node4 && bash -x setup_solr.sh replica 5 6 SHARD5 shard6 helix-people core_node12",
                                "\\n",

                                "sudo sh -x /opt/solrcloud/shard-leader/tomcat/bin/catalina.sh start; sudo sh -x /opt/solrcloud/shard-replicas/tomcat1/bin/catalina.sh start",
                                "\\n"
                            ]
                        ]
                    }
                }
            },
            "DependsOn" : "Instance1"
        },
        "Instance5": {
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
                                "bash -x setup_tomcat.sh """ + zk_quorum + "\"" + """,
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/download_solr_cores.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x download_solr_cores.sh """ + instance5_leader_s3 + " " + instance5_replica_s3 + """ SHARD4 SHARD1",
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get --force s3://inome-solrcloud/scripts/setup_solr.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x setup_solr.sh leader 4 6 SHARD4 shard5 helix-people core_node5 && bash -x setup_solr.sh replica 1 6 SHARD1 shard2 helix-people core_node8",
                                "\\n",

                                "sudo sh -x /opt/solrcloud/shard-leader/tomcat/bin/catalina.sh start; sudo sh -x /opt/solrcloud/shard-replicas/tomcat1/bin/catalina.sh start",
                                "\\n"
                            ]
                        ]
                    }
                }
            },
            "DependsOn" : "Instance1"
        },
        "Instance6": {
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
                                "bash -x setup_tomcat.sh """ + zk_quorum + "\"" + """,
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get s3://inome-solrcloud/scripts/download_solr_cores.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x download_solr_cores.sh """ + instance6_leader_s3 + " " + instance6_replica_s3 + """ SHARD5 SHARD2",
                                "\\n",

                                "/opt/s3cmd/s3cmd --config /opt/s3cfg get --force s3://inome-solrcloud/scripts/setup_solr.sh /opt/solrcloud/scripts/; cd /opt/solrcloud/scripts",
                                "\\n",
                                "bash -x setup_solr.sh leader 5 6 SHARD5 shard6 helix-people core_node6 && bash -x setup_solr.sh replica 2 6 SHARD2 shard3 helix-people core_node9",
                                "\\n",

                                "sudo sh -x /opt/solrcloud/shard-leader/tomcat/bin/catalina.sh start; sudo sh -x /opt/solrcloud/shard-replicas/tomcat1/bin/catalina.sh start",
                                "\\n"
                            ]
                        ]
                    }
                }
            },
            "DependsOn" : "Instance1"
        }
    }
}
"""
tag={"Name":"cf-test-stack-instance"}

#validate template
connection.validate_template(template_body=template_body)

#Now, create stack
connection.create_stack(stack_name=stack_name,template_body=template_body,tags=tag)




