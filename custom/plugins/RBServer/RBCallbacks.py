import os
import sys
import json
import time
import requests
from pprint import pprint
from datetime import datetime
for path in sys.path: print path

SOCKET_ID = os.getenv("SOCKET_ID")

class JobType:
    animation    = u"1"
    still_frame  = u"2"
    multi_task   = u"3"
    free_service = u"4"

_MAPPED_STATUSES = {
    0:  'system_unknown',
    1:  'deadline_rendering',
    2:  'deadline_suspended',
    3:  'deadline_completed',
    4:  'deadline_failed',
    5:  'system_requeue',
    6:  'deadline_pending',
    7:  'deadline_queued',
    8:  'client_uploading',
    9:  'system_uploaded',
    10: 'local_published',
    11: 'unzip_failed',
    12: 'download_failed',
    13: 'system_failed',
    14: 'failed_online',
    15: 'system_pending',
    16: 'local_queued',
    18: 'file_not_found',
    19: 'initializing',
    25: 'system_cancelled',
    50: 'system_deleted',
}

class Operations:

    OnJobSubmitted      = "OnJobSubmitted"
    OnJobStarted        = "OnJobStarted"
    OnJobFinished       = "OnJobFinished"
    OnJobRequeued       = "OnJobRequeued"
    OnJobFailed         = "OnJobFailed"
    OnJobSuspended      = "OnJobSuspended"
    OnJobResumed        = "OnJobResumed"
    OnJobPended         = "OnJobPended"
    OnJobReleased       = "OnJobReleased"
    OnJobDeleted        = "OnJobDeleted"
    OnJobError          = "OnJobError"
    OnJobPurged         = "OnJobPurged"

    OnHouseCleaning     = "OnHouseCleaning"
    OnRepositoryRepair  = "OnRepositoryRepair"

    OnSlaveStarted      = "OnSlaveStarted"
    OnSlaveStopped      = "OnSlaveStopped"
    OnSlaveIdle         = "OnSlaveIdle"
    OnSlaveRendering    = "OnSlaveRendering"
    OnSlaveStartingJob  = "OnSlaveStartingJob"
    OnSlaveStalled      = "OnSlaveStalled"

    OnIdleShutdown      = "OnIdleShutdown"
    OnMachineStartup    = "OnMachineStartup"
    OnThermalShutdown   = "OnThermalShutdown"
    OnMachineRestart    = "OnMachineRestart"

    OnTaskFinished      = "OnTaskFinished"

class Status:

    system_unknown      = 0
    deadline_rendering  = 1
    deadline_suspended  = 2
    deadline_completed  = 3
    deadline_failed     = 4
    system_requeue      = 5
    deadline_pending    = 6
    deadline_queued     = 7
    client_uploading    = 8
    system_uploaded     = 9
    local_published     = 10
    unzip_failed        = 11
    download_failed     = 12
    system_failed       = 13
    failed_online       = 14
    system_pending      = 15
    local_queued        = 16
    file_not_found      = 18
    initializing        = 19
    system_cancelled    = 25
    system_deleted      = 50

    def __init__(self):
        self.status_dict = self._status_dict()

    def _status_dict(self):
        dict_status = {"system_unknown": self.system_unknown,
                       "deadline_rendering": self.deadline_rendering,
                       "deadline_suspended": self.deadline_suspended,
                       "deadline_completed": self.deadline_completed,
                       "deadline_failed": self.deadline_failed,
                       "system_requeue": self.system_requeue,
                       "deadline_pending": self.deadline_pending,
                       "deadline_queued": self.deadline_queued,
                       "client_uploading": self.client_uploading,
                       "system_uploaded": self.system_uploaded,
                       "local_published": self.local_published,
                       "unzip_failed": self.unzip_failed,
                       "download_failed": self.download_failed,
                       "system_failed": self.system_failed,
                       "failed_online": self.failed_online,
                       "system_pending": self.system_pending,
                       "local_queued": self.local_queued,
                       "file_not_found": self.file_not_found,
                       "initializing": self.initializing,
                       "system_cancelled": self.system_cancelled,
                       "system_deleted": self.system_deleted}

        return dict_status


