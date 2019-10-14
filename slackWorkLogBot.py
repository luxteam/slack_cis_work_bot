import os
import time
import datetime
import operator

from webhookHandler import send
import config
import jiraHandler


def createReport():

	jira_report = {}

	persons = config.persons_dict
	for person in persons.keys():
		# get day of week, 0 - monday.
		weekday = datetime.datetime.today().weekday()
		if weekday: # not monday
			# get workdate (yesterday)
			work_date = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
			# make jql for jira filter
			jql = "project = STVCIS and worklogDate = \'{}\' and worklogAuthor = \'{}\'".format(work_date, work_date, person)
			# get jira worklog for current person
			jira_report[person] = jiraHandler.getDayWorkLog(jql, work_date, work_date, person)
		else: # monday, we take holidays to log
			# get 3 days ago date, so workdate is friday
			work_date = (datetime.datetime.today() - datetime.timedelta(days=3)).strftime("%Y/%m/%d")
			# get yesterday date
			yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
			# make jql for jira filter
			jql = "project = STVCIS and worklogDate >= \'{}\' and worklogDate <= \'{}\' and worklogAuthor = \'{}\'".format(work_date, yesterday, person)
			# get jira worklog for current person
			jira_report[person] = jiraHandler.getDayWorkLog(jql, work_date, yesterday, person)

	slack_report = []

	# generate slack report message
	for person in persons.keys():
		jira_report[person] = sorted(jira_report[person].items(), key=operator.itemgetter(0))
		slack_report.append(createPersonJson(person, jira_report[person]))

	# create slack message
	report = {}
	slack_report[0]['pretext'] = "*Work date: {}*".format(work_date)
	report["attachments"] = slack_report

	return report


def createPersonJson(person, person_report):
	report = {}
	report["title"] = config.persons_dict[person]
	tickets = []
	total_time = 0
	if person_report:
		for time in person_report:
			for time_dict in time[1]:
				if time_dict['comment']:
					message = "Time: {}\nLogged time: {}\nComment: {}".format(time[0], time_dict['timeSpent'], time_dict['comment'])
				else:
					message = "Time: {}\nLogged time: {}".format(time[0], time_dict['timeSpent'])
				tickets.append({"title": "[{}] {}".format(time_dict['key'], time_dict['summary']) , "value": message, "short": False})
				total_time += time_dict['timeSpentSeconds']
		tickets.append({"title": "Total time: {}".format(str(datetime.timedelta(seconds=total_time))), "short": False})
	if total_time >= 25200: # 7h
		report["color"] = "good"
	elif total_time:
		report["color"] = "warning"
	else:
		report["color"] = "danger"
		tickets.append({"title": "No logged time", "short": False})
	report["fields"] = tickets
	report["footer"] = "Jira API"
	report["footer_icon"] = "https://platform.slack-edge.com/img/default_application_icon.png"

	return report


def monitoring():

	while True:
		try:
			weekday = datetime.datetime.today().weekday()
			now = datetime.datetime.now()
			if weekday in range(0, 4) and now.hour == 9 and now.minute == 30:
				send(payload=createReport())
				time.sleep(60)
			
			time.sleep(30)
		except Exception as ex:
			print(ex)

if __name__ == "__main__":
	monitoring()
	
