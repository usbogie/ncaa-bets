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
import json
import sys
import html


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
	ncaa_base = 'http://scores.espn.com/mens-college-basketball/scoreboard/_/date/'
	url = base + date
	box_urls = [url]
	if date[4:6] == '03' or date[4:6] == '04':
		tourney_url = ncaa_base + date
		box_urls.append(tourney_url)
	return box_urls

def get_data(game_url, game_info):
	game = Game(game_url, game_info)
	game.make_dataframes()

	gen_info = game.info_df

	#print("Just finished: {} vs {} on {}".format(gen_info['Away_Abbrv'].values[0],gen_info['Home_Abbrv'].values[0],gen_info['Game_Date'].values[0]))
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
				status_dict[event['id']] = event['status']['type']['shortDetail']
				if status_dict[event['id']] == 'Canceled':
					continue

				game_info 							= {}
				game_info['skip_game']				= False
				competition 						= event['competitions'][0]
				game_info['link']					= event['links'][1]['href']
				game_info['neutral_site']			= competition['neutralSite']
				game_info['attendance']				= competition['attendance']
				game_info['conferenceCompetition']	= competition['conferenceCompetition']
				game_info['tipoff']					= competition['startDate']
				try:
					venueJSON						= competition['venue']
					game_info['venue'] = venueJSON['fullName']
					if 'address' in venueJSON.keys():
						game_info['venue']+="|"+"|".join([venueJSON['address']['city'],venueJSON['address']['state']])
				except:
					pass
				away = 0
				home = 1
				competitors	= competition['competitors']
				if competitors[0]['homeAway'] == 'home':
					away = 1
					home = 0

				try:
					game_info['Away_Abbrv'] = competitors[away]['team']['abbreviation']
				except:
					game_info['skip_game'] = True
				game_info['Home_Abbrv'] = competitors[home]['team']['abbreviation']
				game_info['Game_Away'] = html.unescape(competitors[away]['team']['location']).replace('\u00E9', 'e')
				game_info['Game_Home'] = html.unescape(competitors[home]['team']['location']).replace('\u00E9', 'e')
				print(game_info['Game_Away'], game_info['Game_Home'], day)
				game_info['Away_Score'] = competitors[away]['score']
				game_info['Home_Score'] = competitors[home]['score']
				try:
					game_info['Away_Games_Played'] = sum([int(item) for item in competitors[away]['records'][0]['summary'].split('-')])
					game_info['Home_Games_Played'] = sum([int(item) for item in competitors[home]['records'][0]['summary'].split('-')])
				except:
					print("No record for a team. Not D1")
					continue
				links.append(game_info)

				try:
					game_notes.append(event['notes']['headline'])
				except:
					game_notes.append(None)

			for idx, game_info in enumerate(links):
				url = game_info['link']
				game_id = url.split("=")[-1]
				if status_dict[game_id] == 'Postponed' or status_dict[game_id] == 'Canceled' or game_info['skip_game']:
					continue

				else:
					gm_info = get_data(url, game_info)
					gen_info.append(gm_info)

	return gen_info

if __name__ == '__main__':
	start_year = 2011
	info_list = make_overall_df(start_year)
	final_info = pd.concat(info_list, ignore_index=True).set_index('Game_ID')
	final_info.drop_duplicates().to_csv("game_info{}.csv".format(start_year + 1))

	print("\n\nFinished uploading to CSVs")
