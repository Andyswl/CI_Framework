#coding:utf-8
import requests
import base64
import simplejson
import smtplib
import jenkins
import json
from email.mime.text import MIMEText
from email.header import Header
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import sys,MySQLdb,time,re,os
reload(sys)

jenkins_server_url=" http://10.107.37.154:8080"
user_id="y75wang"
api_token='d3063da305e1075d197f92c07f89097f'
job_token="BAT_Release"
PROXY = os.environ.get('http_proxy', "http://10.144.1.10:8080")
PROXY_FLAG = True
proxy = {"http":PROXY} if PROXY_FLAG else {}


def check_branch(packagename):
    match0 = re.search("\BFSM4_MZ_9999", packagename)
    match1 = re.search("\BFSM4_MZ_9000", packagename)
    match2 = re.search("\BFSM4_MZ_0100", packagename)
    match3 = re.search("\BFSM3_MZ_9999", packagename)
    match4 = re.search("\BFSM3_MZ_9000", packagename)
    if match0 != None :
        return "cbts18_fsm4_trunk"
    elif match1 != None :
        return "cbts18_fsm4_psi"
    elif match2 != None :
        return "cbts18_fsm4_pt1"
    elif match3 != None :
        return "cbts18_fsm3_trunk"
    elif match4 != None:
        return "cbts18_fsm3_psi"
    else:
        return False

def check_branch_old(packagename):
    match0 = re.search("\BFSM4", packagename)
    match1 = re.search("\BFSM3", packagename)
    if match0 != None and match1==None:
        return "R4"
    elif match0 == None and match1 !=None:
        return "R3"
    else:
        return False

def build_released_job(packagename,result):
    server = jenkins.Jenkins(jenkins_server_url, username=user_id, password=api_token)
    status ="released" if result else "not_released"
    server.build_job("CBTS_BAT_Released_Trigger", {"VERSION": packagename, "status": status}, job_token)

def get_buildresult(packagename):
    url = "http://coop.int.net.nokia.com:3001/api/pciinfo/get?buildid=%s" %packagename
    try:
        endStr = ',{"_id":'
        info = requests.get(url,proxies =proxy)
        info.raise_for_status()
        test = info.content
        print test
        endIndex = test.count(endStr)
        print endIndex
        if endIndex >0 :
            index = test.index(endStr)
            json = simplejson.loads(test[1:index])
        elif endIndex == 0:
            json = simplejson.loads(test[1:-1])
        print json
        buildresult = json["buildresult"]
        print buildresult
        if buildresult== "PASS":
            return True
        elif buildresult== "SKIP":
            return False

    except Exception as s:
        print s.message

def get_buildresult_test(packagename):
    branch = "cbts18_fsm4_trunk"
    url = "http://coop.int.net.nokia.com:3001/api/pciinfo/get?buildid=%s&branch=%s" %(packagename,branch)
    try:
        endStr = ',{"_id":'
        info = requests.get(url,proxies =proxy)
        info.raise_for_status()
        test = info.content
        print test
        endIndex = test.count(endStr)
        print endIndex
        if endIndex >0 :
            index = test.index(endStr)
            json = simplejson.loads(test[1:index])
        elif endIndex == 0:
            json = simplejson.loads(test[1:-1])
        print json
        buildresult = json["buildresult"]
        print buildresult
        if buildresult== "PASS":
            return True
        elif buildresult== "SKIP":
            return False

    except Exception as s:
        print s.message

def get_open_issue(branch,packagename):
    issuelist = []
    url = 'http://coop.int.net.nokia.com:3001/api/issues/get?bl=hetran&product=cbts&branch=%s&buildid=%s'%(branch,packagename)
    try:
        info = requests.get(url,proxies=proxy)
        info.raise_for_status()
        json = simplejson.loads(info.content)
        length = len(json["data"])
        for i in range(0, length):
            test = json["data"][i]
            if test["status"] != "Closed":
                if test["test_hierarchy"][0]=="BAT":
                    issues = "["+test["bugid"]+"]"+test["description"]
                    issuelist.append(issues)
        return issuelist
    except Exception as s:
        print s.message

