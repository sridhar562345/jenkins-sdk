import os

import requests
from requests.auth import HTTPBasicAuth

JOB_NAME = "🌐 P360"

JENKINS_URL = os.environ["JENKINS_URL"]
USERNAME = os.environ["JENKINS_USERNAME"]
API_TOKEN = os.environ["JENKINS_API_TOKEN"]

session = requests.Session()
session.auth = HTTPBasicAuth(USERNAME, API_TOKEN)

# Get last build number
build = session.get(f"{JENKINS_URL}/job/{JOB_NAME}/lastBuild/api/json").json()
build_number = build["number"]

# Since your input step has fixed ID
input_id = "userConfirmation"

# Send approval with parameter
data = {
    "json": '{"parameter":[{"name":"confirm","value":true}]}',
}
params = {
    "inputId": "UserConfirmation",
}
response = session.post(
    f"{JENKINS_URL}/job/{JOB_NAME}/{build_number}/wfapi/inputSubmit",
    data=data,
    params=params,
)

print(response.status_code)
print(response.text)
