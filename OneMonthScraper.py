# -*- coding: utf-8 -*-

# I wanted to be able to refer to a OneMonth course's videos in the future.
# Unfortunately, OneMonth does not allow you to do that because their subscription model.
# So, I made this scraper to download the videos so I have them locally.
# 
# Be sure to fill out your EMAIL, PASSWORD, and which course you're subscribed to.
# Install the newest version Selenium
# Install Beautiful Soup
# Firefox must be installed in order to use it as a Web Driver.

from bs4 import BeautifulSoup
from urllib2 import urlopen
import urllib2
import urllib
import os
import re
import cgi
import mechanize
import time
import os
import time  
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import httplib

dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = (
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) "
    "Gecko/20100101 Firefox/40.1"
)

# GLOBAL VARS
PATH_TO_SCRIPT = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "https://onemonth.com"
LOGIN_URL = BASE_URL + "/signin/"
COURSE_URL = BASE_URL + "/courses/one-month-rails/"

USER_EMAIL = ""
PASSWORD = ""

WITH_ERRORS = False

browser = webdriver.Firefox()
soup = BeautifulSoup()

# Console Color Text Class
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Print with Colors!
def trace(MSG, COLOR):
	if COLOR == "SUCCESS": # GREEN
		print bcolors.OKGREEN + MSG + bcolors.ENDC
	elif COLOR == "WARNING": # YELLOW
		print bcolors.WARNING + MSG + bcolors.ENDC
	elif COLOR == "FAIL": # FAIL
		print bcolors.FAIL + MSG + bcolors.ENDC

def main():
	# FIRST LOG IN
	if login() == False:
		trace("Login credentials were not correct", "FAIL")
		quit()
	trace("Logged in Successfully", "SUCCESS")
	
	# GET COURSE URLS
	course_urls = get_course_urls()
	if len(course_urls) == 0:
		trace("Something went wrong. No Course Video URLs found. Check your course URL", "FAIL")
		quit()
	trace("Course URLs Retrieved", "SUCCESS")
	
	# START SCRAPE LOOP TO GET VIDEOS
	scrape_loop(course_urls)
	
	# LET USER KNOW IF THERE WAS ERRORS OR NOT
	if WITH_ERRORS == True:
		trace("Scraper completed with Errors", "FAIL")
	else:
		trace("Scraper completed!", "SUCCESS")
	
	# QUIT
	browser.quit()
	quit()

def login():
	trace("Logging in @ "+LOGIN_URL, "WARNING")

	try:
		browser.get(LOGIN_URL)	
		element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "new_user")))
	except httplib.BadStatusLine as e:
		print e

	form = browser.find_element_by_id('new_user')
	email_input = browser.find_element_by_name('user[email]')
	email_input.send_keys(USER_EMAIL)
	password_input = browser.find_element_by_name('user[password]')
	password_input.send_keys(PASSWORD)
	password_input.send_keys(Keys.RETURN)

	soup = BeautifulSoup(browser.page_source)

	flash_div = soup.find_all("div", {"class":"flash-message-container"})
	was_logged_in = False
	for tag in flash_div:
		alert_divs = tag.find_all("div", {"class":"alert"})
		for alert_div in alert_divs:
			if alert_div.text == "Signed in successfully.":
				was_logged_in = True

	if was_logged_in == False:
		return False
	else:
		return True

def get_course_urls():
	trace("Getting list of Course Section URLs", "WARNING")
	try:
		browser.get(COURSE_URL)
		soup = BeautifulSoup(browser.page_source)

	except Exception as e: 
		print e
		return []

	step_urls = []
	section_divs = soup.find_all("div", {"class":"section"})
	step_divs = soup.find_all("div", {"class":"step"})
	for step_div in step_divs:
		links = step_div.findAll('a')
		for a in links:
			step_urls.append(a['href'])
			
	return step_urls;	
			
def scrape_loop(course_urls):
	count = 0;
	for url in course_urls:
		tempnum = count + 1
		trace("\nParsing Step "+str(tempnum)+" of " + str(len(course_urls)), "WARNING")
		grab_video(url)
		count += 1

def grab_video(url):
	trace("Step: "+url, "WARNING")
	STEP_URL = BASE_URL + url
	try:
		browser.get(STEP_URL)
		wait = WebDriverWait(browser, 10)
		wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "step-container")))
		soup = BeautifulSoup(browser.page_source)
	except Exception as e:
		print e
		quit();
		pass
		
	video_source = soup.find('source')
	if video_source is None:
		step_file_name = PATH_TO_SCRIPT + "/" + url.rsplit('/', 1)[-1] + ".txt"
		with open(step_file_name, "wb") as text_file:
		    text_file.write("This step doesn't look like it contains a video.")
		trace(step_file_name+" step doesn't look like it contains a video.","SUCCESS")
	else:
		# Get Text to manipulate, EX: Day 1 • Lesson 1
		step_text = soup.find('div', {"class":'step-container'}).p.small.text.replace(" ", "")
		# Split Day and Lesson text into array
		day_lesson = step_text.split(u"·") # must have for u for decode of non-ascii character
		# Set file name of video to module day and name
		step_file_name = day_lesson[1] + "_"+ url.rsplit('/', 1)[-1] + ".mp4"
	
		# Create a Folder for which day the lesson is
		folder_path = PATH_TO_SCRIPT + "/" + day_lesson[0]
		if not os.path.exists(folder_path):
			os.makedirs(folder_path)
		video_source = soup.find('source')
		video_mp4_url = video_source["src"]
		
		if os.path.isfile(folder_path+'/'+step_file_name):
			trace(step_file_name+" has been downloaded already!","SUCCESS")
			return;
		try:
			f = urllib.urlopen(video_mp4_url)
			with open(folder_path+'/'+step_file_name, "wb") as MP4:
				# Save our File
				MP4.write(f.read()) 
		except Exception as e:
			trace("There was an error downloading: "+step_file_name, "FAIL");
			pass
	
		trace(step_file_name+" has been downloaded!","SUCCESS")
	



# Start Ripping
main()