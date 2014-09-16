import requests
from utils.locallogging import debug

CONNECTION_KEYS = ["/helix-aws/aws_access_key", "/helix-aws/aws_secret_access_key", "/helix-aws/librato_api_key",
                      "/helix-aws/librato_username", "/helix-aws/pingdom_api_key", "/helix-aws/pingdom_password",
                      "/helix-aws/pingdom_username", "/helix-aws/aws_regions"]

def getAccessPropertiesFromConfigService(env="DEV", apiKey=""):
    returnmap = {}
    for key in CONNECTION_KEYS:
        url = "http://config.vs.intelius.com:8080/configuration/1.0/get?env=%s&key=%s" % (env,key)
        if len(apiKey) > 0:
            url += "&callerid=%s" % apiKey
        debug(url)
        try:
            data = requests.get(url)
            datajson = data.json()
            if data.status_code == 200 and "value" in datajson:
                returnmap[key.replace("/helix-aws/", "")] = datajson["value"]
        except Exception as e:
            print("UNABLE TO RETRIEVE DATA FROM THE CONFIGURATION SERVICE")
            print(e)
            returnmap = None
    return returnmap