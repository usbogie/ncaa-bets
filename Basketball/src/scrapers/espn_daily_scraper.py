from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from dateutil import tz
import urllib.request as request
import urllib.error as error
import pandas as pd
from numpy import *
import json
import random
import time
import html
import os

ua = UserAgent()

my_path = os.path.dirname(os.path.abspath(__file__))
names_path = os.path.join(my_path, 'name_dicts', 'espn_names.json')
with open(names_path,'r') as infile:
	names_dict = json.load(infile)

info = ['Game_ID', 'Away_Abbrv', 'Home_Abbrv', 'Away_Score',
		'Home_Score', 'Game_Away', 'Game_Home','Game_Year',
		'Game_Date','Game_Tipoff', 'Game_Location', 'Neutral_Site',
		'Conference_Competition', 'Attendance']

base_url = "http://scores.espn.com/mens-college-basketball/scoreboard/_/group/50/date/"

class Game(object):
	def __init__(self, url, game_info):

		self.from_zone = tz.gettz('UTC')
		self.to_zone = tz.gettz('America/Chicago')

		self.game_id = url.split("=")[1]
		self.game_info = game_info


	def make_dataframes(self):
		dateTime = " ".join(self.game_info['tipoff'].split('T'))[:-1]
		utc = datetime.strptime(dateTime, '%Y-%m-%d %H:%M')
		eastern = utc.replace(tzinfo=self.from_zone).astimezone(self.to_zone)
		date, time = str(eastern)[:-6].split(" ")
		self.year = date.split('-')[0]
		self.tipoff = time
		self.date = "{}/{}".format(date.split("-")[1],date.split("-")[2])

		data = array([arange(len(info))])
		self.info_df = pd.DataFrame(data, columns=info)

		self.info_df['Game_ID'] = self.game_id
		self.info_df['Away_Abbrv'] = self.game_info['Away_Abbrv']
		self.info_df['Home_Abbrv'] = self.game_info['Home_Abbrv']
		self.info_df['Away_Score'] = self.game_info['Away_Score']
		self.info_df['Home_Score'] = self.game_info['Home_Score']
		self.info_df['Game_Away'] = self.game_info['Game_Away'].replace('\u00E9', 'e')
		self.info_df['Game_Home'] = self.game_info['Game_Home'].replace('\u00E9', 'e')
		self.info_df['Game_Year'] = self.year
		self.info_df['Game_Date'] = self.date
		self.info_df['Game_Tipoff'] = self.tipoff
		self.info_df['Game_Location'] = self.game_info['venue']
		self.info_df['Neutral_Site'] = self.game_info['neutral_site']
		self.info_df['Conference_Competition'] = self.game_info['conferenceCompetition']
		self.info_df['Attendance'] = self.game_info['attendance']

def get_json(soup):
	for link in soup.find_all('script'):
		if 'window.espn.scoreboardData' in str(link.text):
			jsonValue1 = '{%s}' % (link.text.split('{', 1)[1].rsplit('}', 1)[0],)
			jsonValue = jsonValue1.split(';window')[0]
			value = json.loads(jsonValue)
			return value['events']


def get_page(url):
	try:
		return request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
	except error.HTTPError as e:
		try:
			wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
			time.sleep(wait_time)
			print("First attempt for %s failed. Trying again." % (d))
			return request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
		except:
			print(e)
			sys.exit()

def get_data(game_url, game_info):
	game = Game(game_url, game_info)
	game.make_dataframes()

	gen_info = game.info_df

	print("Just finished: {} vs {} on {}.".format(gen_info['Away_Abbrv'].values[0],gen_info['Home_Abbrv'].values[0],gen_info['Game_Date'].values[0]))

	return gen_info