class APIController:

    # API Links
    _api_base_link              = "https://api.renderboost.com/node/demand/"
    _update_status_link         = _api_base_link + "change-state"
    _update_progress_link       = _api_base_link + "percent"
    _validate_job_link          = _api_base_link + "valid-job"
    _update_line_id_link        = _api_base_link + "change-job-id"
    _submit_error_link          = _api_base_link + "set-error"
    _get_job_data_link          = _api_base_link + "job-data"
    _anim_task_update_link      = _api_base_link + "animation-task-time"
    _still_task_update_link     = _api_base_link + "still-frame-task-time"
    _cloud_share_link           = _api_base_link + "share-folder"

    def __init__(self, token, job_code):

        self._initializing_job = ("_Submitter", "_Extractor", "_Downloader")
        self.token = token
        self._job_code = job_code

    @property
    def is_initializing_job(self):
        return self._job_code.endswith(self._initializing_job)

    @property
    def job_code(self):
        if "_Submitter" in self._job_code:
            return self._job_code.split("_Submitter")[0]
        elif "_Extractor" in self._job_code:
            return self._job_code.split("_Extractor")[0]
        elif "_Downloader" in self._job_code:
            return self._job_code.split("_Downloader")[0]
        else:
            return self._job_code

    def validate_job(self):
        print "calling %s" % self.validate_job.__name__
        url = self._validate_job_link
        params = {'jobcode': self.job_code}
        response = self.call_post(url, params)

        if not response["status"]:
            raise ValueError("Job is `Unknown`.")
        print _MAPPED_STATUSES[response["status"]]
        return _MAPPED_STATUSES[response["status"]]

    def cloud_share(self):
        print "calling %s" % self.cloud_share.__name__
        url = self._cloud_share_link
        params = {'jobcode': self.job_code}
        response = self.call_post(url, params)

        if response["status"]:
            print "Cloud folder for job `%s` has been shared successfully." % self.job_code
        else:
            raise ValueError("Could not share cloud folder for job `%s` : `%s`" % (self.job_code, response["msg"]))

        return response["status"]

    def get_job_data(self):
        print "calling %s" % self.get_job_data.__name__
        url = self._get_job_data_link
        params = {'jobcode': self.job_code}
        response = self.call_post(url, params)

        if not response["status"]:
            raise ValueError(response["msg"])

        return response["data"]

    def update_status(self, new_status):
        print "calling %s" % self.update_status.__name__
        url = self._update_status_link
        params = {'jobcode': self.job_code,
                  'state': new_status}
        response = self.call_post(url, params)

        if new_status not in _MAPPED_STATUSES.keys():
            raise ValueError("No status found for ID :`%s`." % new_status)

        if response["status"]:
            print "Job status changed to `%s` successfully." % _MAPPED_STATUSES[new_status]
        else:
            raise ValueError("Job status could not be changed to `%s` : `%s`" % (new_status, response["msg"]))

        return response["status"]

    def update_progress(self, value):
        print "calling %s" % self.update_progress.__name__
        url = self._update_progress_link
        params = {'jobcode': self.job_code,
                  'percent': value}
        response = self.call_post(url, params)

        if not isinstance(value, int):
            raise ValueError("Only `int` values are accepted: `%s`" % value)

        if response["status"]:
            print "Job progress changed to `%s` successfully." % value
        else:
            raise ValueError("Job progress could not be changed to `%s` : `%s`" % (value, response["msg"]))

        return response["status"]

    def update_line_id(self, _id):
        print "calling %s" % self.update_line_id.__name__
        url = self._update_line_id_link
        params = {'jobcode': self.job_code,
                  'lineid': _id}
        response = self.call_post(url, params)

        if response["status"]:
            print "Line ID changed to `%s` successfully." % _id
        else:
            raise ValueError("Line ID could not be changed to `%s` : `%s`" % (_id, response["msg"]))

        return response["status"]

    def submit_error(self):
        pass

    def update_anim_task(self, task_id, frame_number, render_time, cpu_usage):
        print "calling %s" % self.update_anim_task.__name__
        url = self._anim_task_update_link
        params = {'jobcode': self.job_code,
                  'task_id': task_id,
                  'frame': frame_number,
                  'minutes': render_time,
                  'cpu': cpu_usage
                  }
        response = self.call_post(url, params)

        if response["status"]:
            print "Animation task updated successfully for job `%s`." % self.job_code
            print "Task ID : %s | Frame Number : %s | Render Time : %s | CPU Usage : %s" % (task_id,
                                                                                            frame_number,
                                                                                            render_time,
                                                                                            cpu_usage)
        else:
            print "Task ID : %s | Frame Number : %s | Render Time : %s | CPU Usage : %s" % (task_id,
                                                                                            frame_number,
                                                                                            render_time,
                                                                                            cpu_usage)
            raise ValueError("Animation task could not be updated : `%s`" % response["msg"])

        return response["status"]

    def update_still_task(self, task_id, frame_number, render_time, cpu_usage):
        print "calling %s" % self.update_still_task.__name__
        url = self._still_task_update_link
        params = {'jobcode': self.job_code,
                  'task_id': task_id,
                  'frame': frame_number,
                  'minutes': render_time,
                  'cpu': cpu_usage
                  }
        response = self.call_post(url, params)

        if response["status"]:
            print "Animation task updated successfully for job `%s`." % self.job_code
            print "Task ID : %s | Frame Number : %s | Render Time : %s | CPU Usage : %s" % (task_id,
                                                                                            frame_number,
                                                                                            render_time,
                                                                                            cpu_usage)
        else:
            print "Task ID : %s | Frame Number : %s | Render Time : %s | CPU Usage : %s" % (task_id,
                                                                                            frame_number,
                                                                                            render_time,
                                                                                            cpu_usage)
            raise ValueError("Animation task could not be updated : `%s`" % response["msg"])

        return response["status"]

    def call_post(self, url, params):
        print "Token: %s" % self.token
        print "Params: %s" % params
        headers = {'token': self.token}
        request_data = requests.post(url, data=params, headers=headers)
        pprint(request_data.json())
        return request_data.json()


