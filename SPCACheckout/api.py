import json
import requests
import os
import re
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
		token = re.findall(second_pass, re.findall(first_pass, self.session.get(self.hostname + '/account/login',
																				headers=self.headers).text)[0])[
			0].replace('value="', '')
		payload['__RequestVerificationToken'] = token
		self.session.post(self.hostname + '/account/login', headers=self.headers, data=payload)
		check_login = self.session.get(self.hostname + '/api/lookup/me')
		check_login.json()

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

	def get_vaccines(self, gender: int, species: int):
		"""
		Get's the list of vaccines
		Args:
			gender: 1 for Male, 2 for Female
			species: 1 for Dog, 2 for Cat

		Returns:
			Vaccine list for the animal type.

		"""
		query_results = self.request(
			'/api/lookup/services?appointmentType=3&clientType=1&genderTypeId={}&speciesId={}'.format(gender, species)).json()
		vaccine_list = []
		for i in query_results:
			if i['type'] == 'Vaccine':
				vaccine_list.append(i)
		return vaccine_list

	def get_appointment_details(self, appointment: int):
		appointment_details = self.request('/api/checkout/appointment/{}'.format(appointment)).json()
		return appointment_details

	def get_financial(self, appointment: int):
		"""
		Get the list of vaccines attached to an appointment.
		Args:
			appointment: Appointment ID

		Returns:
			List of vaccines currently attached to the appointment.
		"""
		return self.request('/spa/checkout/loadfinancial/{}'.format(appointment)).json()

	def get_client_details(self, client_id: int):
		client_details = self.request('/api/clients/{}/profile'.format(client_id)).json()
		return client_details

	def add_service(self, appointment: int, service: int):
		"""
		Add a service to the appointment record.
		Args:
			appointment: Appointment ID to add the service to.
			service: The service to add.

		Returns:
			Information on the service for the specific record, in particular the ID of the service that was added.
		"""
		return self.request('/spa/checkout/addservice/{}'.format(appointment), service, 'post').json()

	def delete_service(self, unique_service_id: int):
		"""
		Removes the designated service from the appointment record.
		Args:
			unique_service_id: The service record to be deleted.

		Returns:
			Success or fail.
		"""
		return self.request('/spa/checkout/DeleteService/{}'.format(unique_service_id), {}, 'post').json()

	def update_appointment(self, appointment: int, payload: dict):
		results = self.request('/api/checkout/appointment/{}'.format(appointment), payload, 'post')
		if results.status_code == 200:
			return True
		else:
			raise Exception('Invalid status code when attempting to update appointment data for {}'.format(appointment))

	def common_lookup(self):
		"""
		Gathers the following options from the server: ageMonthOptions, ageYearOptions, animalTypeOptions, colorOptions, creditCardOptions.
		Returns:
			All the above options.
		"""
		return self.request('/api/lookup/common').json()

	def species_lookup(self):
		"""
		Gathers the list of breeds and species and returns them.
		Returns:
			Dictionary of breeds and species.
		"""
		return self.request('/api/lookup/species').json()

	def vet_lookup(self):
		"""
		Gathers the list of vets and returns them.
		Returns:
			List of veterinarians.
		"""
		return self.request('/api/lookup/vets').json()

	def microchip_providers_lookup(self):
		"""
		Gathers the list of microchip providers and returns them.
		Returns:
			List of microchip providers.
		"""
		return self.request('/api/common/microchip/providers').json()

	def services_lookup(self, genderTypeId: int, speciesId: int, clientType=1, appointmentType=3):
		"""
		Get's a list of possible services.
		Args:
			genderType: Integer, 1=Male, 2=Female
			speciesId: Integer, 1=Dog, 2=Cat
			clientType: Integer, unknown
			appointmentType: Integer, 1=Spay/Neuter, 2=Unknown, 3=Vaccine Clinic

		Returns:
			List of services that apply.
		"""
		return self.request('/api/lookup/services?appointmentType={}&clientType={}&genderTypeId={}&speciesId={}'.format(appointmentType, clientType, genderTypeId, speciesId)).json()

	def get_animal_medical(self, appointment_id: int):
		custom_fields = self.request('/api/common/custom-fields/{}'.format(appointment_id)).json()
		medical_attributes = {
			'spayed_neutered': "Yes",
			'health_issues': "Yes",
			'meds_pregnant': "Yes",
			'vaccine_reactions': "Yes",
			'vaccines_reacted_to': ""
		}
		for field in custom_fields:
			if field['id'] == 9173:
				if str(field['value']) == str(8685):  # If not pregnant/meds
					medical_attributes['meds_pregnant'] = "No"
			if field['id'] == 9174:
				if str(field['value']) == str(8687):  # If no health issues
					medical_attributes['health_issues'] = "No"
			if field['id'] == 9175:
				if str(field['value']) == str(8689):  # If no vaccine reactions
					medical_attributes['vaccine_reactions'] = "No"
			if field['id'] == 8977:  # If it exists, do not highlight
				medical_attributes['spayed_neutered'] = "No"
			if field['id'] == 9176:  # If it exists, do not highlight
				medical_attributes['vaccines_reacted_to'] = field['value']
		return medical_attributes

	def get_payment_details(self, appointment_id: int):
		"""
		Retrieves details for all services & payments.
		Args:
			appointment_id: Appointment ID to lookup
		Returns:
			Results of the lookup.
		"""
		return self.request('/api/checkout/financial/{}'.format(appointment_id)).json()

	def microchip_providers(self):
		"""
		Retrieves the list of microchip providers.
		Returns:
			Microchip providers dictionary.
		"""
		return self.request('/api/common/microchip/providers').json()

	def microchip_details(self, animal_id: int):
		"""
		Returns the microchip information for the specified animal.
		Args:
			animal_id: ID of the animal to retrieve.
		Returns:
			Microchip attributes dictionary.
		"""
		return self.request("/api/common/microchip/{}".format(animal_id)).json()


