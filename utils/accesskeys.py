import requests
from utils.locallogging import debug

CONNECTION_KEYS = ["/helix-aws/aws_access_key", "/helix-aws/aws_secret_access_key", "/helix-aws/librato_api_key",
                      "/helix-aws/librato_username", "/helix-aws/pingdom_api_key", "/helix-aws/pingdom_password",
                      "/helix-aws/pingdom_username", "/helix-aws/aws_regions"]

def get_key_from_configservice(env="DEV", api_key="", key="", default_value=None):
    url = "http://config.vs.intelius.com:8080/configuration/1.0/get?env=%s&key=%s" % (env, key)
    if len(api_key) > 0:
        url += "&callerid=%s" % api_key
    debug(url)
    try:
        data = requests.get(url)
        datajson = data.json()
        if data.status_code == 200 and "value" in datajson:
            return datajson["value"]
        elif "value" not in datajson:
            return default_value
    except Exception as e:
        print("UNABLE TO RETRIEVE DATA FROM THE CONFIGURATION SERVICE")
        print(e)

def getAccessPropertiesFromConfigService(env="DEV", api_key="", strip_helix_prefix=True):
    returnmap = {}
    for key in CONNECTION_KEYS:
        value = get_key_from_configservice(env, api_key, key)
        if value is not None:
            if strip_helix_prefix:
                returnmap[key.replace("/helix-aws/", "")] = value
            else:
                returnmap[key] = value
    return returnmap