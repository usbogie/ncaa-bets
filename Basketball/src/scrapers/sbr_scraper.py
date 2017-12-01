from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import sys
import re
import json
import os
from helpers import get_soup, make_season

my_path = os.path.dirname(os.path.abspath(__file__))
names_path = os.path.join(my_path,'..','names.json')
data_path = os.path.join(my_path,'..','..','data')

with open(names_path,'r') as infile:
	names_dict = json.load(infile)

def get_data(data=[],get_yesterday=False,get_today=False,year=2018):
	all_dates = make_season(year-1)
	base = "https://www.sportsbookreview.com/betting-odds/ncaa-basketball/?date="
	today = int(datetime.now().strftime('%Y%m%d'))
	yesterday = int((datetime.now()-timedelta(1)).strftime('%Y%m%d'))
	for day in all_dates:
		if today < int(day.replace('-','')):
			continue
		if get_yesterday and yesterday != int(day.replace('-','')):
			continue
		if get_today and today != int(day.replace('-','')):
			continue
		print(day)
		url = base + day.replace('-','')

		content = get_soup(url).read()
		soup = BeautifulSoup(content, "html5lib")

		games = soup.find_all('div', {'class': 'event-holder holder-complete'})

		for game in games:
			teams = game.find('div', {'class': 'el-div eventLine-team'}).find_all('div', {'class': 'eventLine-value'})
			try:
				away = names_dict[teams[0].a.text]
				home = names_dict[teams[1].a.text]
			except:
				print("Can't find {} or {}".format(teams[0].a.text, teams[1].a.text))
				continue




if __name__ == '__main__':
	year = 2018
	cur_season = get_data(year=year)
	csv_path = os.path.join(my_path,'..','..','data','cbbref','{}.csv'.format(year))
	cur_season.to_csv(csv_path, index=False)
