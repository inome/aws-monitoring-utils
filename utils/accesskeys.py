__author__ = 'mhuff'
import requests
from utils.locallogging import debug

KEYS_WE_CARE_ABOUT = ["/helix-aws/aws_access_key", "/helix-aws/aws_secret_access_key", "/helix-aws/librato_api_key",
                      "/helix-aws/librato_username", "/helix-aws/pingdom_api_key", "/helix-aws/pingdom_password",
                      "/helix-aws/pingdom_username", "/helix-aws/aws_regions"]

def getAccessPropertiesFromConfigService(env="DEV", apiKey=""):
    returnmap = {}
    for key in KEYS_WE_CARE_ABOUT:
        url = "http://config.vs.intelius.com:8080/configuration/1.0/get?env=%s&key=%s" % (env,key)
        if len(apiKey) > 0:
            url += "&callerid=%s" % apiKey
        debug(url)
        data = requests.get(url)
        datajson = data.json()
        if data.status_code == 200 and "value" in datajson:
            returnmap[key.replace("/helix-aws/", "")] = datajson["value"]

    return returnmap