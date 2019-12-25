import os
import sys
import json
import requests
from pprint import pprint

import Deadline.DeadlineConnect as Connect
conn = Connect.DeadlineCon('localhost', 1234)

storage_directory = os.getenv("FILE_STORAGE")


def validate_version_info(username, uid, filename, filedate, filepath):

    json_file = os.path.join(filepath, '_version.json')
    dict_version_info = {"username": username,
                         "uid": uid,
                         "filename": filename,
                         "filedate": filedate}

    if os.path.exists(json_file):
        print "Version file is exists. : %s" % json_file
        with open(json_file, 'r') as json_file:
            loaded_data = json.load(json_file)
        if sorted(dict_version_info) == sorted(loaded_data):
            print "This file is already downloaded, returning the process. : %s" % filename
            return False

    with open(json_file, 'w') as json_file:
        print "Creating version file. : %s" % json_file
        json.dumps(dict_version_info, json_file)

    return True


def get_job_data(job_code):

    token_id = os.getenv("SOCKET_ID", str())
    print "Socket ID : %s" % token_id

    url = 'https://api.renderboost.com/node/demand/job-data'
    body = {'jobcode': job_code}
    headers = {'token': str(token_id)}

    request_data = requests.post(url, data=body, headers=headers)
    pprint(request_data.json())

    return request_data.json()


def create_aria_job(job_code, python_job_id, system_options):

    username = system_options["username"]
    userpath = system_options["userpath"]
    uid = system_options["uid"]
    directlink = system_options["directlink"]
    filename = system_options["filename"]
    find = system_options["find"]
    filedate = system_options["filedate"]

    plugin = "Aria"
    output_directory = os.path.join(storage_directory, userpath, job_code)

    if not os.path.exists(output_directory):
        print "Download directory is not exist : %s" % output_directory
        print "Creating download directory"
        os.makedirs(output_directory)

    if not os.path.exists(os.path.join(output_directory, filename)):

        JobInfo = {"Name": job_code + "_Downloder",
                   "Frames": "1",
                   "Priority": 100,
                   "Plugin": plugin,
                   "BatchName": job_code + "_Batch",
                   "Whitelist": "S11",
                   "MachineLimit": 1,
                   "JobDependency0": str(python_job_id),
                   "PreJobScript": "A:/DeadlineRepository10/custom/plugins/Aria/Pre_Aria_Script.py"}

        PluginInfo = {'OutputDirectory': output_directory,
                      'DownloadLink': directlink,
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
            return new_job
        except Exception as _err:
            print("Submission failed: %s" % _err)
    else:
        return


def create_zip_job(job_code, aria_job_id, system_options):

    userpath = system_options["userpath"]
    filename = system_options["filename"]
    find = system_options["find"]

    plugin = 'RBZip'
    output_directory = os.path.join(storage_directory, userpath, job_code)

    JobInfo = {"Name": job_code + "_Extractor",
               "Frames": "1",
               "Priority": 100,
               "Plugin": plugin,
               "BatchName": job_code + "_Batch",
               "Whitelist": "S11",
               "MachineLimit": 1,
               "JobDependency0": str(aria_job_id)}

    PluginInfo = {'OutputDirectory': output_directory}

    try:
        new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
        print("Job created with id {}".format(new_job['_id']))
        return new_job
    except Exception as _err:
        print("Submission failed: %s" % _err)


def create_render_job(job_code, zip_job_id, job_options, plugin_options):
    print "Creating Render Job "


def submit_jobs(*args):
    print "Running Python Script"
    print type(args), args
    for idx, arg in enumerate(args[0]):
        print "Index : %s | Arg : %s" % (idx, arg)

    # get jobs data from API
    job_code = args[0][1]
    jobs_data = get_job_data(job_code)
    python_job_id = args[0][2]

    print "Job_Code: %s" % job_code


    system_options = jobs_data["data"]["SystemInfo"]
    for key, value in system_options.items():
        print "SysOptions Key : %s | Value : %s" % (key, value)
        if not value:
            raise ValueError("No value given for : %s" % key)

    # create aria job
    aria_job_id = create_aria_job(job_code, python_job_id, system_options)

    # create extractor job
    zip_job_id = create_zip_job(job_code, aria_job_id, system_options)

    # create render job
    job_options = jobs_data["data"]["JobInfo"]
    plugin_options = jobs_data["data"]["PluginInfo"]
    create_render_job(job_code, zip_job_id, job_options, plugin_options)


if __name__ == "__main__":
    submit_jobs(sys.argv)