def get_task_data():

    host_name = os.getenv("DEADLINE_SERVER")
    port_number = os.getenv("DEADLIN_PORT")

    print "DEADLINE_SERVER", host_name, "DEADLIN_PORT", port_number

    Deadline = Connect.DeadlineCon(host_name, port_number)
    task_data = Deadline.Tasks.GetJobTask(job_id, task_id)

    print "Printing task data from deadline "
    pprint(task_data)

    def parse_time(_time):
        _time = "-".join(_time.split("-")[:-1])
        if "." in _time:
            _time.split(".")[0]
        return _time

    # export render time from task times
    time_format = "%Y-%m-%dT%H:%M:%S"
    start_time = parse_time(task_data["StartRen"])
    o_start = datetime.strptime(start_time.split(".")[0], time_format)
    comp_time = parse_time(task_data["Comp"])
    o_comp = datetime.strptime(comp_time.split(".")[0], time_format)
    delta_time = o_comp - o_start
    render_time = round(float(delta_time.seconds)/60, 2)
    print "Extracted task render time, start : %s | comp : %s result : %s" % (start_time, comp_time, delta_time)

    # export frame number
    start_frame, end_frame = task_data["Frames"].split("-")

    if start_frame == end_frame:
        _frames = start_frame
    else:
        _frames = task_data["Frames"]
    print "Extracted task frames : %s " % _frames

    # export cpu usage
    cpu_usage = task_data["CpuPer"]
    print "Extracted task cpu usage : %s" % cpu_usage

    return _frames, render_time, cpu_usage


def get_job_progress():

    host_name = os.getenv("DEADLINE_SERVER")
    port_number = os.getenv("DEADLIN_PORT")

    print "DEADLINE_SERVER", host_name, "DEADLIN_PORT", port_number

    Deadline = Connect.DeadlineCon(host_name, port_number)
    job_data = Deadline.Jobs.GetJob(job_id)

    total_tasks = job_data["Props"]["Tasks"]
    completed_tasks = job_data["CompletedChunks"]
    progress_percent = (int(completed_tasks) * 100)/int(total_tasks)
    print "Number of Tasks : %s " % total_tasks
    print "Number of Completed Tasks : %s " % completed_tasks
    print "Job Completion in Percent : %s " % progress_percent

    return progress_percent, total_tasks


