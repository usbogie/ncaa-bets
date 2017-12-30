from datetime import datetime, timedelta
from dateutil import tz
import pandas as pd
from numpy import *
import json
import random
import time
import html
import os
from scrapers.shared import get_soup, make_season, get_season_year, get_date_str
import helpers as h
import sqlite3
my_path = h.path
names_dict = h.read_names()

info = ['Game_ID', 'Away_Abbrv', 'Home_Abbrv', 'Away_Score',
		'Home_Score', 'Game_Away', 'Game_Home','Season',
		'Game_Date','Game_Tipoff', 'Game_Location', 'Neutral_Site']

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
		self.season = get_season_year(date)
		self.tipoff = time
		self.date = self.game_info['date']

		data = array([arange(len(info))])
		self.info_df = pd.DataFrame(data, columns=info)

		self.info_df['Game_ID'] = self.game_id
		self.info_df['Away_Abbrv'] = self.game_info['Away_Abbrv']
		self.info_df['Home_Abbrv'] = self.game_info['Home_Abbrv']
		self.info_df['Away_Score'] = self.game_info['Away_Score']
		self.info_df['Home_Score'] = self.game_info['Home_Score']
		self.info_df['Game_Away'] = self.game_info['Game_Away'].replace('\u00E9', 'e')
		self.info_df['Game_Home'] = self.game_info['Game_Home'].replace('\u00E9', 'e')
		self.info_df['Season'] = self.season
		self.info_df['Game_Date'] = self.date
		self.info_df['Game_Tipoff'] = self.tipoff
		try:
			self.info_df['Game_Location'] = self.game_info['venue']
		except:
			pass
		self.info_df['Neutral_Site'] = self.game_info['neutral_site']

def get_json(soup):
	for link in soup.find_all('script'):
		if 'window.espn.scoreboardData' in str(link.text):
			jsonValue1 = '{%s}' % (link.text.split('{', 1)[1].rsplit('}', 1)[0],)
			jsonValue = jsonValue1.split(';window')[0]
			value = json.loads(jsonValue)
			return value['events']

def get_data(game_url, game_info):
	game = Game(game_url, game_info)
	game.make_dataframes()

	gen_info = game.info_df

	print("Just finished: {} vs {} on {}.".format(gen_info['Away_Abbrv'].values[0],gen_info['Home_Abbrv'].values[0],gen_info['Game_Date'].values[0]))

	return gen_info

def create_day_urls(date):
	ncaa_base = 'http://scores.espn.com/mens-college-basketball/scoreboard/_/date/'
	cbi_base = 'http://www.espn.com/mens-college-basketball/scoreboard/_/group/55/date/'
	cit_base = 'http://www.espn.com/mens-college-basketball/scoreboard/_/group/56/date/'
	url = base_url + date
	box_urls = [url]
	if date[4:6] == '03' or date[4:6] == '04':
		ncaa_url = ncaa_base + date
		cbi_url = cbi_base + date
		cit_url = cit_base + date
		box_urls.extend((ncaa_url, cbi_url, cit_url))
	return box_urls

def get_tonight_info():
	date = datetime.now().strftime('%Y%m%d')
	url = base_url + date

	soup = get_soup(url)

	gen_info = []

	events = get_json(soup)

	for event in events:
		data = array([arange(len(info))])
		game_info = pd.DataFrame(data, columns=info)
		competition = event['competitions'][0]
		game_info['Game_ID'] = event['id']
		game_info['Neutral_Site'] = competition['neutralSite']
		game_info['Game_Date'] = datetime.now().strftime('%Y-%m-%d')
		game_info['Season'] = str(h.this_season)

		competitors	= competition['competitors']
		away = 0
		home = 1
		if competitors[0]['homeAway'] == 'home':
			away = 1
			home = 0

		try:
			game_info['Game_Away'] = names_dict[html.unescape(competitors[away]['team']['location']).replace('\u00E9', 'e')]
			game_info['Game_Home'] = names_dict[html.unescape(competitors[home]['team']['location']).replace('\u00E9', 'e')]
		except:
			print("Unrecognized team, continue on {} vs {}".format(html.unescape(competitors[away]['team']['location']),html.unescape(competitors[home]['team']['location'])))
			continue
		print("{} vs {}".format(game_info['Game_Away'][0], game_info['Game_Home'][0]))
		game_info['Away_Abbrv'] = competitors[away]['team']['abbreviation']
		game_info['Home_Abbrv'] = competitors[home]['team']['abbreviation']
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
	return pd.concat(gen_info, ignore_index=True) if gen_info else pd.DataFrame()


