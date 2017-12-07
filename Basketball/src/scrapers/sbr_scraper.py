from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import sys
import re
import json
import os
from shared import get_soup, make_season

my_path = os.path.dirname(os.path.abspath(__file__))
names_path = os.path.join(my_path,'..','organizers','names.json')
data_path = os.path.join(my_path,'..','..','data')

with open(names_path,'r') as infile:
	names_dict = json.load(infile)

def get_data(data=[],get_yesterday=False,get_today=False,year=2018):
	all_dates = make_season(year)
	base = "https://www.sportsbookreview.com/betting-odds/ncaa-basketball/?date="
	today = int(datetime.now().strftime('%Y%m%d'))
	yesterday = int((datetime.now()-timedelta(1)).strftime('%Y%m%d'))
	events = []
	for day in all_dates:
		if today < int(day.replace('-','')):
			continue
		if get_yesterday and yesterday != int(day.replace('-','')):
			continue
		if get_today and today != int(day.replace('-','')):
			continue
		print(day)
		url = base + day.replace('-','')

		soup = get_soup(url)

		games = soup.find_all('div', {'class': 'event-holder holder-complete'})

		for game in games:
			teams = game.find('div', {'class': 'el-div eventLine-team'}).find_all('div', {'class': 'eventLine-value'})
			try:
				away = names_dict[teams[0].a.text]
				home = names_dict[teams[1].a.text]
			except:
				print("Can't find {} or {}".format(teams[0].a.text, teams[1].a.text))
				continue

			event = {}
			open_line = game.find('div', {'class': 'el-div eventLine-opener'}).find_all('div', {'class': 'eventLine-book-value'})
			try:
				home_open_line = open_line[1].text.split()[0].replace("½",".5")
				if 'PK' in home_open_line:
					home_open_line = 0
			except:
				try:
					away_open_line = open_line[0].text.split()[0].replace("½",".5")
					if 'PK' in away_open_line:
						away_open_line = 0
					home_open_line = float(away_open_line) * -1
				except:
					print("No open line listed for {} vs {}".format(away, home))
					continue

			event['home'] = home
			event['away'] = away
			event['date'] = day
			event['open_line'] = float(home_open_line)

			print(event)
			events.append(event)

	for

	return events

if __name__ == '__main__':
	year = 2018
	data = get_data(year=year)
	json_path = os.path.join(my_path,'..','..','data','sbr','{}.json'.format(year))
	with open(json_path,'w') as infile:
		json.dump(data,infile)
