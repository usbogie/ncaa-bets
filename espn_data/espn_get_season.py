from bs4 import BeautifulSoup
import urllib.request as request
import urllib.error as error
from fake_useragent import UserAgent
from espn_game_parse import Game
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
import random
import fileinput
import json
import sys


ua = UserAgent()

def make_season(start_year):

	months = ['11', '12', '01', '02', '03', '04']

	dates = {'11': list(range(31)[1:]), '12': list(range(32)[1:]), '01': list(range(32)[1:]), '02': list(range(29)[1:]),
			 '03': list(range(32)[1:]), '04': list(range(9)[1:])}

	all_season = []
	for month in months:
		if month in ['01', '02', '03', '04']:
			year = start_year + 1
			if year % 4 == 0:
				dates['02'].append(29)
		else:
			year = start_year
		for d in dates[month]:
			day = str(d)
			if len(day) == 1:
				day = '0'+day
			date = str(year)+month+day
			all_season.append(date)

	return all_season

def create_day_url(base, date):
	box_urls = []
	url = base + date + '&confId=50'
	box_urls.append(url)
	if date[4:6] == '03' or date[4:6] == '04':
		tourney_url = base + date
		box_urls.append(tourney_url)
	return box_urls

def get_data(game_url, ua, tourney_df, ncaa, game_info):
	game = Game(game_url, ua, tourney_df, ncaa, game_info)
	if game.exist == False:
		return "continue"
	game.make_dataframes()

	gen_info = game.info_df

	print("Just finished: {} vs {} on {}".format(game.away_abbrv, game.home_abbrv, game.date))
	return gen_info


def make_overall_df(start_year):

	gen_info = []
	date_list = make_season(start_year)

	base_url = "http://scores.espn.com/mens-college-basketball/scoreboard/_/group/50/date/"
	for day in date_list:
		if (datetime.now() - timedelta(1)).strftime('%Y-%m-%d').replace('-','') < day:
			continue

		day_urls = create_day_url(base_url, day)

		for d in day_urls:
			try:
				page = request.urlopen(request.Request(d, headers = { 'User-Agent' : ua.random }))
			except error.HTTPError as e:
				try:
					wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
					time.sleep(wait_time)
					print("First attempt for %s failed. Trying again." % (d))
					page = request.urlopen(request.Request(d, headers = { 'User-Agent' : ua.random }))
				except:
					print(e)
					sys.exit()

			content = page.read()
			soup = BeautifulSoup(content, "html5lib")

			events = []
			for link in soup.find_all('script'):
				if 'window.espn.scoreboardData' in str(link.text):
					jsonValue = '{%s}' % (link.text.split('{', 1)[1].rsplit('}', 1)[0],)
					value = json.loads(jsonValue.split(';window')[0])
					events = value['events']

			if len(events) == 0:
				continue

			links = []
			status_dict = {}
			game_notes = []
			for event in events:
				status_dict[event['id']]			= event['status']['type']['shortDetail']
				game_info 							= {}
				game_info['link']					= event['links'][1]['href']
				competition 						= event['competitions'][0]
				game_info['neutral_site']			= competition['neutralSite']
				game_info['attendance']				= competition['attendance']
				game_info['conferenceCompetition']	= competition['conferenceCompetition']
				venueJSON							= competition['venue']

				if 'address' in venueJSON.keys():
					game_info['venue'] = "|".join([venueJSON['fullName'],venueJSON['address']['city'],venueJSON['address']['state']])
				else:
					game_info['venue'] = venueJSON['fullName']

				links.append(game_info)

				try: 
					game_notes.append(event['notes']['headline'])
				except:
					game_notes.append(None)

			for idx, game_info in enumerate(links):
				url = game_info['link']
				game_id = url.split("=")[-1]
				if status_dict[game_id] == 'Postponed' or status_dict[game_id] == 'Canceled':
					continue

				else:
					# Making a small dataframe that contains tourney-specific information
					tourney_col = ['Tournament', 'Round', 'Away_Seed', 'Home_Seed']
					ncaa = False
					data = np.array([np.repeat(np.nan,4)])
					tourney_df = pd.DataFrame(data, columns=tourney_col)

					try:
						note = game_notes[idx]
						tourney_split = note.split(' - ')
						if tourney_split[0]:
							tourney_df['Tournament'] = tourney_split[0]
							round_split = tourney_split[-1].split(' AT ')

							if tourney_split[0] == "MEN'S BASKETBALL CHAMPIONSHIP":
								ncaa = True
							if round_split[0]:
								tourney_df['Round'] = round_split[0]
					except:
						pass

					gm_info = get_data(url, ua, tourney_df, ncaa, game_info)
					if isinstance(gm_info, str):
						continue
					gen_info.append(gm_info)
					"""
					if gm_stats is not None:
						#players.append(gm_players)
						game_stats.append(gm_stats)
					"""

			chance = range(100)
			choice = random.choice(chance)
			if choice < 10:
				big_wait_time = round(max(25, 28 + random.gauss(0,2)), 2)
				print("Big wait of %d seconds\n\n" % big_wait_time)
				time.sleep(big_wait_time)

	return gen_info

if __name__ == '__main__':

	start_year = 2013
	info_list = make_overall_df(start_year)
	final_info = pd.concat(info_list, ignore_index=True).set_index('Game_ID')
	#final_players = pd.concat(players_list, ignore_index=True)
	#final_gm_stats = pd.concat(gm_stats_list, ignore_index=True)

	final_info.drop_duplicates().to_csv("game_info2014.csv")
	#final_players.to_csv("players.csv", index=False)
	#final_gm_stats.to_csv("game_stats.csv", index=False)

	start_year = 2014
	info_list = make_overall_df(start_year)
	final_info = pd.concat(info_list, ignore_index=True).set_index('Game_ID')
	final_info.drop_duplicates().to_csv("game_info2015.csv")

	start_year = 2015
	info_list = make_overall_df(start_year)
	final_info = pd.concat(info_list, ignore_index=True).set_index('Game_ID')
	final_info.drop_duplicates().to_csv("game_info2016.csv")

	start_year = 2016
	info_list = make_overall_df(start_year)
	final_info = pd.concat(info_list, ignore_index=True).set_index('Game_ID')
	final_info.drop_duplicates().to_csv("game_info2017.csv")

	print("\n\nFinished uploading to CSVs")
