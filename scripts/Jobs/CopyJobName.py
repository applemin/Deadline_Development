from Deadline.Scripting import MonitorUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog


def __main__():
    """Monitor based job script to copy selected job names
    to the system clipboard."""
    selected_jobs = MonitorUtils.GetSelectedJobs()

    if selected_jobs:
        job_names = []
        for job in selected_jobs:
            job_names.append(job.JobName)

        str_job_names = '\n'.join(job_names)

        script_dialog = DeadlineScriptDialog()
        script_dialog.CopyToClipboard(str_job_names)
