import os
import sys
import json
import requests
from pprint import pprint

import Deadline.DeadlineConnect as Connect
conn = Connect.DeadlineCon('localhost', 1234)


def get_job_data(job_code):

    token_id = os.environ['SOCKET_ID']

    url = 'https://api.renderboost.com/node/demand/job-data'
    body = {'jobcode': job_code}
    headers = {'token': token_id}

    request_data = requests.post(url, data=json.dumps(body), headers=headers)
    pprint(request_data)

    return request_data


def create_aria_job(system_options):

    JobInfo = {"Name": "Aria_Test_Job",
               "Frames": "1",
               "Priority": 100,
               "Plugin": "Aria",
               "BatchName": "Test_Batch",
               "Whitelist": "S11",
               "MachineLimit": 1,
               "OutputDirectory0": "A:/AriaTest",
               "PreJobScript": "A:/DeadlineRepository10 / custom / plugins / Aria / Pre_Aria_Script.py"}

    PluginInfo = {'OutputDirectory': '',
                  'DownloadLink': '',
                  'Version': 2,
                  'Log': '',
                  'DryRun': False,
                  'OutputFilename': '',
                  'ServerConnections': 1,
                  'SplitConnections': 5,
                  'ServerTimeStamp': True,
                  'Timeout': 60}

    try:
        new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
        print("Job created with id {}".format(new_job['_id']))
    except Exception as _err:
        print("Submission failed: %s" % _err)


def create_render_job(job_info, plugin_info):
    pass


def submit_jobs(*args):
    print "Running Python Script"
    for idx, arg in enumerate(args):
        print "Index : %s |Arg : %s " % (idx, arg)

    # get jobs data from API
    jobs_data = get_job_data(args[1])
    print "Job_Code: %s" % args[1]

    # create aria job
    system_options = dict()
    create_aria_job(system_options)

    # create render job
    job_options = dict()
    plugin_options = dict()
    create_render_job(job_options, plugin_options)


if __name__ == "__main__":
    submit_jobs(sys.argv)


