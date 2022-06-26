import PySimpleGUI as sg
import json
from SPCACheckout import api
from datetime import datetime
from dateutil.relativedelta import relativedelta

sg.theme('TanBlue')

login_layout = [
	[sg.Push(), sg.Text('ClinicHQ User'), sg.InputText('', key='UserName')],
	[sg.Push(), sg.Text('ClinicHQ Password'), sg.InputText('', key='Password', password_char='*')],
	[sg.Push(), sg.Button('Login', bind_return_key=True), sg.Button('Cancel'), sg.Push()]
]
login_window = sg.Window('SPCA NN - Login', login_layout)


def bool_to_yes_no(boolean: bool):
	if boolean:
		return 'Yes'
	else:
		return 'No'


def search_window():
	search_layout = [
		[sg.Push(), sg.Text('Appointment ID'), sg.InputText('', key='appointment_id', size=(12, 1), do_not_clear=False, focus=True), sg.Push()],
		[sg.Push(), sg.Button('Search', bind_return_key=True), sg.Button('Quit'), sg.Push()]
	]

	return sg.Window('SPCA NN - Search', search_layout).finalize()


def main_window(session, appointment_id: int):
	appointment_details = session.get_appointment_details(appointment_id)
	financial_details = session.get_financial(appointment_id)
	medical_attributes = session.get_animal_medical(appointment_id)
	payment_details = session.get_payment_details(appointment_id)
	services_list = session.services_lookup(int(appointment_details['genderTypeId']), int(appointment_details['speciesId']))
	veterinarians = list(map(lambda x: x['value'], session.vet_lookup()))
	microchip_providers_list = list(map(lambda x: x['name'], session.microchip_providers()))
	vaccines_available = []
	for service in services_list:
		if service['type'] == 'Vaccine':
			vaccines_available.append(service['name'])
			vaccines_available.sort()
	vaccines_available.insert(0, '')
	species = session.species_lookup()
	if appointment_details['species'] == "Cat":
		breeds = species['breeds']['2']
	elif appointment_details['species'] == "Dog":
		breeds = species['breeds']['1']
	else:
		raise ValueError('Unknown or undefined species: {}'.format(appointment_details['species']))
	common_data = session.common_lookup()
	colors = common_data['colorOptions']
	colors.insert(0, {'id': None, 'title': '', 'isFrequent': False})
	ageMonthOptions = list(map(lambda x: x['key'], common_data['ageMonthOptions']))
	ageYearOptions = list(map(lambda x: x['key'], common_data['ageYearOptions']))

	left_titles = [
		[sg.Push(), sg.Text('Appointment Time')],
		[sg.Push(), sg.Text('Client Name')],
		[sg.Push(), sg.Text('Address')],
		[sg.Push(), sg.Text('Address 2')],
		[sg.Push(), sg.Text('City')],
		[sg.Push(), sg.Text('Cell Phone')],
		[sg.Push(), sg.Text('E-mail')],
	]

	left_fields = [
		[sg.InputText(appointment_details['startTimeText'], disabled=True, key='appointment_time', size=(9, 1)), sg.Text('Animal Number'), sg.InputText(appointment_details['number'], key='animal_number', size=(10, 1)), sg.Push()],
		[sg.InputText(appointment_details['clientName'], disabled=True, key='client_name'), sg.Push()],
		[sg.InputText(appointment_details['owner']['address'].split(',')[0], disabled=True, key='address'), sg.Push()],
		[sg.InputText(disabled=True, key='address2'), sg.Push()],
		[sg.InputText(appointment_details['owner']['address'].split(', ')[1], size=(21, 1), justification='left', disabled=True, key='city'), sg.Text('State'), sg.InputText(appointment_details['owner']['address'].split(', ')[2].strip()[:2], size=(3, 1), justification='center', disabled=True, key='state'), sg.Text('Zip'), sg.InputText(appointment_details['owner']['address'].split(', ')[2].strip()[2:], size=(6, 1), justification='center', disabled=True, key='zip'), sg.Push()],
		[sg.InputText(appointment_details['owner']['cellPhone'], size=(14, 1), justification='left', key='cell_phone'), sg.Text('Home Phone'), sg.InputText(appointment_details['owner']['homePhone'], size=(14, 1), justification='left', key='home_phone'), sg.Push()],
		[sg.InputText(appointment_details['owner']['email'], justification='left', key='email'), sg.Push()]
	]

	right_titles = [
		[sg.Push(), sg.Text('Animal Name')],
		[sg.Push(), sg.Text('Species')],
		[sg.Push(), sg.Text('Breed')],
		[sg.Push(), sg.Text('Primary Color')],
		[sg.Push(), sg.Text('Age Years')],
		[sg.Push(), sg.Text('Known health issues?')],
		[sg.Push(), sg.Text('Ever Reacted to a Vaccine?')]
	]

	right_fields = [
		[sg.InputText(appointment_details['name'], justification='left', key='animal_name', enable_events=True), sg.Push()],
		[sg.Combo(['Cat', 'Dog'], key='species', default_value=appointment_details['species'], disabled=True), sg.Text('Sex'), sg.Combo(['Male', 'Female'], key='sex', default_value=appointment_details['sex']), sg.Push()],
		[sg.Combo(list(map(lambda x: x['title'], breeds)), default_value=appointment_details['breed'], key='breed'), sg.Push()],
		[sg.Combo(list(map(lambda x: x['title'], colors)), default_value=appointment_details['primaryColor'], key='primary_color'), sg.Text('Secondary Color'), sg.Combo(list(map(lambda x: x['title'], colors)), default_value=appointment_details['secondaryColor'], key='secondary_color'), sg.Push()],
		[sg.Combo(ageYearOptions, default_value=appointment_details['ageYears'], key='age_years'), sg.Text('Age Months'), sg.Combo(ageMonthOptions, default_value=appointment_details['ageMonths'], key='age_months'), sg.Text('Spayed/Neutered?'), sg.Combo(['Yes', 'No', 'Unknown'], key='altered', size=(4, 1), default_value=bool_to_yes_no(appointment_details['isSpayedNeutered'])), sg.Push()],
		[sg.Combo(['', 'Yes', 'No'], default_value=medical_attributes['health_issues'], key='health_issues'), sg.Text('On Medication/Pregnant?'), sg.Combo(['', 'Yes', 'No'], key='meds_pregnant', default_value=medical_attributes['meds_pregnant'])],
		[sg.Combo(['', 'Yes', 'No'], key='vaccine_reaction', default_value=medical_attributes['vaccine_reactions']), sg.Text('If so, which vaccine?'), sg.InputText(size=(20, 1), key='which_vaccine_reaction', default_text=medical_attributes['vaccines_reacted_to']), sg.Push()]
	]

	vaccines_list = [
		[sg.HorizontalSeparator()],
		[sg.Push(), sg.Text('Vaccine', size=(35, 1)), sg.Push(), sg.Text('Reminder'), sg.Push(), sg.Text('Price')]
	]
	vaccine_total = float()
	for vaccine in financial_details:
		reminder_options = ['1yr']
		three_week_vaccines = ['dhpp', 'dapp', 'fvrcp', 'felv', 'leukemia', 'flu', 'influenza']
		three_year_vaccines = ['rabies', 'fvrcp']
		for i in three_week_vaccines:
			if i.lower() in vaccine['name'].lower():
				if '3wk' not in reminder_options:
					reminder_options.insert(0, '3wk')
		for i in three_year_vaccines:
			if i.lower() in vaccine['name'].lower():
				if '3yr' not in reminder_options:
					reminder_options.append('3yr')
		reminder_options.insert(0, '')
		vaccines_list.append([sg.Push(), sg.Checkbox(vaccine['name'], key='vaccine_{}'.format(vaccine['id']), size=(35, 1), default=True), sg.Push(), sg.Combo(reminder_options, key='reminder_{}'.format(vaccine['id'])), sg.Push(), sg.Text('${:.2f}'.format(float(vaccine['price'])))])
		vaccine_total += vaccine['price']
		if vaccine['name'] in vaccines_available:
			vaccines_available.pop(vaccines_available.index(vaccine['name']))
	vaccines_list.append([sg.HorizontalSeparator()])
	vaccines_list.append([sg.Push(), sg.Text('Sub-Total:  ${:.2f}'.format(vaccine_total))])
	vaccines_list.insert(0, [sg.Text('Add Vaccine:'), sg.Combo(vaccines_available, key='add_vaccine'), sg.Button('Add')])

	final_total = vaccine_total
	for payment in payment_details['payments']:
		if payment['integratedPaymentTypeText']:
			payment_source = payment['integratedPaymentTypeText']
		else:
			payment_source = 'Manually'
		vaccines_list.append([sg.Push(), sg.Text('{}: {}, {} by {}: -${:.2f}'.format(payment['type'], datetime.strptime(payment['date'].split('T')[0], "%Y-%m-%d").strftime("%m/%d/%Y"), payment_source, payment['createdBy'], float(payment['amount'])))])
		final_total -= payment['amount']
	vaccines_list.append([sg.HorizontalSeparator()])
	vaccines_list.append([sg.Push(), sg.Text('Remaining Balance: {:.2f}'.format(final_total))])
	vaccines_list.append([sg.VPush()])

	wellness_rabies = [
		[sg.Push(), sg.Text("Wellness", font=('Arial', 14, 'bold')), sg.Push()],
		[sg.Push(), sg.Text('Veterinarian'), sg.Combo(veterinarians, key='vet', default_value='Lisa Burnett', size=(18, 1))],
		[sg.Push(), sg.Text('Behavior Alert'), sg.Checkbox('', key='animal_caution', default=appointment_details['animalCaution'], size=(20, 1))],
		[sg.Push(), sg.Text('Respiratory'), sg.Combo(['Normal', 'Abnormal'], key='respiratory', default_value='Normal', size=(18, 1))],
		[sg.Push(), sg.Text('Weight'), sg.InputText('', size=(20, 1), key='weight')],
		[sg.Push(), sg.Text('Temperature'), sg.InputText('', size=(20, 1), key='temperature')],
		[sg.HorizontalSeparator()],
		[sg.Push(), sg.Text("Rabies", font=('Arial', 14, 'bold')), sg.Push()],
		[sg.Push(), sg.Text('Vaccine {}')],
		[sg.Push(), sg.Text('Manufacturer'), sg.InputText("", justification='left', size=(10, 1), key='rabies_mfg')],
		[sg.Push(), sg.Text('Date'), sg.InputText(datetime.now().date(), justification='left', size=(10, 1), key='rabies_date')],
		[sg.Push(), sg.Text('Expires'), sg.InputText(datetime.now().date() + relativedelta(years=1), justification='left', size=(10, 1), key='rabies_exp')],
		[sg.Push(), sg.Text('Tag Number'), sg.InputText("", justification='left', size=(10, 1), key='rabies_tag_number')],
		[sg.Push(), sg.Text('Lot Number'), sg.InputText("", justification='left', size=(10, 1), key='rabies_lot_number')],
		[sg.Push(), sg.Text('Lot Expiration Date'), sg.InputText("", justification='left', size=(10, 1), key='rabies_lot_exp')],
		[sg.VPush()]
	]

	microchip = [
		[sg.Push(), sg.Text("Microchip", font=('Arial', 14, 'bold')), sg.Push()],
		[sg.Push(), sg.Text('Provider'), sg.Combo(microchip_providers_list, key='microchip_provider', default_value='24PetWatch')],
		[sg.Push(), sg.Text('Chip ID'), sg.InputText("", justification='left', size=(20, 1), key='microchip_id')],
		[sg.HorizontalSeparator()]
	]

	layout = [[sg.Column(left_titles), sg.Column(left_fields), sg.VerticalSeparator(), sg.Column(right_titles), sg.Column(right_fields)],
			  [sg.HorizontalSeparator()],
			  [sg.Column(vaccines_list, expand_y=True), sg.VerticalSeparator(), sg.Column(wellness_rabies, expand_y=True), sg.VerticalSeparator(), sg.Column(microchip, expand_y=True, expand_x=True)],
	]

	return sg.Window('SPCA NN - Checkout', layout, resizable=True).finalize()