def update_espn_data():
	date = (datetime.now() - timedelta(1)).strftime('%Y%m%d')
	url = base_url + date
	# ncaa_base = 'http://scores.espn.com/mens-college-basketball/scoreboard/_/date/'
	# url_ncaa = base + date
	# if date[4:6] == '03' or date[4:6] == '04':
	# 	tourney_url = ncaa_base + date
	# 	box_urls.append(tourney_url)

	page = get_page(url)

	content = page.read()
	soup = BeautifulSoup(content, "html5lib")

	gen_info = []

	links = []
	status_dict = {}
	game_notes = []
	events = []
	for link in soup.find_all('script'):
		if 'window.espn.scoreboardData' in str(link.text):
			jsonValue1 = '{%s}' % (link.text.split('{', 1)[1].rsplit('}', 1)[0],)
			jsonValue = jsonValue1.split(';window')[0]
			value = json.loads(jsonValue)
			events = value['events']

	for event in events:
		status_dict[event['id']] = event['status']['type']['shortDetail']
		if status_dict[event['id']] == 'Canceled':
			continue
		game_info 							= {}
		game_info['link']					= event['links'][1]['href']
		competition 						= event['competitions'][0]
		game_info['neutral_site']			= competition['neutralSite']
		game_info['attendance']				= competition['attendance']
		game_info['conferenceCompetition']	= competition['conferenceCompetition']
		game_info['tipoff']					= competition['startDate']
		venueJSON							= competition['venue']

		game_info['venue'] = venueJSON['fullName']
		if 'address' in venueJSON.keys():
			game_info['venue']+="|"+"|".join([venueJSON['address']['city'], venueJSON['address']['state']])

		competitors	= competition['competitors']
		away = 0
		home = 1
		if competitors[0]['homeAway'] == 'home':
			away = 1
			home = 0
		game_info['Away_Abbrv'] = competitors[away]['team']['abbreviation']
		game_info['Home_Abbrv'] = competitors[home]['team']['abbreviation']
		try:
			game_info['Game_Away'] = names_dict[html.unescape(competitors[away]['team']['location']).replace('\u00E9', 'e')]
			game_info['Game_Home'] = names_dict[html.unescape(competitors[home]['team']['location']).replace('\u00E9', 'e')]
		except:
			print("Continue on {} vs {}".format(html.unescape(competitors[away]['team']['location']),html.unescape(competitors[home]['team']['location']).replace('\u00E9', 'e')))
			continue
		game_info['Away_Score'] = competitors[away]['score']
		game_info['Home_Score'] = competitors[home]['score']

		links.append(game_info)

		if date[4:6] == '03' or date[4:6] == '04' and 'notes' in event.keys():
			game_notes.append(event['notes']['headline'])
		else:
			game_notes.append(None)

	for idx, game_info in enumerate(links):
		url = game_info['link']
		game_id = url.split("=")[-1]
		if status_dict[game_id] == 'Postponed' or status_dict[game_id] == 'Canceled':
			continue
		else:
			gm_info = get_data(url, game_info)
			gen_info.append(gm_info)
	try:
		return pd.concat(gen_info, ignore_index=True).set_index('Game_ID')
	except:
		return pd.DataFrame()

def get_tonight_info():
	date = datetime.now().strftime('%Y%m%d')
	url = base_url + date

	content = get_page(url).read()
	soup = BeautifulSoup(content, "html5lib")

	gen_info = []

	events = get_json(soup)

	for event in events:
		data = array([arange(len(info))])
		game_info = pd.DataFrame(data, columns=info)
		competition = event['competitions'][0]
		game_info['Game_ID'] = event['id']
		game_info['Neutral_Site'] = competition['neutralSite']
		game_info['Conference_Competition']	= competition['conferenceCompetition']
		game_info['Attendance']	= competition['attendance']
		game_info['Game_Date'] = date[4:6]+'/'+date[6:]
		game_info['Game_Year'] = date[:4]

		competitors	= competition['competitors']
		away = 0
		home = 1
		if competitors[0]['homeAway'] == 'home':
			away = 1
			home = 0
		game_info['Away_Abbrv'] = competitors[away]['team']['abbreviation']
		game_info['Home_Abbrv'] = competitors[home]['team']['abbreviation']
		try:
			game_info['Game_Away'] = names_dict[html.unescape(competitors[away]['team']['location']).replace('\u00E9', 'e')]
			game_info['Game_Home'] = names_dict[html.unescape(competitors[home]['team']['location']).replace('\u00E9', 'e')]
		except:
			print("Continue on {} vs {}".format(html.unescape(competitors[away]['team']['location']),html.unescape(competitors[home]['team']['location'])))
			continue
		game_info['Away_Score'] = competitors[away]['score']
		game_info['Home_Score'] = competitors[home]['score']

		dateTime = " ".join(competition['startDate'].split('T'))[:-1]
		utc = datetime.strptime(dateTime, '%Y-%m-%d %H:%M')
		eastern = utc.replace(tzinfo=tz.gettz('UTC')).astimezone(tz.gettz('America/New_York'))
		game_info['Game_Tipoff'] = str(eastern)[:-6].split(" ")[1]

		venueJSON = competition['venue']
		if 'address' in venueJSON.keys():
			game_info['Game_Location'] = "|".join([venueJSON['fullName'],venueJSON['address']['city'],venueJSON['address']['state']])
		else:
			game_info['Game_Location'] = venueJSON['fullName']

		gen_info.append(game_info)
	try:
		return pd.concat(gen_info, ignore_index=True).set_index('Game_ID')
	except:
		return pd.DataFrame()

if __name__ == '__main__':
	# today_data = get_tonight_info()
	# today_data.drop_duplicates().to_csv('upcoming_games.csv', index_label='Game_ID')
	# print("Updated ESPN Data")

	last_night = update_espn_data()
	csv_path = os.path.join(my_path,'..','..','data','espn','2017.csv')
	cur_season = pd.read_csv(csv_path, index_col='Game_ID')
	cur_season_indices = [str(idx) for idx in list(cur_season.index.values)]
	for index, row in last_night.iterrows():
		if index not in cur_season_indices:
			cur_season = cur_season.append(row)
	cur_season = cur_season[~cur_season.index.duplicated(keep='first')]
	cur_season.to_csv(csv_path, index_label='Game_ID')
