import os
import time
from webhookHandler import send
import datetime
import jiraHandler


def createReport():

	weekday = datetime.datetime.today().weekday()
	if weekday: # not monday
		yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
		jql = "project = STVCIS and worklogDate = \'{}\'".format(yesterday)
	else:
		friday = (datetime.datetime.today() - datetime.timedelta(days=3)).strftime("%Y/%m/%d")
		monday = datetime.datetime.today().strftime("%Y/%m/%d")
		jql = "project = STVCIS and worklogDate >= \'{}\' and worklogDate < \'{}\'".format(friday, monday)
	
	dayWorkLog = jiraHandler.getDayWorkLog(jql)

	report_list = []

	for person in dayWorkLog:
		report_list.append(createPersonJson(person, dayWorkLog[person]))

	report = {}
	report["attachments"] = report_list

	return report


def createPersonJson(person, data):
	'''
	{
		"title": "Andrei Alekseevich log time",
		"color": "good",
		"pretext": "Date: 10/06/2019",
		"text": "Total time: 12h",
		"fields": [
			{
				"title": "STVCIS-145",
				"value": "Time: 4h",
				"short": false
			},
			{
				"title": "STVCIS-145",
				"value": "Time: 4h",
				"short": false
			},
			{
				"title": "STVCIS-145",
				"value": "Time: 4h",
				"short": false
			}
		],
		"mrkdwn_in": [
			"text",
			"pretext"
		]
	}
	'''
	person_dict = {'aalekseevich': 'Andrey Alekseevich', 'askravchenko': 'Andrey Kravchenko', 'dgalkin': 'Dmitrii Galkin'}
	report = {}
	report["title"] = person_dict[person]
	tickets = []
	if data:
		report["color"] = "good"
		for d in data:
			tickets.append({"title": "[{}] {}".format(d[0], d[1]) , "value": "Logged time: " + str(d[2]), "short": False})
	else:
		report["color"] = "danger"
		tickets.append({"title": "No logged time", "short": False})
	report["fields"] = tickets
	report["footer"] = "Jira API"
	report["footer_icon"] = "https://platform.slack-edge.com/img/default_application_icon.png"

	return report


def monitoring():

	try:
		weekday = datetime.datetime.today().weekday()
		now = datetime.datetime.now()
		if weekday in range(0, 4) and now.hour == 10 and now.minute == 0:
			send(payload=createReport())
			time.sleep(60)
		
		time.sleep(10)
	except Exception as ex:
		pass

if __name__ == "__main__":
	monitoring()
	