login_successful = False
while True:
	login_event, login_values = login_window.read()
	if login_event == 'Login':
		try:
			session = api.ClinicHQ(login_values['UserName'].strip(), login_values['Password'].strip())
			login_successful = True
		except json.JSONDecodeError:
			pass
	elif login_event in (sg.WIN_CLOSED, 'Cancel'):
		login_window.close()
		break
	if login_successful:
		login_window.close()
		while True:
			sw = search_window()
			search_event, search_values = sw.read()
			if search_event in (sg.WIN_CLOSED, 'Quit'):
				sw.close()
				exit(0)
			elif search_event == 'Search':
				sw.close()
				lookup_successful = False
				try:
					appointment_details = session.get_appointment_details(search_values['appointment_id'])
					lookup_successful = True
				except:
					pass
				if lookup_successful:
					mw = main_window(session, search_values['appointment_id'])
					# mw['animal_name'].bind("<Tab>", "_Tab")
					while True:
						main_events, main_values = mw.read()
						if main_events in (sg.WIN_CLOSED, 'Cancel'):
							break
						elif main_events == 'Save':
							original_appointment_details = session.get_appointment_details(search_values['appointment_id'])
							new_details = original_appointment_details
							if original_appointment_details['name'] != main_values['animal_name']:
								new_details['name'] = main_values['animal_name']
							if original_appointment_details['sex'] != main_values['sex']:
								new_details['sex'] = main_values['sex']
								if main_values['sex'].lower() == 'female':
									new_details['genderTypeId'] = 2
								elif main_values['sex'].lower() == 'male':
									new_details['genderTypeId'] = 1
							print(original_appointment_details)
							print(main_values)
					mw.close()


