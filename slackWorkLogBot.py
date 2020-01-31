import os
import time
import datetime
import operator

from webhookHandler import send
import config
import jiraHandler


def createReport(persons, project):

	jira_report = {}

	for person in persons.keys():
		weekday = datetime.datetime.today().weekday()
		if weekday: # not monday
			work_date = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
			jql = "project = {} and worklogDate = \'{}\' and worklogAuthor = \'{}\'".format(project, work_date, person)
			jira_report[person] = jiraHandler.getDayWorkLog(jql, work_date, work_date, person)
		else: # monday, we take holidays to log
			work_date = (datetime.datetime.today() - datetime.timedelta(days=3)).strftime("%Y/%m/%d")
			yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
			jql = "project = {} and worklogDate >= \'{}\' and worklogDate <= \'{}\' and worklogAuthor = \'{}\'".format(project, work_date, yesterday, person)
			jira_report[person] = jiraHandler.getDayWorkLog(jql, work_date, yesterday, person)

	slack_report = []

	for person in persons.keys():
		jira_report[person] = sorted(jira_report[person].items(), key=operator.itemgetter(0))
		slack_report.append(createPersonJson(persons[person], person, jira_report[person]))

	report = {}
	if project == 'STVCIS':
		slack_report[0]['pretext'] = "*Work date: {}*\n*Sprint progress*: {}".format(work_date, jiraHandler.getSprintProgress())
	else:
		slack_report[0]['pretext'] = "*Work date: {}*".format(work_date)

	report["attachments"] = slack_report

	return report


def createPersonJson(name, username, person_report):
	report = {}
	report["title"] = name

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


def sendDirectMessage(text):
	report = {}
	report["attachments"] = [{'text': text}]
	send(config.test_webhook_url, payload=report)


def monitoring():

	sendDirectMessage("CIS/ART Worklog bot was started!")	

	#cis_response = send(config.test_webhook_url, payload=createReport(config.cis_persons_dict, 'STVCIS'))
	#sendDirectMessage("CIS response: {}".format(cis_response))
	#art_response = send(config.test_webhook_url, payload=createReport(config.art_persons_dict, 'STVART'))
	#sendDirectMessage("ART response: {}".format(art_response))

	while True:
		try:
			weekday = datetime.datetime.today().weekday()
			now = datetime.datetime.now()
			if weekday in range(0, 5) and now.hour == 6 and now.minute == 30:

				cis_response = send(config.cis_webhook_url, payload=createReport(config.cis_persons_dict, 'STVCIS'))
				sendDirectMessage("CIS response: {}".format(cis_response))
				art_response = send(config.art_webhook_url, payload=createReport(config.art_persons_dict, 'STVART'))
				sendDirectMessage("ART response: {}".format(art_response))

				while cis_response != 'ok':
					time.sleep(15)
					cis_response = send(config.cis_webhook_url, payload=createReport(config.cis_persons_dict, 'STVCIS'))
					sendDirectMessage("CIS response: {}".format(cis_response))

				while art_response != 'ok':
					time.sleep(15)
					art_response = send(config.art_webhook_url, payload=createReport(config.art_persons_dict, 'STVART'))
					sendDirectMessage("ART response: {}".format(art_response))

				time.sleep(60)
			
			time.sleep(30)
		except Exception as ex:
			sendDirectMessage(ex)


if __name__ == "__main__":
	monitoring()
	
