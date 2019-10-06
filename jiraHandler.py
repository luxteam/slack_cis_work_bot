import time
import config
from datetime import datetime
from jira import JIRA


def createJiraClient():
	jira_options = {'server': config.jira_host}
	return JIRA(options=jira_options, basic_auth=(config.username, config.password))


def getDayWorkLog(jql):
	jira = createJiraClient()
	issues_list = jira.search_issues(jql)
	day_worklog = {'aalekseevich': [], 'askravchenko': [], 'dgalkin': []}
	for issue in issues_list:
		ticket = jira.issue(issue.key)
		worklogs = ticket.fields.worklog.worklogs
		for worklog in worklogs:
			if datetime.strptime(worklog.updated[:19], '%Y-%m-%dT%H:%M:%S').strftime("%Y/%m/%d") == date:
				day_worklog[worklog.author.key].append([issue.key, issue.fields.summary, worklog.timeSpent])
	return day_worklog



