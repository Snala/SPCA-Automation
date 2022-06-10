import requests
import os
import pathlib
import re
import datetime
import fitz
import glob
import time
from json import load
from pathlib import Path
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
		with open(os.path.join(pathlib.Path().absolute(), 'pdfs/' + str(appointment_id) + '.pdf'), 'wb') as file:
			file.write(response.content)
			file.close()


class Details:
	def __init__(self):
		self.clinic_connection = ClinicHQ()
		self.appointment_list = []

	def get_appointment_list(self, date: str):
		datetime.datetime.strptime(date, "%Y-%m-%d")  # Verify the time string is valid.
		appointments = self.clinic_connection.get_appointments(date)
		for appointment in appointments:
			self.appointment_list.append({
				'id': int(appointment['id']),
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
		with open(os.path.join(Path.home(), "Downloads", "Reminder List " + datetime.date.today().strftime("%d-%m-%Y") + ".txt"), 'w') as vaccine_reminder_document:
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
			doc = fitz.open(os.path.join(pathlib.Path().absolute(), 'pdfs/' + str(appointment['id']) + '.pdf'))
			search_terms = []
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
			else:
				raise ValueError('Unexpected species: {}'.format(appointment['species']))
			if str(appointment['species']).lower() == 'cat':
				page = doc.load_page(0)
				rect = page.rect  # the page rectangle
				mp = (rect.tl + rect.br) / 2  # its middle point, becomes top-left of clip
				clip = fitz.Rect(mp, rect.br)  # the area we want
				# page.draw_rect(clip, color=None, fill=None, overlay=False)
				for term in search_terms:
					i_rects = page.search_for(term, clip=clip, quad=False)
					for i in i_rects:
						if i in clip:
							page.draw_rect(i, color=(0, 0, 0), fill=None, overlay=False)  # draw i
			elif str(appointment['species']).lower() == 'dog':
				page = doc.load_page(0)
				rect = page.rect
				clip = fitz.Rect(rect.x0, rect.y1/2, rect.x1/3, rect.y1)
				# page.draw_rect(clip, color=(0, 0, 0), fill=(0, 0, 0), overlay=True)
				for term in search_terms:
					i_rects = page.search_for(term, clip=clip, quad=False)
					for i in i_rects:
						if i in clip:
							page.draw_rect(i, color=(0, 0, 0), fill=None, overlay=False)  # draw i
			else:
				raise ValueError('Unexpected species: {}'.format(appointment['species']))
			count += 1
			string_count = str(count)
			while len(string_count) < 4:
				string_count = str(0) + string_count
			doc.save(os.path.join(pathlib.Path().absolute(), 'completed/' + string_count + '.pdf'), garbage=1, deflate=True, clean=True)

	@staticmethod
	def merge_pdfs():
		destination_path = os.path.join(Path.home(), "Downloads", "Vaccination Releases " + datetime.date.today().strftime("%d-%m-%Y") + ".pdf")
		directory_list = glob.glob(os.path.join(pathlib.Path().absolute(), 'completed/', '*.pdf'))
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
		directories = [os.path.join(pathlib.Path().absolute(), 'completed/'), os.path.join(pathlib.Path().absolute(), 'pdfs/')]
		for directory in directories:
			filelist = glob.glob(os.path.join(directory, "*.pdf"))
			for f in filelist:
				os.remove(f)


if __name__ == "__main__":
	program_start = time.time()
	print("Starting!")
	test = Details()
	query_date = '2022-06-11'
	print('Gathering appointments')
	appointment_list = test.get_appointment_list(query_date)
	print('Generating Reminder Summary List')
	test.generate_reminder_summary()
	print("Done, pre-cleaning temporary directories")
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