if __name__ == "__main__":

    _, job_id, job_name, job_status, operation, task_id = sys.argv

    API = APIController(SOCKET_ID, job_name)

    #   TODO:need to verify line id
    if API.validate_job():
        if operation in [Operations.OnTaskFinished, Operations.OnHouseCleaning]:

            import Deadline.DeadlineConnect as Connect

            value,  number_of_tasks = get_job_progress()
            print "Updating job progress for: `%s` with value : `%s`." % (job_name, value)
            API.update_progress(value)

            if operation == Operations.OnTaskFinished:
                if number_of_tasks > 1:
                    print "Updating animation task : `%s` for job ID : `%s`." % (task_id, job_name)
                    frames, render_time, cpu_usage = get_task_data()
                    # incrementing task id by one as online data base is not zero index
                    API.update_anim_task(str(int(task_id) + 1), frames, render_time, cpu_usage)
                else:
                    "This is still frame job , skipping animation task update."
            elif operation == Operations.OnHouseCleaning:
                print "Updating still frame task : `%s` for job ID : `%s`." % (task_id, job_name)
                frames, render_time, cpu_usage = get_task_data()
                #   TODO:update still frame time
                print "Updating still frame task : `%s` for job ID : `%s`." % (task_id, job_name)

                # incrementing task id by one as online data base is not zero index
                #API.update_anim_task(str(int(task_id) + 1), frames, render_time, cpu_usage)

        elif operation == Operations.OnJobStarted:
            # register new job ID to integrate server side controllers
            API.update_line_id(job_id)
            if API.is_initializing_job:
                print "Initializing job : `%s` with ID : `%s` is started." % (job_name, job_id)
                API.update_status(Status.initializing)
            else:
                API.update_status(Status.deadline_rendering)
        elif operation == Operations.OnJobDeleted:
            pass
        elif operation == Operations.OnJobError:
            pass
        elif operation == Operations.OnJobFailed:
            if API.is_initializing_job:
                print "Initializing job : `%s` with ID : `%s` is failed." % (job_name, job_id)
                #   TODO :need to send error to API
                API.update_status(Status.deadline_failed)
            else:
                API.update_status(Status.deadline_failed)
        elif operation == Operations.OnJobFinished:
            if API.is_initializing_job:
                print "Initializing job : `%s` with ID : `%s` is completed." % (job_name, job_id)
            else:
                API.update_status(Status.deadline_completed)
        elif operation == Operations.OnJobPended:
            if API.is_initializing_job:
                print "Initializing job : `%s` with ID : `%s` is pended." % (job_name, job_id)
            else:
                API.update_status(Status.deadline_pending)
        elif operation == Operations.OnJobPurged:
            pass
        elif operation == Operations.OnJobReleased:
            pass
        elif operation == Operations.OnJobRequeued:
            if API.is_initializing_job:
                print "Initializing job : `%s` with ID : `%s` is re-queued." % (job_name, job_id)
                API.update_status(Status.deadline_queued)
            else:
                API.update_status(Status.deadline_queued)
        elif operation == Operations.OnJobResumed:
            if API.is_initializing_job:
                print "Initializing job : `%s` with ID : `%s` is re-queued." % (job_name, job_id)
                API.update_status(Status.initializing)
            else:
                API.update_status(Status.deadline_rendering)
        elif operation == Operations.OnJobSubmitted:
            pass
        elif operation == Operations.OnJobSuspended:
            if API.is_initializing_job:
                print "Initializing job : `%s` with ID : `%s` is suspended." % (job_name, job_id)
                API.update_status(Status.deadline_suspended)
            else:
                API.update_status(Status.deadline_suspended)
    else:
        print "Job could not be found on online system : %s" % job_name
