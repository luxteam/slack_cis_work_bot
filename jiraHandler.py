import time
import config
import requests
import datetime
from jira import JIRA


# create jira client connection
def createJiraClient():
	jira_options = {'server': config.jira_host}
	return JIRA(options=jira_options, basic_auth=(config.jira_username, config.jira_token))


# get ticket json, api doesn't return worklog, so we use get request to jira server
def getTicketWorklog(ticket):
	response = requests.get("{}/rest/api/2/issue/{}/worklog".format(config.jira_host ,ticket), auth=(config.jira_username, config.jira_token))
	worklogs = response.json()['worklogs']
	return worklogs


# return daily worklog using jql, date and person name.
def getDayWorkLog(jql, friday_or_yesterday_date, sunday_or_yesterday_date, person):
	jira = createJiraClient()
	issues_list = jira.search_issues(jql)
	day_worklog = {}
	for issue in issues_list:
		worklogs = getTicketWorklog(issue.key)
		for worklog in worklogs:
			worklog_date = datetime.datetime.strptime(worklog['started'][:19], '%Y-%m-%dT%H:%M:%S').strftime("%Y/%m/%d")
			if worklog_date >= friday_or_yesterday_date and worklog_date <= sunday_or_yesterday_date and worklog['author']['key'] == person:
				worklog_time = datetime.datetime.strptime(worklog['started'][:19], '%Y-%m-%dT%H:%M:%S').strftime("%H:%M:%S")
				
				comment = ''
				if 'comment' in worklog.keys():
					comment = worklog['comment']

				worklog_dict = {'key': issue.key, 'summary': issue.fields.summary, 'comment': comment, 'timeSpent': worklog['timeSpent'], 'timeSpentSeconds': worklog['timeSpentSeconds']}
				if worklog_time in day_worklog.keys():
					day_worklog[worklog_time].append(worklog_dict)
				else:
					day_worklog[worklog_time] = [worklog_dict]
	return day_worklog




