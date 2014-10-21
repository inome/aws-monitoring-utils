__author__ = 'dkonidena'

import json
from collections import OrderedDict
from cloudformation.org_instance_template import *
from cloudformation.people_loc_template import *


'''launch people cluster'''
def launch_people_cluster(connection,zk_quorum,s3baseurl,deployment="dev",monitoring="off"):
    template = dict()

    #template suffix
    template["AWSTemplateFormatVersion"] = "2010-09-09"
    template["Description"] = "A sample cloudformation stack with a single ec2 instance"

    #instance templates
    instance_templates = OrderedDict()
    for i in range(1,7,1):
        instance_templates["Instance" + str(i)] = get_instance_template(i,zk_quorum,s3baseurl,"helix-people")

    template["Resources"] = instance_templates

    template_body = json.dumps(template)

    #validate template
    connection.validate_template(template_body)

    #tag
    tag={"Name":"helix-people"}

    #launch the stack
    connection.create_stack(stack_name="helix-people",template_body=template_body,tags=tag)

'''launch locations cluster'''
def launch_locations_cluster(connection,zk_quorum,s3baseurl,deployment="dev",monitoring="off"):
    template = dict()

    #template suffix
    template["AWSTemplateFormatVersion"] = "2010-09-09"
    template["Description"] = "A sample cloudformation stack with a single ec2 instance"

    #instance templates
    instance_templates = OrderedDict()
    for i in range(1,7,1):
        instance_templates["Instance" + str(i)] = get_instance_template(i,zk_quorum,s3baseurl,"helix-locations")

    template["Resources"] = instance_templates

    template_body = json.dumps(template)

    #validate template
    connection.validate_template(template_body)

    #tag
    tag={"Name":"helix-locations"}

    #launch the stack
    connection.create_stack(stack_name="helix-locations",template_body=template_body,tags=tag)

'''launch organization cluster'''
def launch_org_cluster(connection,zk_quorum,s3baseurl,deployment="dev",monitoring="off"):
    template = dict()

    #template suffix
    template["AWSTemplateFormatVersion"] = "2010-09-09"
    template["Description"] = "A sample cloudformation stack with a single ec2 instance"

    #instance templates
    instance_templates = OrderedDict()
    for i in range(1,3,1):
        instance_templates["Instance" + str(i)] = get_instance_template_org(i,zk_quorum,s3baseurl,"helix-organizations")

    template["Resources"] = instance_templates

    template_body = json.dumps(template)

    #validate template
    connection.validate_template(template_body)

    #tag
    tag={"Name":"helix-organizations"}

    #launch the stack
    connection.create_stack(stack_name="helix-organizations",template_body=template_body,tags=tag)

# zk_quorum="ip-172-31-35-46.us-west-2.compute.internal:2181,ip-172-31-35-45.us-west-2.compute.internal:2181,ip-172-31-35-44.us-west-2.compute.internal:2181"
# s3_base_url="s3://inome-helix/helix-3.4-20140908/solr-cores"

# launch_org_cluster(zk_quorum,s3_base_url)
# launch_people_cluster(zk_quorum,s3_base_url)
# launch_locations_cluster(zk_quorum,s3_base_url)




