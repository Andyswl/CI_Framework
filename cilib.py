import requests
import os
import re
import sys
import time
import base64
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from hran_execution.reporters.base import TestReporter, log_response, retry
from conf import settings
from base.utils import logger

api_maps = {
    'get_testset': '{base_url}/bat/testset',
    'post_set': '{base_url}/bat/report/testset',
    'post_case': '{base_url}/bat/report/case',
}

def parse_flag(flag):
    flag_map = {
        'true': True,
        'false': False
    }
    try:
        return {x.split(':')[0]:flag_map[x.split(':')[1]] for x in flag.split(',')}
    except Exception, e:
        print str(e)


def need_report(flag):
    print "determine report flag {}".format(flag)
    if flag and True in flag.values():
        return True
    else:
        return False


class CiApi(object):
    def __init__(self, baseline, report_flag):
        self.baseline = baseline
        self.report_flag = parse_flag(report_flag) or {"coop":False,'qc':False,'wft':False}
        self.proxy = {"http":settings.PROXY} if settings.PROXY_FLAG else {}
    @retry
    @log_response
    def _get(self, url, data):
        info = requests.get(url, data,proxies =self.proxy)
        info.raise_for_status()
        return info

    @retry
    @log_response
    def _post(self, url, data):
        info = requests.post(url, json=data,proxies =self.proxy)
        info.raise_for_status()
        return info

    def _get_url(self, action):
        return api_maps[action].format(base_url=settings.CI_SERVER)

    def get_testrun(self):
        return self._get(self._get_url('get_testset'), {'baseline': self.baseline}).content

    def report_case(self, case, result, comment=''):
        """sth"""

    def report_test(self, test, verdict, comment):
        """sth"""

    def report_set(self, case_list, result, reason, comment=''):
        if not need_report(self.report_flag):
            logger.info("Skip report for report_flag")
        else:
            return self._post(self._get_url('post_set'),
                              {'baseline': self.baseline,
                               'data': case_list,
                               'result': result,
                               'reason': reason,
                               'comment': comment,
                               'report': self.report_flag,
                               'qc_info': {
                                   'parent_id':settings.QC_FOLDER_ID,
                                   'release':settings.QC_RELEASE,
                                   'test_set':settings.QC_TEST_SET_TEMP,
                                   'auth':{'token':'Basic ' + base64.b64encode('{}:{}'.format(settings.CI_USER, settings.CI_PASSWORD))},
                                   'domain':settings.QC_DOMAIN,
                                   'project':settings.QC_PROJECT}
                               })


class CiReporter(TestReporter, CiApi):
    def __init__(self, baseline, report_flag):
        TestReporter.__init__(self)
        CiApi.__init__(self, baseline, report_flag)
        self.test_data = {"planned_count": 0,
                          "feature_tested": 0,
                          "result_url": os.getenv("JENKINS_URL"),
                          "test_hierarchy": settings.test_hierarchy,
                          "pass_criteria": settings.pass_criteria,
                          "pass_count": 0,
                          "fail_count": 0,
                          "cases":[]
                          }

    def report_case_start(self, name, args):
        self.test_data["planned_count"] += 1
        self.test_data["feature_tested"] += 1

    def report_case_end(self, name, args):
        if args['status'] =="PASS":
            self.test_data["pass_count"] += 1
        else :
            self.test_data["fail_count"] += 1
        self.test_data["cases"].append({
            "name": name,
            "result": args['status']
        })

    def report_testing_started(self):
        self.test_data['start'] =int(time.time())
        """ Run when testing starts """

    def report_testing_finished(self):
        """ Run when testing ends """

    def report_test_result(self, test, verdict, comment, test_report=None, html_report=None):
        job_name = os.environ.get('JOB_NAME', 'FHEB')
        self.test_data["test_hierarchy"] = "{};{};{}".format(settings.test_hierarchy, test,job_name.split('_')[-1])
        self.report_test(test, verdict, comment)
        """ Report single test result
        :param test_report:
        :param html_report:
        """

    def report_test_set_result(self, result, reason, comment=''):
        self.test_data['end'] = int(time.time())
        logger.info(self.test_data)
        self.report_set(self.test_data, result, reason, comment)
        """ Report collective test set result """

    def clear_test_result(self, test):
        """ Reset single test result """

    def clear_report_results(self):
        """ Reset all test results in a report """

