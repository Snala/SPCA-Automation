import PySimpleGUI as sg
import json
import api

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
	# print(appointment_details)
	# print('\n\n')
	# print(financial_details)

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
		[sg.Push(), sg.Text('Spayed/Neutered?')],
		[sg.Push(), sg.Text('Ever Reacted to a Vaccine?')],
		[sg.Push(), sg.Text('Behavior Alert')]
	]

	right_fields = [
		[sg.InputText(appointment_details['name'], justification='left', key='animal_name', enable_events=True), sg.Push()],
		[sg.Combo(['Cat', 'Dog'], key='species', default_value=appointment_details['species'], disabled=True), sg.Text('Sex'), sg.Combo(['Male', 'Female'], key='sex', default_value=appointment_details['sex']), sg.Push()],
		[sg.InputText(appointment_details['breed'], size=(30, 1), key='breed'), sg.Push()],
		[sg.InputText(appointment_details['primaryColor'], size=(15, 1), key='primary_color'), sg.Text('Secondary Color'), sg.InputText(appointment_details['secondaryColor'], size=(15, 1), key='secondary_color'), sg.Push()],
		[sg.InputText(appointment_details['ageYears'], size=(4, 1), justification='center', key='age_years'), sg.Text('Age Months'), sg.InputText(appointment_details['ageMonths'], size=(4, 1), justification='center', key='age_months'), sg.Push()],
		[sg.Combo(['Yes', 'No', 'Unknown'], key='altered', size=(4, 1), default_value=bool_to_yes_no(appointment_details['isSpayedNeutered'])), sg.Text('Known health issues?'), sg.Combo(['Yes', 'No'], key='health_issues'), sg.Text('On Medication/Pregnant'), sg.Combo(['Yes', 'No'], key='meds_pregnant')],
		[sg.Combo(['Yes', 'No', 'Unknown'], key='vaccine_reaction'), sg.Text('If so, which vaccine?'), sg.InputText(size=(20, 1), key='which_vaccine_reaction'), sg.Push()],
		[sg.Checkbox('', key='animal_caution', default=appointment_details['animalCaution']), sg.Push()]
	]

	headers = ['', 'Vaccine', 'ID', 'Cost']

	table_values = []

	layout = [[sg.Column(left_titles), sg.Column(left_fields), sg.Column(right_titles), sg.Column(right_fields)],
			  [sg.Table(values=table_values, headings=headers, auto_size_columns=True, justification='left', alternating_row_color='lightblue', num_rows=min(len(table_values), 20))]]
	return sg.Window('SPCA NN - Checkout', layout).finalize()


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
					mw['animal_name'].bind("<Tab>", "_Tab")
					while True:
						main_events, main_values = mw.read()
						if main_events in (sg.WIN_CLOSED, 'Cancel'):
							break
						elif main_events == 'animal_name' + '_Tab':
							print(main_events)
							print(main_values)
					mw.close()


