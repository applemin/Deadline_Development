import os
import sys
import json
import requests

import Deadline.DeadlineConnect as Connect
conn = Connect.DeadlineCon('localhost', 1234)


def get_job_data(job_code):

    token_id = os.environ['SOCKET_ID']

    url = 'https://get_data'
    body = {'': ''}
    headers = {'': ''}

    request_data = requests.post(url, data=json.dumps(body), headers=headers)

    return request_data

def create_aria_job(system_options):

    JobInfo = {"Name": "Aria_Test_Job",
               "Frames": "1",
               "Priority": 100,
               "Plugin": "Aria",
               "BatchName": "Test_Batch"}

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

    """
    Name = Laptop Animation_NORMAL
    UserName = renderboost
    Whitelist = S11
    MachineLimit = 1
    MachineName = S11
    OutputDirectory0 = A:/AriaTest
    PreJobScript = A:/DeadlineRepository10/custom/plugins/Aria/Pre_Aria_Script.py
    """

    try:
        new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
        print("Job created with id {}".format(new_job['_id']))
    except Exception as _err:
        print("Submission failed: %s" % _err)


def submit_jobs(*args):
    print "Running Python Script"
    for idx, arg in args:
        print "Index : %s |Arg : %s " % (idx, arg)

    # get jobs data from API
    # jobs_data = get_job_data(args[1])

    # create aria job
    system_options = list()
    create_aria_job(system_options)


if __name__ == "__main__":
    submit_jobs(sys.argv)


