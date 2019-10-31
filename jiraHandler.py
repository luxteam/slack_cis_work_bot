import time
import config
import requests
import datetime
from jira import JIRA


# create jira client connection
def createJiraClient():
	jira_options = {'server': config.jira_host}
	return JIRA(options=jira_options, basic_auth=(config.jira_username, config.jira_token))


def getActiveSprintId():
	jira_client = createJiraClient()
	# STVCIS Board ID = 1577
	all_board_sprints = jira_client.sprints(1577)
	jira_client.close()
	for sprint in all_board_sprints:
		if sprint.state == "ACTIVE":
			return sprint.id


def getSprintInfo(sprint_id):
	response = requests.get("{}/rest/agile/1.0/sprint/{}".format(config.jira_host, sprint_id), auth=(config.jira_username, config.jira_token))
	sprint_info = response.json()
	return sprint_info


def getIssuesListFronJQL(jql):
	jira_client = createJiraClient()
	issue_dict = jira_client.search_issues(jql, maxResults=100, json_result=True)

	issues_keys = []
	for i in issue_dict['issues']:
		issues_keys.append(i['key'])

	startAt = 100
	while len(issue_dict['issues']) == 100:
		issue_dict = jira_client.search_issues(jql, startAt=startAt, maxResults=100, json_result=True)
		for i in issue_dict['issues']:
			issues_keys.append(i['key'])
		startAt += 100

	jira_client.close()
	return issues_keys


# get ticket json, api doesn't return worklog, so we use get request to jira server
def getTicketWorklog(ticket):
	response = requests.get("{}/rest/api/2/issue/{}/worklog".format(config.jira_host ,ticket), auth=(config.jira_username, config.jira_token))
	worklogs = response.json()['worklogs']
	return worklogs


def getIssueInfo(ticket):
	response = requests.get("https://adc.luxoft.com/jira/rest/api/2/issue/{}".format(ticket), auth=(config.jira_username, config.jira_token))
	issueInfo = response.json()
	return issueInfo


def getSprintProgress():
	sprint_id = getActiveSprintId()
	if sprint_id:
		sprint_info = getSprintInfo(sprint_id)
		jql = "project = STVCIS and sprint = {}".format(sprint_id)
		issues_list = getIssuesListFronJQL(jql)
		total_estimation, total_log_time, cis_total_time, cis_log_time = (0, 0, 0, 0)
		for issue in issues_list:
			issueInfo = getIssueInfo(issue)
			worklogs = getTicketWorklog(issueInfo['key'])
			if type(issueInfo['fields']['aggregatetimeoriginalestimate']) == int:
				if 'CIS Maintenance' in issueInfo['fields']['summary']:
					cis_total_time += issueInfo['fields']['aggregatetimeoriginalestimate']
				else:
					total_estimation += issueInfo['fields']['aggregatetimeoriginalestimate']

				issueLogTime = 0
				for worklog in worklogs:
					if worklog['started'] >= sprint_info['startDate'] and worklog['started'] <= sprint_info['endDate']:
						issueLogTime += worklog['timeSpentSeconds']

				if issueInfo['fields']['status']['name'] in ('Resolved', 'Closed'):
					total_log_time += issueInfo['fields']['aggregatetimeoriginalestimate']
				elif issueLogTime < issueInfo['fields']['aggregatetimeoriginalestimate']:
					total_log_time += issueLogTime
				else:
					total_log_time += issueInfo['fields']['aggregatetimeoriginalestimate']
			else:
				for worklog in worklogs:
					cis_log_time += worklog['timeSpentSeconds']

		total_estimation += cis_total_time
		if cis_log_time < cis_total_time:
			total_log_time += cis_log_time
		else:
			total_log_time += cis_total_time

		progress = round(total_log_time/total_estimation, 2)
	else:
		progress = 0
	return "{}%".format(progress*100)



# return daily worklog using jql, date and person name.
def getDayWorkLog(jql, friday_or_yesterday_date, sunday_or_yesterday_date, person):
	issues_list = getIssuesListFronJQL(jql)
	day_worklog = {}
	for issue in issues_list:
		issueInfo = getIssueInfo(issue)
		worklogs = getTicketWorklog(issue)
		for worklog in worklogs:
			worklog_date = datetime.datetime.strptime(worklog['started'][:19], '%Y-%m-%dT%H:%M:%S').strftime("%Y/%m/%d")
			if worklog_date >= friday_or_yesterday_date and worklog_date <= sunday_or_yesterday_date and worklog['author']['key'] == person:
				worklog_time = datetime.datetime.strptime(worklog['started'][:19], '%Y-%m-%dT%H:%M:%S').strftime("%H:%M:%S")
				
				comment = ''
				if 'comment' in worklog.keys():
					comment = worklog['comment']

				parent_key, parent_summary = ('', '')
				if 'parent' in issueInfo['fields'].keys():
					parent_key = issueInfo['fields']['parent']['key']
					parent_summary = issueInfo['fields']['parent']['fields']['summary']

				worklog_dict = {'key': issueInfo['key'], 'summary': issueInfo['fields']['summary'], 'parent_key': parent_key, 'parent_summary': parent_summary, \
						'timeSpent': worklog['timeSpent'], 'timeSpentSeconds': worklog['timeSpentSeconds'], 'comment': comment}

				if worklog_time in day_worklog.keys():
					day_worklog[worklog_time].append(worklog_dict)
				else:
					day_worklog[worklog_time] = [worklog_dict]

	return day_worklog




