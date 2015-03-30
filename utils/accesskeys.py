import MySQLdb
import requests
import os
from utils.locallogging import debug
from boto.pyami.config import *

CONNECTION_KEYS = ["/helix-aws/aws_access_key", "/helix-aws/aws_secret_access_key", "/helix-aws/librato_api_key",
                      "/helix-aws/librato_username", "/helix-aws/pingdom_api_key", "/helix-aws/pingdom_password",
                      "/helix-aws/pingdom_username", "/helix-aws/aws_regions"]
USE_DB = False

def get_key_from_configservice(env="DEV", api_key="", key="", default_value=None):
    global USE_DB
    if not USE_DB:
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
            USE_DB = True
    if USE_DB:
        # try to read directly from DB (config service in-proc)
        db_host = os.environ.get('INSIGHTS_CONFIGDB_HOST')
        if db_host is None:
            print("UNABLE TO RETRIEVE DATA FROM THE CONFIGURATION SERVICE")
        else:
            db_user = os.environ.get('INSIGHTS_CONFIGDB_USER')
            db_pass = os.environ.get('INSIGHTS_CONFIGDB_PASS')
            db = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass)
            cur = db.cursor()
            cur.execute("SELECT Value FROM Inome.Configuration WHERE Env = '%s' AND `Key` = '%s'" % (env, key))
            for row in cur.fetchall():
                return row[0]
    return default_value

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

# NOTE: This requires that you have a file called .boto in your home directory
# with the access key and secret key defined
def getAccessPropertiesFromBotoConfig():
    returnmap = {}
    config = Config()

    access_key_id = config.get_value(section="Credentials", name="aws_access_key_id")
    secret_access_key = config.get_value(section="Credentials", name="aws_secret_access_key")

    returnmap["aws_access_key"] = access_key_id
    returnmap["aws_secret_access_key"] = secret_access_key

    return returnmap

