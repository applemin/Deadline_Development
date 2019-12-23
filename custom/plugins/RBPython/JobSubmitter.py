import sys
import Deadline.DeadlineConnect as Connect
conn = Connect.DeadlineCon('localhost', 1234)


def submit_jobs(*args):
    print "Running Python Script"
    print "Args: ", args

    # # api-endpoint
    # URL="http://maps.googleapis.com/maps/api/geocode/json"
    #
    # # location given here
    # location="delhi technological university"
    #
    # # defining a params dict for the parameters to be sent to the API
    # PARAMS={'address': location}
    #
    # # sending get request and saving the response as response object
    # r=requests.get(url=URL, params=PARAMS)
    #
    # # extracting data in json format
    # data=r.json()
    #
    # # extracting latitude, longitude and formatted address
    # # of the first matching location
    # latitude=data['results'][0]['geometry']['location']['lat']
    # longitude=data['results'][0]['geometry']['location']['lng']
    # formatted_address=data['results'][0]['formatted_address']
    #
    # # printing the output
    # print("Latitude:%s\nLongitude:%s\nFormatted Address:%s" % (latitude, longitude, formatted_address))


if __name__ == "__main__":
    submit_jobs(sys.argv)

# JOB_NAME = 'Ping Localhost'
# CMD_APP = r'c:\windows\system32\cmd.exe'
# CMD_ARG = r'/c ping localhost'
#
# JobInfo = {
#     "Name": JOB_NAME,
#     "Frames": "1",
#     "Plugin": "CommandLine"
#     }
#
# PluginInfo = {
#     'Shell': 'default',
#     'ShellExecute': False,
#     'StartupDirectory': '',
#     'Executable': CMD_APP,
#     'Arguments': CMD_ARG
#     }
#
# try:
#     new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
#     print("Job created with id {}".format(new_job['_id']))
# except:
#     print("Submission failed")
