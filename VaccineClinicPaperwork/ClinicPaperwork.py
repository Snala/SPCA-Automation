import json
import requests
import os
import pathlib
import base64
import tempfile
import re
import datetime
import fitz
import glob
import time
import getpass
import sys
from pathlib import Path
from dateutil.relativedelta import relativedelta


class ClinicHQ:
	def __init__(self, user_name, password):
		self.hostname = 'https://clinichq.com'
		self.headers = {'User-Agent': 'Mozilla/5.0'}
		payload = {'UserName': user_name, 'Password': password}
		self.session = requests.Session()
		first_pass = r'<input name="__RequestVerificationToken" type="hidden" value="[^"]*" />'
		second_pass = r'value="[^"]*'
		token = re.findall(second_pass, re.findall(first_pass, self.session.get(self.hostname + '/account/login', headers=self.headers).text)[0])[0].replace('value="', '')
		payload['__RequestVerificationToken'] = token
		self.session.post(self.hostname + '/account/login', headers=self.headers, data=payload)
		check_login = self.session.get(self.hostname + '/api/paperwork/appointments/2022-06-10?sortOrder=5')
		try:
			check_login.json()
		except json.JSONDecodeError:
			print('Invalid username/password, exiting!')
			time.sleep(10)
			exit(1)
		# print(self.session.get(self.hostname + '/api/paperwork/appointments/2022-06-10?sortOrder=5').text)

	def request(self, url: str, payload=None, request_type='get'):
		if not payload:
			payload = {}
		if request_type == 'get':
			result = self.session.get(self.hostname + url, headers=self.headers, data=payload)
			if result.status_code != 200:
				raise Exception('Bad request, status code: {}'.format(result.status_code))
			return result
		elif request_type == 'post':
			result = self.session.post(self.hostname + url, headers=self.headers, json=payload)
			if result.status_code != 200:
				raise Exception('Bad request, status code: {}'.format(result.status_code))
			return result

	def get_appointments(self, date: str, sort_order=5):
		datetime.datetime.strptime(date, "%Y-%m-%d")  # Verify the time string is valid.
		return self.request('/api/paperwork/appointments/{}?sortOrder={}'.format(date, sort_order)).json()

	def get_animal_summary(self, animal: int):
		return self.request('/api/animals/summary/{}'.format(animal)).json()

	def get_chosen_services(self, appointment_id: int):
		selected_services = self.request('/spa/checkout/loadfinancial/{}'.format(appointment_id)).json()
		result = []
		for service in selected_services:
			result.append(service['name'])
		return result

	def download_pdf(self, appointment_id: int):
		payload = {'ids': [appointment_id], 'consentType': 2, 'templates': [], 'paperwork': []}
		response = self.request('/paperwork/printAll/', payload, 'post')
		if len(response.content) == 0:
			payload['consentType'] = 3
		response = self.request('/paperwork/printAll/', payload, 'post')
		with open(os.path.join(tempfile.gettempdir(), 'pdfs/' + str(appointment_id) + '.pdf'), 'wb') as file:
			file.write(response.content)
			file.close()

	def get_animal_cautions(self, date: str):
		checkout_queue = self.request('/api/checkout/queue/?date={}'.format(date)).json()['items']
		animal_cautions = []
		for animal in checkout_queue:
			if animal['animalCaution']:
				animal_cautions.append(animal['id'])
		return animal_cautions


