import json
import requests
import configparser
import operator
from keys import tunefind
from requests.auth import HTTPBasicAuth
from pprint import pprint
import datetime as dt
from datetime import time
import praw
import sqlite3


BASE_URL = 'https://www.tunefind.com/api/v1/show/'

# Choose configfile based on day and time
config = configparser.ConfigParser()
config.read('showlist.ini')
now = dt.datetime.now()
today = now.strftime("%A")
timenow = now.time()



if timenow >= time(5,00) and timenow <= time(23,00):
	print('Checking schedule...')
	print(' '.join(["Getting show info for", today]))
else:
	print("Time is out of range")

try:
	# Sunday
	if today == 'Sunday' and timenow >= time(5,00) and timenow <= time(23,00): 
		show = config['Sunday']['show']
		subreddit = config['Sunday']['subreddit']
		print(' '.join(['Show found:',show]))

	# Monday
	elif today == 'Monday' and timenow >= time(22,00) and timenow <= time(23,00): 
		show = config['Monday']['show']

	# Tuesday
	elif today == 'Tuesday' and timenow >= time(22,00) and timenow <= time(23,00): 
		show = config['Tuesday']['show']

	# Wednesday
	elif today == 'Wednesday' and timenow >= time(1,00) and timenow <= time(23,59): 
		show = config['Wednesday']['show']
		subreddit = config['Wednesday']['subreddit']

	# Thursday
	elif today == 'Thursday' and timenow >= time(0,00) and timenow <= time(23,00): 
		show = config['Thursday']['show']
		subreddit = config['Thursday']['subreddit']

	# Friday
	elif today == 'Friday' and timenow >= time(5,00) and timenow <= time(23,00): 
		show = config['Friday']['show']

	# Saturday
	elif today == 'Saturday' and timenow >= time(9,00) and timenow <= time(23,00): 
		show = config['Saturday']['show']
		subreddit = config['Saturday']['subreddit']
		print(show)
		
	else:
		print('Something went wrong with the time schedule.')

except:
	print('Unable to get show details')


# config.read('showinfo.txt')
# show = config['show']['title']
username = tunefind.username
password = tunefind.password

# Sort the list of seasons and then get the latest one
def get_latest_season(show):

	url = BASE_URL + show
	r = requests.get(url, auth=HTTPBasicAuth(username, password))
	data = r.json()
	startingList = sorted([data['seasons'], []])
	orderedList = max(startingList)
	currentSeason = orderedList[-1]['number']

# Get the latest episode of the latest season
	fullUrl = BASE_URL + show + '/' + 'season-' + currentSeason

	r = requests.get(fullUrl, auth=HTTPBasicAuth(username, password))
	data = r.json()

	startingList = sorted([data['episodes'], []])
	orderedList = max(startingList)
	currentEp = orderedList[-1]['id']

	# print(currentEp)
	# print('\n'.join(['[show]',
	# 				'season = ' + currentSeason,
	# 				'title = ' + show,
	# 				'epid = ' + currentEp]))

	# Make a config file
	print(' '.join(["Writing info for", show, "to config file..."]))
	epInfo = configparser.ConfigParser()
	epInfo['show'] = {'title': show,
							'season': currentSeason,
							'epID': currentEp
							}


	with open('test.ini', 'w') as configfile:
		epInfo.write(configfile)

get_latest_season(show)

# Get song data
BASE_URL = 'https://www.tunefind.com/api/v1/show/'
config = configparser.ConfigParser()
config.read('test.ini')
show = config['show']['title']
season = config['show']['season']
epID = config['show']['epid']

def get_show(show, season, epID):
	
	url = BASE_URL + show + '/' + 'season-' + season + '/' + epID
	username = tunefind.username
	password = tunefind.password
	r = requests.get(url, auth=HTTPBasicAuth(username, password))
	data = r.json()
	# print("Performer | Song | Scene")
	# print(":----------: | :-------------: | :-----")
	header = "Performer | Song | Scene"
	divider = ":----------: | :-------------: | :-----"

	with open('tunes.txt', 'w') as configfile:
				configfile.write('\n'.join(
					["{0}", "{1}"]).format(header, divider))

	# with open('tunes.txt', 'w') as configfile:
	# 	configfile.write('\n'.join(
	# 		["{0}", "{1}"]).format(header, divider))

	for s in data['songs']:
		artist = s['artist']['name']
		song = s['name']
		scene = s['scene']

		with open('tunes.txt', 'a') as configfile:
					configfile.write('\n'+'| '.join([artist, song, scene]))
		
		# print('| '.join([artist, song, scene]))

get_show(show, season, epID)

# Connect to reddit API
config = configparser.ConfigParser()
config.read('keys.txt')
user = config['reddit']['user']
pw = config['reddit']['pass']
user_agent = ("Tunesfinder by /u/kidrocco"
				"github/kbolt/Tunesfinder/")
r = praw.Reddit(user_agent=user_agent)
r.login(user, pw, disable_warning=True)

phraseMatch = ['discussion', 'Discussion','recap']
negWords = ['Live']

conn = sqlite3.connect('tunefinder.db') 
c = conn.cursor()


c.execute('''CREATE TABLE IF NOT EXISTS cachedshows
			(uid integer PRIMARY KEY AUTOINCREMENT,
			 showTitle text, 
			 postID text unique on conflict fail)''')

def get_tunes(query):
	submissions = r.get_subreddit(query)
	stickyTitle = submissions.get_hot(limit=2)
	

	for submission in stickyTitle:
		pastData = c.fetchall()
		title = submission.title.lower()
		showTitle = subreddit
		postID = submission.id
		uid = []
		isMatch = any(string in title for string in phraseMatch)
		ignore = any(string in title for string in negWords)

		if postID not in pastData and isMatch:
			print('posting...')
			# with open('tunes.txt', 'r') as results:
			# 		submission.add_comment(results.read())
		

			cache = [(showTitle, postID)]
			try:
				c.executemany('INSERT INTO cachedshows(showTitle, postID) VALUES (?,?)', (cache))
				conn.commit()
			except:
				print("No new topics found. No post was made.")
		elif postID in pastData and isMatch:
			print("No new topics found. No post was made.")
		# print(isMatch)

		print(submission.title)
	# print(submissions.title)

get_tunes(subreddit)


c.close()
conn.close()