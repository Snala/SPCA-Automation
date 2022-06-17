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
		financial_details = self.request('/spa/checkout/loadfinancial/{}'.format(appointment)).json()
		return financial_details

	def get_client_details(self, client_id: int):
		client_details = self.request('/api/clients/{}/profile'.format(client_id)).json()
		return client_details

	def add_service(self, appointment: int, service: int):
		results = self.request('/spa/checkout/addservice/{}'.format(appointment), service, 'post').json()
		return results

	def delete_service(self, unique_service_id: int):
		results = self.request('/spa/checkout/DeleteService/{}'.format(unique_service_id), {}, 'post').json()
		return results

	def update_appointment(self, appointment: int, payload: dict):
		results = self.request('/api/checkout/appointment/{}'.format(appointment), payload, 'post')
		if results.status_code == 200:
			return True
		else:
			raise Exception('Invalid status code when attempting to update appointment data for {}'.format(appointment))


