import boto.ec2
import os
import requests
from time import gmtime, strftime
import base64
from utils.accesskeys import getAccessPropertiesFromConfigService
from utils.locallogging import debug

DEFAULT_LIBRATO_LENGTH = 100

def addToSecurityGroup(pingdom_security_groups, ip):
    # length has to be at least 1
    if len(pingdom_security_groups) == 0:
        return False

    # group to attempt to add this ip to
    pingdom_group = pingdom_security_groups[0]
    try:
        debug("Attempting to add " + ip + " to " + pingdom_group.name)
        conn.authorize_security_group(group_id=pingdom_group.id, ip_protocol="tcp", from_port=80, to_port=80,
                                      cidr_ip="%s/32" % ip)
    except boto.exception.EC2ResponseError:
        # remove the group we just tried and try again on a different one
        pingdom_security_groups.pop(0)
        if not addToSecurityGroup(pingdom_security_groups, ip):
            return False
    return True

accessProperties = getAccessPropertiesFromConfigService()
debug(accessProperties)

toEncode = bytes(accessProperties["pingdom_username"] + ":" + accessProperties["pingdom_password"], "UTF-8")
pingdomAuthHeader = base64.b64encode(toEncode)
pingdomAuthHeader = str(pingdomAuthHeader)[2:][:-1]
headers = {"Authorization": "Basic " + pingdomAuthHeader, "App-Key": accessProperties["pingdom_api_key"]}
debug(headers)
probes = requests.get("https://api.pingdom.com/api/2.0/probes", headers=headers).json()
debug(probes)

conn = boto.ec2.connect_to_region(accessProperties["aws_regions"], aws_access_key_id=accessProperties["aws_access_key"], aws_secret_access_key=accessProperties["aws_secret_access_key"])
all_security_groups = conn.get_all_security_groups()
pingdom_security_groups = []
rule_cidr_map = {}
for security_group in all_security_groups:
    if ("pingdom" in security_group.name):
        pingdom_security_groups.append(security_group)
        for rule in security_group.rules:
            for grant in rule.grants:
                rule_cidr_map[rule.from_port + ":" + grant.cidr_ip] = security_group.name
debug(all_security_groups)
debug(pingdom_security_groups)
debug(rule_cidr_map)
debug(len(rule_cidr_map))

pingdom_index = 0
totalNewIpsAdded = 0
totalIpsFailedToAdd = 0

if len(pingdom_security_groups) > 0:
    for probe in probes["probes"]:
        map_key = "80:%s/32" % probe["ip"]
        # Only add this IP in the case that it hasn't already been added before
        if not map_key in rule_cidr_map:
            if addToSecurityGroup(pingdom_security_groups, probe["ip"]):
                totalNewIpsAdded += 1
            else:
                print("Failed to add %s" % probe["ip"])
                totalIpsFailedToAdd += 1

print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
print("Total ips that failed to be added: " + str(totalIpsFailedToAdd))
print("Total ips added to security groups: " + str(totalNewIpsAdded))
