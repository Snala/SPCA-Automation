import requests
import os
import pathlib
import re
import datetime
from json import load
from dateutil.relativedelta import relativedelta


class ClinicHQ:
	def __init__(self):
		with open(os.path.join(pathlib.Path().absolute(), 'authentication.json'), 'r') as json_file:
			server_settings = load(json_file)
			self.hostname = server_settings['host']
			user_name = server_settings['user']
			password = server_settings['password']
			json_file.close()
		self.headers = {'User-Agent': 'Mozilla/5.0'}
		payload = {'UserName': user_name, 'Password': password}
		self.session = requests.Session()
		first_pass = r'<input name="__RequestVerificationToken" type="hidden" value="[^"]*" />'
		second_pass = r'value="[^"]*'
		token = re.findall(second_pass, re.findall(first_pass, self.session.get(self.hostname + '/account/login', headers=self.headers).text)[0])[0].replace('value="', '')
		payload['__RequestVerificationToken'] = token
		self.session.post(self.hostname + '/account/login', headers=self.headers, data=payload)
		# print(self.session.get(self.hostname + '/api/paperwork/appointments/2022-06-10?sortOrder=5').text)

	def request(self, url, request_type='get', payload=''):
		if request_type == 'get':
			return self.session.get(self.hostname + url, headers=self.headers, data=payload)
		elif request_type == 'post':
			return self.session.post(self.hostname + url, headers=self.headers, data=payload)

	def get_appointments(self, date: str, sort_order=5):
		datetime.datetime.strptime(date, "%Y-%m-%d")  # Verify the time string is valid.
		return self.request('/api/paperwork/appointments/{}?sortOrder={}'.format(date, sort_order)).json()

	def get_animal_summary(self, animal: int):
		return self.request('/api/animals/summary/{}'.format(animal)).json()


class Details:
	def __init__(self):
		self.clinic_connection = ClinicHQ()

	def appointment_list(self, date: str):
		datetime.datetime.strptime(date, "%Y-%m-%d")  # Verify the time string is valid.
		appointments = self.clinic_connection.get_appointments(date)
		appointment_list = []
		for appointment in appointments:
			appointment_list.append({
				'id': int(appointment['id']),
				'clientName': appointment['clientName'],
				'animalName': appointment['animalName'],
				'animalNumber': appointment['animalNumber'],
				'species': appointment['species'],
				'animalId': int(appointment['animalId']),
				'startTime': appointment['startTime']
			})
		return appointment_list

	def vaccine_reminders(self, animal_id: int):
		vaccine_list = ['Rabies', 'DHPP', 'Bordetella', 'Influenza', 'FVRCP', 'FelineLeukemia']
		reminders = {}
		animal_summary = self.clinic_connection.get_animal_summary(animal_id)
		for appointment in animal_summary['appointments']:
			for custom_field in appointment['customValues']:
				for vaccine in vaccine_list:
					if vaccine in str(custom_field['customFieldName']):
						date = str(custom_field['value']).replace('.', '/').replace('-', '/')
						date = date.split('/')
						if len(date[0]) < 2:
							date[0] = '0'+str(date[0])
						if len(date[1]) < 2:
							date[1] = '0'+str(date[1])
						if len(date[2]) < 4:
							date[2] = '20'+str(date[2])
						date = str("{}/{}/{}").format(date[0], date[1], date[2])
						if vaccine in reminders:
							if datetime.datetime.strptime(date, "%m/%d/%Y") > datetime.datetime.strptime(reminders[vaccine], "%m/%d/%Y"):
								reminders[vaccine] = date
						else:
							reminders[vaccine] = date
		return reminders


test = Details()
print("Starting!")
query_date = '2022-06-11'
appointment_list = test.appointment_list(query_date)
with open(os.path.join(pathlib.Path().absolute(), 'vaccine_reminder_list.txt'), 'w') as vaccine_reminder_document:
	for appointment in appointment_list:
		if appointment['animalId'] > 0:
			vaccine_reminders_list = test.vaccine_reminders(appointment['animalId'])
			if vaccine_reminders_list:
				start_time = datetime.datetime.strptime(appointment['startTime'], "%H:%M:%S")
				start_time = start_time.strftime("%#I:%M")
				vaccine_reminder_document.write("{},{},{},({}),{}\n".format(start_time, appointment['animalName'], appointment['animalNumber'], appointment['clientName'], appointment['species']))
				for vaccine in vaccine_reminders_list:
					try:
						if datetime.datetime.strptime(vaccine_reminders_list[vaccine], "%m/%d/%Y") < datetime.datetime.strptime(query_date, "%Y-%m-%d"):
							alert = "!-"
						elif datetime.datetime.strptime(vaccine_reminders_list[vaccine], "%m/%d/%Y") < datetime.datetime.strptime(query_date, "%Y-%m-%d") + relativedelta(months=+6):
							alert = "+-"
						else:
							alert = "  "
					except ValueError:
						alert = "?-"
					vaccine_reminder_document.write("\t{}: {}\n".format(alert+vaccine, vaccine_reminders_list[vaccine]))
				vaccine_reminder_document.write("\n")
	vaccine_reminder_document.close()
print("Done!")