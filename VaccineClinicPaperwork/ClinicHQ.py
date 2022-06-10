import pathlib
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class Connection:
	def __init__(self):
		with open(os.path.join(pathlib.Path().absolute(), 'authentication.json'), 'r') as json_file:
			server_settings = json.load(json_file)
			self.hostname = server_settings['host']
			self.user_name = server_settings['user']
			self.password = server_settings['password']
			json_file.close()
		# Start Web Driver
		self.driver = webdriver.Chrome('C:\ChromeDriver\chromedriver.exe')
		# Open Login Page and Login
		self.driver.get(self.hostname + '/account/login')
		time.sleep(2)
		user_name = self.driver.find_element(by=By.NAME, value='UserName')
		password = self.driver.find_element(by=By.NAME, value='Password')
		user_name.send_keys(self.user_name)
		password.send_keys(self.password)
		password.submit()




start_connection = Connection()
exit(1)

driver = webdriver.Chrome('C:\ChromeDriver\chromedriver.exe')  # Optional argument, if not specified will search path.
driver.get('https://www.google.com/')
time.sleep(5)
search_box = driver.find_element_by_name('q')
search_box.send_keys('Snala')
search_box.submit()
time.sleep(5)
# driver.quit()