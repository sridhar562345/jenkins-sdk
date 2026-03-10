import os

from jira import JIRA

JIRA_SERVER = os.environ["JIRA_SERVER"]
JIRA_USERNAME = os.environ["JIRA_USERNAME"]
JIRA_API_KEY = os.environ["JIRA_API_KEY"]

jiraOptions = {"server": JIRA_SERVER}
jira = JIRA(
    options=jiraOptions,
    basic_auth=(JIRA_USERNAME, JIRA_API_KEY),
)


def search_issues():
    for singleIssue in jira.search_issues(
        jql_str="status NOT IN (Closed, Done) AND assignee = 712020:e2943fc0-418c-4ff3-972c-9ab4caf57bd4 ORDER BY updated DESC"
    ):
        print(
            "{}: {}: {}".format(
                singleIssue.key,
                singleIssue.fields.description,
                singleIssue.fields.summary,
                singleIssue.fields.reporter.displayName,
            )
        )


def get_issue_by_ticket(ticket_id):
    issue = jira.issue(id=ticket_id)
    return issue.fields.description


if __name__ == "__main__":
    issue = jira.issue(id="15275")
    print(issue.fields.description)
