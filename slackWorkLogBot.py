import os
import time
import datetime
import operator
import logging

from webhookHandler import send
import config
import jiraHandler


logging.basicConfig(filename="slackbot.log", level=logging.INFO, format='%(asctime)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)


def createReport():

	jira_report = {}

	persons = config.persons_dict
	for person in persons.keys():
		weekday = datetime.datetime.today().weekday()
		if weekday: # not monday
			work_date = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
			jql = "project = STVCIS and worklogDate = \'{}\' and worklogAuthor = \'{}\'".format(work_date, person)
			jira_report[person] = jiraHandler.getDayWorkLog(jql, work_date, work_date, person)
		else: # monday, we take holidays to log
			work_date = (datetime.datetime.today() - datetime.timedelta(days=3)).strftime("%Y/%m/%d")
			yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
			jql = "project = STVCIS and worklogDate >= \'{}\' and worklogDate <= \'{}\' and worklogAuthor = \'{}\'".format(work_date, yesterday, person)
			jira_report[person] = jiraHandler.getDayWorkLog(jql, work_date, yesterday, person)

	slack_report = []

	for person in persons.keys():
		jira_report[person] = sorted(jira_report[person].items(), key=operator.itemgetter(0))
		slack_report.append(createPersonJson(person, jira_report[person]))

	report = {}
	slack_report[0]['pretext'] = "*Work date: {}*\n*Sprint progress*: {}".format(work_date, jiraHandler.getSprintProgress())
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

	logger.info("Bot started")
	report = {}
	report["attachments"] = [{'text': "CIS Worklog bot was started!"}]
	send(config.webhook_test, payload=report)
	send(config.webhook_test, payload=createReport())

	while True:
		try:
			weekday = datetime.datetime.today().weekday()
			now = datetime.datetime.now()
			if weekday in range(0, 4) and now.hour == 6 and now.minute == 30:
				logger.info("Sending message")
				response = send(config.webhook_url, payload=createReport())
				logger.info("Response: {}".format(response))
				time.sleep(60)
			if now.hour in (8, 10, 12, 14, 16, 18, 20, 22) and now.minute == 0:
				report = {}
				report["attachments"] = [{'text': "CIS Worklog bot is working!"}]
				logger.info("Sending status")
				response = send(config.webhook_test, payload=report)
				logger.info("Response: {}".format(response))
				time.sleep(60)
			
			time.sleep(30)
		except Exception as ex:
			logger.info("Exception: {}".format(ex))

if __name__ == "__main__":
	monitoring()
	
