from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from espn_game_parse import Game
from dateutil import tz
import urllib.request as request
import urllib.error as error
import pandas as pd
from numpy import *
import json
import random
import time
import html



ua = UserAgent()

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
	base = "http://scores.espn.com/mens-college-basketball/scoreboard/_/group/50/date/"
	date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d').replace('-','')
	url = base + date + '&confId=50'

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
			game_info['venue']+="|"+"|".join([venueJSON['address']['city'],venueJSON['address']['state']])

		competitors	= competition['competitors']
		away = 0
		home = 1
		if competitors[0]['homeAway'] == 'home':
			away = 1
			home = 0
		game_info['Away_Abbrv'] = competitors[away]['team']['abbreviation']
		game_info['Home_Abbrv'] = competitors[home]['team']['abbreviation']
		game_info['Game_Away']  = html.unescape(competitors[away]['team']['location'])
		game_info['Game_Home']  = html.unescape(competitors[home]['team']['location'])
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

	return pd.concat(gen_info, ignore_index=True).set_index('Game_ID')

def get_tonight_info():
	base = "http://scores.espn.com/mens-college-basketball/scoreboard/_/group/50/date/"
	date = datetime.now().strftime('%Y-%m-%d').replace('-','')
	url = base + date + '&confId=50'

	page = get_page(url)
	content = page.read()
	soup = BeautifulSoup(content, "html5lib")

	gen_info = []

	events = get_json(soup)

	for event in events:
		info = ['Game_ID', 'Away_Abbrv', 'Home_Abbrv', 'Away_Score', 'Home_Score',
				'Game_Away', 'Game_Home','Game_Year', 'Game_Date','Game_Tipoff',
				'Game_Location', 'Neutral_Site', 'Conference_Competition', 'Attendance']
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
		game_info['Game_Away'] = html.unescape(competitors[away]['team']['location'])
		game_info['Game_Home'] = html.unescape(competitors[home]['team']['location'])
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

	return pd.concat(gen_info, ignore_index=True).set_index('Game_ID')


if __name__ == '__main__':
	last_night = update_espn_data()
	print(last_night)
	cur_season = pd.read_csv('espn_data/game_info2017.csv', index_col='Game_ID')
	cur_season_indices = [idx.astype(int32) for idx in list(cur_season.index.values)]
	for index, row in last_night.iterrows():
		if int(index) not in list(cur_season.index.values):
			cur_season.append(row)
	cur_season = pd.concat([cur_season,last_night])
	cur_season = cur_season[~cur_season.index.duplicated(keep='first')]
	cur_season.to_csv('espn_data/game_info2017.csv', index_label='Game_ID')

	today_data = get_tonight_info()
	today_data.drop_duplicates().to_csv('espn_data/upcoming_games.csv', index_label='Game_ID')