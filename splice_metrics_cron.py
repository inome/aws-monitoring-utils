import json
import os.path
import requests
import time

import MySQLdb

import avro.ipc as ipc
import avro.protocol as protocol
from utils.accesskeys import getAccessPropertiesFromConfigService, get_key_from_configservice
from utils.locallogging import debug

splice_path = os.path.join(os.path.dirname(__file__), 'protocols/Splice.avpr')

if not os.path.isfile(splice_path):
    exit(1)

PROTOCOL = protocol.parse(open(splice_path).read())

if __name__ == '__main__':
    db_host = get_key_from_configservice(key="/helix-aws/spliceui_dbhost")
    db_user = get_key_from_configservice(key="/helix-aws/spliceui_dbuser")
    db_pass = get_key_from_configservice(key="/helix-aws/spliceui_dbpass")

    db = MySQLdb.connect(host=db_host,
                         user=db_user,
                         passwd=db_pass)

    users_and_lists = {}

    now = time.strftime("%Y-%m-%d %H:%M:%S")

    cur = db.cursor()
    cur.execute("SELECT id, name, primaryEmail AS email, createdate AS create_date, termsacceptancedate AS terms_date, emailverified AS verified FROM InomeSpliceUI.Customers WHERE createdate > DATE_SUB('%s', INTERVAL 24 HOUR) AND createdate <= '%s' ORDER BY createdate DESC" % (now, now))
    for row in cur.fetchall():
        createdate = row[3]
        if createdate is not None:
           createdate = createdate.strftime("%Y-%m-%d %H:%M")
        termsdate = row[4]
        if termsdate is not None:
           termsdate = termsdate.strftime("%Y-%m-%d %H:%M")
        users_and_lists[str(row[0])] = {"new": True, "id": str(row[0]), "name": row[1], "email": row[2], "createdate": createdate, "termsaccepteddate": termsdate, "emailverified": row[5]}

    cur.execute("SELECT C.id AS customerid, C.name, C.primaryEmail, L.id AS listid, L.name, L.datecreated AS listcreatedate FROM InomeSpliceUI.Lists L INNER JOIN InomeSpliceUI.Customers C ON L.customerid = C.id WHERE L.datecreated > DATE_SUB('%s', INTERVAL 24 HOUR) AND L.datecreated <= '%s'" % (now, now))
    for row in cur.fetchall():
        customerid = str(row[0])
        listid = str(row[3])
        if customerid not in users_and_lists:
            users_and_lists[customerid] = {"id": str(customerid), "name": row[1], "email": row[2]}
        if "lists" not in users_and_lists[customerid]:
            users_and_lists[customerid]["lists"] = {}
        users_and_lists[customerid]["lists"][listid] = {"listid": listid, "listname": row[4], "listdatecreated": row[5].strftime("%Y-%m-%d %H:%M")}

    splice_host = get_key_from_configservice(key="/helix-aws/splice-host")
    splice_port = get_key_from_configservice(key="/helix-aws/splice-port")
    splice_path = get_key_from_configservice(key="/helix-aws/splice-path")
    # client code - attach to the server and send a message
    client = ipc.HTTPTransceiver(str(splice_host), int(splice_port), str(splice_path))
    requester = ipc.Requestor(PROTOCOL, client)

    new_customers_title = "New Customers in the last 24 hours"
    new_lists_title = "New Lists uploaded in the last 24 hours"

    new_customers_table = "%s\nCustomer Id\tCustomer Name\tEmail\tDate Created\tTerms Acceptance\tEmail Verified\n" % new_customers_title
    new_customers_table += "-" * len(new_customers_table)
    new_customers_table += "\n"
    new_lists_table = "%s\nCustomer Id\tCustomer Name\tEmail\tList Id\tList name\tDate Created\tNumber of Records\n\n" % new_lists_title
    new_lists_table += "-" * len(new_lists_table)
    new_lists_table += "\n"

    new_customers_table_html = "<table><tr><th colspan=6>%s</th></tr><tr><th>Customer Id</th><th>Customer Name</th><th>Email</th><th>Date Created</th><th>Terms Acceptance</th><th>Email Verified</th></tr>" % new_customers_title
    new_lists_table_html = "<table><tr><th colspan=7>%s</th></tr><tr><th>Customer Id</th><th>Customer Name</th><th>Email</th><th>List Id</th><th>List name</th><th>Date Created</th><th>Number of Records</th></tr>" % new_lists_title

    # fill in the Message record and send it
    for customeridint, customer in users_and_lists.iteritems():
        params = dict()
        params['customerId'] = "%s" % customeridint
        if "lists" in customer:
            for customerlistid, customerlist in customer["lists"].iteritems():
                params['customerListId'] = "%s" % customerlist["listid"]
                try:
                    debug(requester)

                    listdetails = None
                    try:
                        listdetails = requester.request('getListInfo', params)
                    except AttributeError as e:
                        print("Unable to retrieve list with params %s" % str(params))
                        continue
                    except UnicodeDecodeError as e:
                        print("Bad response received from the server for params %s" % str(params))
                        continue

                    new_lists_table += "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (customer["id"], customer["name"], customer["email"], customerlist["listid"], customerlist["listname"], customerlist["listdatecreated"], listdetails["numRecords"])
                    new_lists_table_html += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % \
                                       (customer["id"], customer["name"], customer["email"], customerlist["listid"], customerlist["listname"], customerlist["listdatecreated"], listdetails["numRecords"])
                except UnicodeDecodeError as e:
                    continue
        if "new" in customer:
            new_customers_table += "%s\t%s\t%s\t%s\t%s\t%s\n" % (customer["id"], customer["name"], customer["email"], customer["createdate"], customer["termsaccepteddate"], customer["emailverified"])
            new_customers_table_html += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (customer["id"], customer["name"], customer["email"], customer["createdate"], customer["termsaccepteddate"], customer["emailverified"])

    new_customers_table_html += "</table>"
    new_lists_table_html += "</table>"

    client.close()

    sharedcount_url = get_key_from_configservice(key="/helix-aws/splice_sharedcount_url")
    sharedcount_resp = ""
    sharedcount_table_html = "<table>"
    try:
       sharedcount_resp = requests.get(sharedcount_url).json()
       sharedcount_table_html += "<tr><td>FB (comments)</td><td>%s</td></tr><tr><td>FB (click)</td><td>%s</td></tr><tr><td>FB (comment)</td><td>%s</td></tr><tr><td>FB (like)</td><td>%s</td></tr><tr><td>FB (share)</td><td>%s</td></tr><tr><td>FB (total)</td><td>%s</td></tr><tr><td>Google Plus</td><td>%s</td></tr><tr><td>Twitter</td><td>%s</td></tr><tr><td>Pinterest</td><td>%s</td></tr><tr><td>LinkedIn</td><td>%s</td></tr>" % (sharedcount_resp["Facebook"]["commentsbox_count"], sharedcount_resp["Facebook"]["click_count"], sharedcount_resp["Facebook"]["comment_count"], sharedcount_resp["Facebook"]["like_count"], sharedcount_resp["Facebook"]["share_count"], sharedcount_resp["Facebook"]["total_count"], sharedcount_resp["GooglePlusOne"], sharedcount_resp["Twitter"], sharedcount_resp["Pinterest"], sharedcount_resp["LinkedIn"])
       sharedcount_table_html += "</table>"
       debug(sharedcount_resp)
       debug(sharedcount_table_html)
    except requests.exceptions.RequestException as e:
       print("Error requesting sharedcount details: %s" %e)

    # construct mandrill request
    mandrill_api_key = get_key_from_configservice(key="/helix-aws/splice_mandrill_key")
    cron_recipients = get_key_from_configservice(key="/helix-aws/cron_recipients")
    if mandrill_api_key is None or cron_recipients is None:
        exit(1)

    recipients = cron_recipients.split(",")

    request = dict()
    request["key"] = mandrill_api_key
    request["message"] = {}
    request["message"]["text"] = "%s\n\n\n%s\n\n\n%s" % (new_customers_table, new_lists_table, str(sharedcount_resp))
    request["message"]["html"] = "%s<br /><br />%s<br /><br />%s" % (new_customers_table_html, new_lists_table_html, sharedcount_table_html)
    request["message"]["subject"] = "insights - 24 hrs of activity"
    request["message"]["from_email"] = "noreply-insights-cron@noreply.com"
    request["message"]["from_name"] = "noreply-insights-cron"
    request["message"]["to"] = []
    for recipient in recipients:
        request["message"]["to"].append({"email": recipient, "type": "to"})
    request["async"] = "false"

    url = "https://mandrillapp.com/api/1.0/messages/send.json"

    mandrill_response = requests.post(url, data=json.dumps(request))
    debug(str(mandrill_response))
