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
template_body="""{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "A sample cloudformation stack with a single ec2 instance",
  "Resources" : {
    "Ec2Instance" : {
      	"Type" : "AWS::EC2::Instance",
		"Properties" : {
			"BlockDeviceMappings" : [
				{
			      "DeviceName" : "/dev/sdb",
			      "Ebs" : { "VolumeSize" : "75", "VolumeType" : "gp2" }
			   	},
			   	{
			      "DeviceName" : "/dev/sdc",
			      "Ebs" : { "VolumeSize" : "75", "VolumeType" : "gp2" }
			   	}
			],
			"ImageId" : "ami-79196349",
			"SubnetId" : "subnet-4b83612e",
			"KeyName" : "inome_helix_production_cluster",
			"InstanceType": "r3.large",
			"PlacementGroupName" : "production-cluster",
			"SecurityGroupIds": ["sg-eeca1a8b"]
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