def update_espn_data(date):
	urls = create_day_urls(date.replace('-',''))
	gen_info = []

	for url in urls:
		soup = get_soup(url)

		links = []
		status_dict = {}
		game_notes = []

		events = get_json(soup)
		if events is None or len(events)==0:
			continue

		for event in events:
			status_dict[event['id']] = event['status']['type']['shortDetail']
			if status_dict[event['id']] == 'Canceled':
				continue
			game_info = {}
			game_info['skip_game'] = False
			competition = event['competitions'][0]
			game_info['link'] = event['links'][1]['href']
			game_info['neutral_site'] = competition['neutralSite']
			game_info['attendance']	= competition['attendance']
			game_info['conferenceCompetition'] = competition['conferenceCompetition']
			game_info['tipoff']	= competition['startDate']
			game_info['date'] = date
			try:
				venueJSON = competition['venue']
				game_info['venue'] = venueJSON['fullName']
				if 'address' in venueJSON.keys():
					game_info['venue']+="|"+"|".join([venueJSON['address']['city'],venueJSON['address']['state']])
			except:
				pass

			competitors	= competition['competitors']
			away = 0
			home = 1
			if competitors[0]['homeAway'] == 'home':
				away = 1
				home = 0

			try:
				game_info['Away_Abbrv'] = competitors[away]['team']['abbreviation']
			except:
				game_info['skip_game'] = True

			game_info['Home_Abbrv'] = competitors[home]['team']['abbreviation']
			game_info['Away_Score'] = competitors[away]['score']
			game_info['Home_Score'] = competitors[home]['score']

			try:
				game_info['Game_Away'] = names_dict[html.unescape(competitors[away]['team']['location']).replace('\u00E9', 'e')]
				game_info['Game_Home'] = names_dict[html.unescape(competitors[home]['team']['location']).replace('\u00E9', 'e')]
			except:
				print("Unrecognized team, continue on {} vs {}".format(html.unescape(competitors[away]['team']['location']),html.unescape(competitors[home]['team']['location']).replace('\u00E9', 'e')))
				continue

			try:
				game_info['Away_Games_Played'] = sum([int(item) for item in competitors[away]['records'][0]['summary'].split('-')])
				game_info['Home_Games_Played'] = sum([int(item) for item in competitors[home]['records'][0]['summary'].split('-')])
			except:
				print("No record for team, continue on {} vs {}".format(game_info['Game_Away'],game_info['Game_Home']))
				continue

			links.append(game_info)

		for idx, game_info in enumerate(links):
			url = game_info['link']
			game_id = url.split("=")[-1]
			try:
				if status_dict[game_id] == 'Postponed' or status_dict[game_id] == 'Canceled' or game_info['skip_game']:
					continue

			except:
				print("something went wrong, some dumb shit. CONTINUE")
				continue

			else:
				gm_info = get_data(url, game_info)
				gen_info.append(gm_info)


	return gen_info

def make_year_dataframe(season):
	gen_info = []
	date_list = make_season(season)
	for day in date_list:
		print(day)
		if (datetime.now() - timedelta(1)).strftime('%Y%m%d') < day:
			continue
		gen_info += update_espn_data(day)

	return gen_info


def insert_games(cur, dfs, games):
	final_info = dfs.drop_duplicates(subset=['Game_Home','Game_Away','Game_Date']).reset_index(drop=True)
	items = []
	for index, row in final_info.iterrows():
		if not row['Home_Score'] and not row['Away_Score']:
			continue
		values = [int(index + games) if var == 'Game_ID' 
				  else get_date_str(row['Season'],row[var]) if var == 'Game_Date'
		   		  else row[var] for var in info]
		key = ','.join([row['Game_Home'],row['Game_Away'],get_date_str(row['Season'],row['Game_Date'])])
		items.append(tuple(values + [key]))
	cur.executemany('''INSERT OR REPLACE INTO espn VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', items)
	return len(items)


def create_table(cur):
	cur.execute('''DROP TABLE IF EXISTS espn''')
	cur.execute('''CREATE TABLE espn (Game_ID INTEGER PRIMARY KEY,
		Away_Abbrv TEXT, Home_Abbrv TEXT, Away_Score TEXT, Home_Score TEXT,
		Game_Away TEXT, Game_Home TEXT, Season TEXT, Game_Date TEXT,
		Game_Tipoff TEXT, Game_Location TEXT, Neutral_Site TEXT, Key TEXT)''')


def rescrape(year_list = h.all_years):
	year_list = h.all_years
	with sqlite3.connect(h.database) as db:
		cur = db.cursor()
		create_table(cur)
		games = 0
		for year in year_list:
			info_list = make_year_dataframe(year)
			games += insert_games(cur, pd.concat(info_list, ignore_index=True), games)
		db.commit()


def transfer_to_db():
	with sqlite3.connect(h.database) as db:
		cur = db.cursor()
		create_table(cur)
		dfs = []
		for year in h.all_years:
			csv_path = os.path.join(h.data_path,'espn','{}.csv'.format(year))
			dfs.append(pd.read_csv(csv_path, dtype=str))
		insert_games(cur, pd.concat(dfs, ignore_index=True),0)
		db.commit()


if __name__ == '__main__':
	# today_data = get_tonight_info()
	# today_data.drop_duplicates().to_csv('upcoming_games.csv', index_label='Game_ID')
	# print("Updated ESPN Data")
	'''
	start_season = 2011
	info_list = make_year_dataframe(start_season)
	final_info = pd.concat(info_list, ignore_index=True).set_index('Game_ID')
	csv_path = os.path.join(my_path,'..','..','data','espn','{}.csv'.format(start_season))
	final_info.drop_duplicates().to_csv(csv_path)
	'''