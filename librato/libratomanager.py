__author__ = 'mhuff'
import boto.ec2
import os
import requests
from time import gmtime, strftime
from awsutils.accesskeys import getAccessPropertiesFromConfigService
from awsutils.locallogging import debug

DEFAULT_LIBRATO_LENGTH = 100

def libratoGET(url, keyname=None, offset=0, auth=None):
    # If no keyname passed in, use the substring of url starting at index 1
    if keyname is None:
        keyname = url[1:]
    fullurl = "https://metrics-api.librato.com/v1" + url + "?length=" + str(DEFAULT_LIBRATO_LENGTH) + "&offset=" + str(offset)
    debug(fullurl)
    data = requests.get(fullurl, auth=auth)
    returnArray = []
    if data.status_code == 200:
        datajson = data.json()
        debug("Length = " + str(datajson["query"]["length"]) + ", found = " + str(datajson["query"]["found"]) + ", total=" + str(datajson["query"]["total"]) + ", offset=" + str(datajson["query"]["offset"]))
        returnArray.extend(datajson[keyname])
        if (datajson["query"]["length"] + datajson["query"]["offset"]) < datajson["query"]["found"]:
            returnArray.extend(libratoGET(url, keyname=keyname, offset=(datajson["query"]["offset"] + DEFAULT_LIBRATO_LENGTH), auth=auth))
        return returnArray
    return None

def libratoPOST(url, data, auth=None):
    url = "https://metrics-api.librato.com/v1" + url
    debug(url)
    response = requests.put(url, data=data, auth=auth)
    if response.status_code != 204:
        return False
    return True

def getLibratoSourcesToUpdate(auth):
    sources = libratoGET("/sources", auth=auth)
    sourcesToUpdate = []
    for source in sources:
        if source["display_name"] is None:
            sourcesToUpdate.append(source["name"])
    return sourcesToUpdate

accessProperties = getAccessPropertiesFromConfigService()
debug(accessProperties)
totalSourcesUpdated = 0
totalErrorsEncountered = 0

sourcesToUpdate = getLibratoSourcesToUpdate(auth=(accessProperties["librato_username"], accessProperties["librato_api_key"]))
debug("Librato sources needing a display_name value: " + str(sourcesToUpdate))

conn = boto.ec2.connect_to_region(accessProperties["aws_regions"], aws_access_key_id=accessProperties["aws_access_key"], aws_secret_access_key=accessProperties["aws_secret_access_key"])
instances = conn.get_all_reservations(filters={"instance-state-name": "running"})
for reservation in instances:
    for instance in reservation.instances:
        if instance.id in sourcesToUpdate:
            debug("Need to update display_name of " + instance.id + " to " + instance.tags['Name'])
            if not libratoPOST("/sources/" + instance.id, data={"display_name": instance.tags["Name"]}):
                print("ERROR updating source " + instance.id)
                totalErrorsEncountered += 1
            else:
                totalSourcesUpdated += 1

print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
print("Total errors encountered: " + str(totalErrorsEncountered))
print("Total sources updated: " + str(totalSourcesUpdated))
