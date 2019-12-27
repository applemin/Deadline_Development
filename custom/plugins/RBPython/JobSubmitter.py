import os
import sys
import json
import requests
from pprint import pprint

import Deadline.DeadlineConnect as Connect
conn = Connect.DeadlineCon('localhost', 1234)

job_code = str()
storage_directory = os.getenv("FILE_STORAGE")
cloud_directory = os.getenv("CLOUD_DIRECTORY")


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

        JobInfo = {"Name": job_code + "_Downloader",
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
            return new_job['_id']
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
    zip_file = os.path.join(output_directory, filename)

    JobInfo = {"Name": job_code + "_Extractor",
               "Frames": "1",
               "Priority": 100,
               "Plugin": plugin,
               "BatchName": job_code + "_Batch",
               "Whitelist": "S11",
               "MachineLimit": 1,
               "JobDependency0": str(aria_job_id)}

    PluginInfo = {'ZipFile': zip_file,
                  'OutputDirectory': output_directory}

    try:
        new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
        print("Job created with id {}".format(new_job['_id']))
        return new_job['_id']
    except Exception as _err:
        print("Submission failed: %s" % _err)


def create_cloud_directory():

    cloud_job_folder = os.path.join(cloud_directory, job_code)
    if not os.path.exists(cloud_job_folder):
        os.makedirs(cloud_job_folder)
        print "Job folder created in cloud : %s" % cloud_job_folder

    return cloud_job_folder


def get_scene_file(scene_file_name):

    base_job_dir = os.path.join(storage_directory, job_code)
    scene_file_path = str()

    if os.path.exists(base_job_dir):
        print "Job directory is exists: %s" % base_job_dir
    else:
        raise Exception("Job folder is not exist in storage %s" % base_job_dir)

    for (dir_path, dir_names, file_names) in os.walk(base_job_dir):
        scene_file_path = [os.path.join(dir_path, _file) for _file in file_names if _file == scene_file_name]
        print "Scene file path found : %s " % scene_file_path

    return scene_file_path


def get_extra_options(scene_file_name, job_options, plugin_options):

    output_directory = create_cloud_directory()
    scene_file = get_scene_file(scene_file_name)

    extra_job_options = {"OutputDirectory0": output_directory}

    extra_plugin_options = {"OutputFile": os.path.join(output_directory, job_options["OutputFilename0"]),
                            "SceneFile": scene_file}

    if job_options["Plugin"] == "RBKeyshot":
        return extra_job_options, extra_plugin_options
    elif job_options["Plugin"] == "Keyshot":
        return extra_job_options, extra_plugin_options
    else:
        return extra_job_options, extra_plugin_options


def create_render_job(job_code, zip_job_id, scene_file_name, job_options, plugin_options):

    print "Creating Render Job "
    extra_job_options, extra_plugin_options = get_extra_options(scene_file_name, job_options, plugin_options)

    JobInfo = {"BatchName": job_code + "_Batch",
               "JobDependency0": str(zip_job_id)}
    JobInfo.update(job_options)
    JobInfo.update(extra_job_options)

    PluginInfo = dict()
    PluginInfo.update(plugin_options)
    PluginInfo.update(extra_plugin_options)

    try:
        new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
        print("Job created with id {}".format(new_job['_id']))
        return new_job['_id']
    except Exception as _err:
        print("Submission failed: %s" % _err)


def submit_jobs(*args):

    print "Running Python Script"
    print type(args), args

    global job_code
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
    scene_file_name = jobs_data["data"]["SystemInfo"]["find"]
    plugin_options = jobs_data["data"]["PluginInfo"]
    render_job_id = create_render_job(job_code,
                                      zip_job_id,
                                      scene_file_name,
                                      job_options,
                                      plugin_options)


if __name__ == "__main__":
    submit_jobs(sys.argv)


