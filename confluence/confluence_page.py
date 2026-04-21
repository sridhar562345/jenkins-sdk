# Fetch content
import os

import requests

# JIRA_SERVER = os.environ["JIRA_SERVER"]
JIRA_USERNAME = os.environ["JIRA_USERNAME"]
JIRA_API_KEY = os.environ["JIRA_API_KEY"]

auth = (JIRA_USERNAME, JIRA_API_KEY)

url = "https://reyahealth.atlassian.net/wiki/rest/api/content/4069228553?expand=body.storage"
res = requests.get(url, auth=auth)
content = res.json()["body"]["storage"]["value"]
print(content)