def get_caseresult_R4(packagename):
    url = "http://coop.int.net.nokia.com:3001/api/pciinfo/get?buildid=%s" %packagename
    try:
        endStr = ',{"_id":'
        info = requests.get(url,proxies =proxy)
        info.raise_for_status()
        test = info.content
        print test
        endIndex = test.count(endStr)
        print endIndex
        if endIndex >0 :
            index = test.index(endStr)
            json = simplejson.loads(test[1:index])
        elif endIndex == 0:
            json = simplejson.loads(test[1:-1])
        pci_sum = json['pci_sum'][0]['children']
        print len(pci_sum)
        planned_count = json['pci_sum'][0]['planned_count']
        print planned_count
        pass_count = json['pci_sum'][0]['pass_count']
        print pass_count
        fail_count = json['pci_sum'][0]['fail_count']
        print fail_count
        total_count = fail_count+pass_count
        print total_count
        if len(pci_sum)>1:
            if planned_count==28 and pass_count==28:
                #print "#R4 all case pass"
                return True
            elif fail_count>0 and planned_count==28 and total_count==28:
                #print "#R4 case fail"
                return False
            else:
                return planned_count
    except Exception as s:
        print s.message

def get_caseresult_R3(packagename):
    url = "http://coop.int.net.nokia.com:3001/api/pciinfo/get?buildid=%s" %packagename
    try:
        endStr = ',{"_id":'
        info = requests.get(url,proxies =proxy)
        info.raise_for_status()
        test = info.content
        print test
        endIndex = test.count(endStr)
        print endIndex
        if endIndex >0 :
            index = test.index(endStr)
            json = simplejson.loads(test[1:index])
        elif endIndex == 0:
            json = simplejson.loads(test[1:-1])
        print json
        pci_sum = json['pci_sum'][0]['children']
        planned_count = json['pci_sum'][0]['planned_count']
        pass_count = json['pci_sum'][0]['pass_count']
        fail_count = json['pci_sum'][0]['fail_count']
        print fail_count
        total_count = fail_count+pass_count
        print total_count
        if len(pci_sum)==1:
            if planned_count==12 and pass_count==12:
                #R3 all case pass
                return True
            elif fail_count>0 and planned_count==12 and total_count==12:
                #R3 case fail
                return False
            else:
                return planned_count
    except Exception as s:
        print s.message

def execute_sql(handle,cmd):
    with handle:
        cur = handle.cursor()
        cur.execute(cmd)
        return cur.fetchall()

def update_cb_result(packagename):
    cb_sql = MySQLdb.connect(host='10.159.215.166', user='cbts', passwd='cbts', db='cloudbts', port=3306)
    cmd = "UPDATE central_build SET lswbt_status='Passed', swbt_level=5,swbt_site='HZ' WHERE packag_name='%s'" %packagename
    print(cmd)
    execute_sql(cb_sql,cmd)

def get_test_result(packagename):
    conn = MySQLdb.connect(host='10.159.215.166',port=3306,user='admin',passwd='btsci',db='cloudbts')
    cursor = conn.cursor()
    cmd = "select lswbt_status from central_build where packag_name='"+packagename+"'"
    cursor.execute(cmd)
    result =cursor.fetchall()
    format_result = result[0]
    return format_result[0]

def get_maillist(branchname):
    conn = MySQLdb.connect(host='10.159.215.166',port=3306,user='admin',passwd='btsci',db='cloudbts')
    cursor = conn.cursor()
    cmd_1 = "SELECT mail_to_group,mail_cc_group from report_info where report_info.branch='CBTS_MZ'"
    cursor.execute(cmd_1)
    mail_group =cursor.fetchall()
    format_to_maillist = mail_group[0][0]
    format_cc_maillist = mail_group[0][1]
    print format_to_maillist
    print format_cc_maillist
    return format_to_maillist,format_cc_maillist

def trigger_R4_email(packagename,branch):
    server=jenkins.Jenkins(jenkins_server_url, username=user_id, password=api_token)
    server.build_job("CBTS_BAT_Report", {"VERSION": packagename,"Branch": branch})

def trigger_R3_email(packagename,branch):
    server=jenkins.Jenkins(jenkins_server_url, username=user_id, password=api_token)
    server.build_job("CBTS_BAT_Report_R3", {"VERSION": packagename,"Branch": branch})

#if __name__ == '__main__':
#     check_branch("CBTS00_FSM4_MZ_9000_000468_000000"
#   get_open_issue("cbts18_fsm4_trunk","CBTS00_FSM4_MZ_9999_000468_000000")
#     get_caseresult_R4("CBTS00_FSM4_MZ_9999_000385_000000")
#     get_maillist("CBTS00_FSM4_MZ_9999_000280_000000")
#     build_released_job("CBTS00_FSM4_MZ_9999_000280_000000","True")
#     print "sys.argv[1]---------",sys.argv[1]
#     packagename = sys.argv[1]
#     status = {'Quality Level':5,'Result':'Passed'}
#     CL = CiApi()
#     caseresult = CL.get_caseresult(packagename)
#    get_buildresult_test("CBTS00_FSM4_MZ_9999_000336_000000")
    #get_caseresult_R4("CBTS00_FSM4_MZ_9999_000296_000000")