class Details:
	def __init__(self, user: str, password: str):
		self.clinic_connection = ClinicHQ(user.strip(), password.strip())
		self.appointment_list = []
		self.date = ""

	def get_appointment_list(self, date: str):
		datetime.datetime.strptime(date, "%Y-%m-%d")  # Verify the time string is valid.
		self.date = date
		appointments = self.clinic_connection.get_appointments(self.date)
		animal_cautions = self.clinic_connection.get_animal_cautions(self.date)
		for appointment in appointments:
			if int(appointment['id']) in animal_cautions:
				set_caution = True
			else:
				set_caution = False
			self.appointment_list.append({
				'id': int(appointment['id']),
				'animalCaution': set_caution,
				'clientName': appointment['clientName'],
				'animalName': appointment['animalName'],
				'animalNumber': appointment['animalNumber'],
				'species': appointment['species'],
				'animalId': int(appointment['animalId']),
				'startTime': appointment['startTime'],
				'services': self.clinic_connection.get_chosen_services(appointment['id'])
			})
		return self.appointment_list

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

	def generate_reminder_summary(self):
		with open(os.path.join(Path.home(), "Downloads", "Reminder List " + self.date + ".txt"), 'w') as vaccine_reminder_document:
			for appointment in self.appointment_list:
				if appointment['animalId'] > 0:
					vaccine_reminders_list = test.vaccine_reminders(appointment['animalId'])
					if vaccine_reminders_list:
						start_time = datetime.datetime.strptime(appointment['startTime'], "%H:%M:%S")
						start_time = start_time.strftime("%#I:%M")
						vaccine_reminder_document.write(
							"{},{},{},({}),{}\n".format(start_time, appointment['animalName'], appointment['animalNumber'], appointment['clientName'], appointment['species']))
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
							vaccine_reminder_document.write(
								"\t{}: {}\n".format(alert + vaccine, vaccine_reminders_list[vaccine]))
						vaccine_reminder_document.write("\n")
			vaccine_reminder_document.close()

	def download_all_pdfs(self):
		count = 0
		for appointment in self.appointment_list:
			count += 1
			self.clinic_connection.download_pdf(appointment['id'])
		return count

	def parse_pdf(self):
		count = 0
		for appointment in self.appointment_list:
			# noinspection PyUnresolvedReferences
			doc = fitz.open(os.path.join(tempfile.gettempdir(), 'pdfs/' + str(appointment['id']) + '.pdf'))
			search_terms = []
			page = doc.load_page(0)
			rect = page.rect  # the page rectangle
			if str(appointment['species']).lower() == 'dog':
				for item in appointment['services']:
					if 'Rabies' in item:
						search_terms.append('Rabies: $15')
					elif 'DAPP' in item:
						search_terms.append('Distemper/Parvo: $15')
					elif 'Bordetella' in item:
						search_terms.append('Bordetella: $15')
					elif 'Influenza' in item:
						search_terms.append('Flu: $30')
					elif 'Microchip' in item:
						search_terms.append('Microchip: $15')
				clip = fitz.Rect(rect.x0, rect.y1/2, rect.x1/3, rect.y1)
				# page.draw_rect(clip, color=(0, 0, 0), fill=(0, 0, 0), overlay=True)
			elif str(appointment['species']).lower() == 'cat':
				for item in appointment['services']:
					if 'Rabies' in item:
						search_terms.append('Rabies: $15')
					elif 'FVRCP' in item:
						search_terms.append('FVRCP: $15')
					elif 'Leukemia' in item:
						search_terms.append('Feline Leukemia: $15')
					elif 'Microchip' in item:
						search_terms.append('Microchip: $15')
				mp = (rect.tl + rect.br) / 2  # its middle point, becomes top-left of clip
				clip = fitz.Rect(mp, rect.br)  # the area we want
				# page.draw_rect(clip, color=None, fill=None, overlay=False)
			else:
				raise ValueError('Unexpected species: {}'.format(appointment['species']))
			for term in search_terms:
				i_rects = page.search_for(term, clip=clip, quad=False)
				for i in i_rects:
					if i in clip:
						page.draw_rect(i, color=(0, 0, 0), fill=None, overlay=False)  # draw i
			if appointment['animalCaution']:
				star_location = fitz.Rect(560, 20, 600, 60)
				star_image = b'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'
				page.insert_image(star_location, stream=base64.b64decode(star_image))
			count += 1
			string_count = str(count)
			while len(string_count) < 4:
				string_count = str(0) + string_count
			doc.save(os.path.join(tempfile.gettempdir(), 'completed/' + string_count + '.pdf'), garbage=1, deflate=True, clean=True)

	def merge_pdfs(self):
		destination_path = os.path.join(Path.home(), "Downloads", "Vaccination Releases " + self.date + ".pdf")
		directory_list = glob.glob(os.path.join(tempfile.gettempdir(), 'completed/', '*.pdf'))
		directory_list.sort(reverse=False)
		# noinspection PyUnresolvedReferences
		result = fitz.open()
		for pdf in directory_list:
			# noinspection PyUnresolvedReferences
			with fitz.open(pdf) as merged_file:
				result.insert_pdf(merged_file)
		result.save(destination_path, garbage=1, deflate=True, clean=True)

	@staticmethod
	def cleanup():
		directories = [os.path.join(tempfile.gettempdir(), 'completed/'), os.path.join(tempfile.gettempdir(), 'pdfs/')]
		for directory in directories:
			filelist = glob.glob(os.path.join(directory, "*.pdf"))
			for f in filelist:
				os.remove(f)


if __name__ == "__main__":
	username = str(input("ClinicHQ User Name: ")).strip()
	if not sys.stdin.isatty():
		p = str(input("ClinicHQ Password *WILL SHOW AS TYPED*: ")).strip()
	else:
		p = getpass.getpass(prompt="ClinicHQ Password: ")
	print("Opening connection!")
	test = Details(username, p)
	print("Login Successful.")
	query_date = ""
	while query_date == "":
		try:
			query_date = str(input("Enter a date (mm/dd/yyyy): ")).strip()
			query_date = datetime.datetime.strptime(query_date, "%m/%d/%Y")
			query_date = query_date.strftime("%Y-%m-%d")
		except ValueError:
			query_date = ""
			print('Invalid date, try again!')
	program_start = time.time()
	print('Gathering appointments')
	appointment_list = test.get_appointment_list(query_date)
	print('Generating Reminder Summary List')
	test.generate_reminder_summary()
	print("Done, pre-cleaning & setting up temporary directories")
	os.makedirs(os.path.join(tempfile.gettempdir(), 'completed/'), exist_ok=True)
	os.makedirs(os.path.join(tempfile.gettempdir(), 'pdfs/'), exist_ok=True)
	test.cleanup()
	print("Done, retrieving the PDF's")
	test.download_all_pdfs()
	print("All pdf's downloaded, parsing and marking up..")
	test.parse_pdf()
	print("All pdf's marked up, merging into one and placing in Downloads folder.")
	test.merge_pdfs()
	print("Done, cleaning up.")
	test.cleanup()
	print("Cleanup done, exiting.")
	print("--- Completed in %s seconds ---" % (time.time() - program_start))
	input("Press return to exit.")
