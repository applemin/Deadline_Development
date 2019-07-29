from Deadline.Scripting import MonitorUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog


def __main__():
    """Monitor based job script to copy selected job ids
    to the system clipboard."""
    selected_jobs = MonitorUtils.GetSelectedJobs()

    if selected_jobs:
        job_ids = []
        for job in selected_jobs:
            job_ids.append(job.ID)

        str_job_ids = '\n'.join(job_ids)

        script_dialog = DeadlineScriptDialog()
        script_dialog.CopyToClipboard(str_job_ids)
