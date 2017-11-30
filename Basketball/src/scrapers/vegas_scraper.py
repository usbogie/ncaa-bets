from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import re
import json
import os
from helpers import get_soup, make_season

my_path = os.path.dirname(os.path.abspath(__file__))
names_path = os.path.join(my_path,'..','names.json')

with open(names_path,'r') as infile:
	names_dict = json.load(infile)

def ordered(obj):
	if isinstance(obj, dict):
		return sorted((k, ordered(v)) for k, v in obj.items())
	if isinstance(obj, list):
		return sorted(ordered(x) for x in obj)
	else:
		return obj

def get_open_line(table):
	link = table.find('a', text='BT Movements')['href']
	url = 'http://www.vegasinsider.com{}/linechanges/y'.format(link)

	content = get_soup(url).read()
	soup = BeautifulSoup(content, "html5lib")

	if soup.find('h1', {'class': 'page_title'}).text == 'Scoreboard':
		return -1000

	rows = soup.find('table', { 'class': 'rt_railbox_border2' }).findAll('tr')[3:]
	for row in rows:
		items = row.findAll('td')
		try:
			home_open = items[8].text.strip()
			home_percent = items[9].text.strip()
			away_percent = items[12].text.strip()
		except:
			return -1000

		if not (home_percent=='n/a' or home_percent=='0%' and away_percent=='0%'):
			if home_open == '+PK':
				return 0.0
			else:
				return float(home_open)

	return -1000

def get_data(data=[],get_yesterday=False,get_today=False,year=2018):
	all_dates = make_season(year-1)
	base = "http://www.vegasinsider.com/college-basketball/matchups/matchups.cfm/date/"
	today = int(datetime.now().strftime('%Y%m%d'))
	yesterday = int((datetime.now()-timedelta(1)).strftime('%Y%m%d'))
	for day in all_dates:
		if today < int(day.replace('-','')):
			continue
		if get_yesterday and yesterday != int(day.replace('-','')):
			continue
		if get_today and today != int(day.replace('-','')):
			continue
		print (day)
		url_day = "-".join(day.split('-')[1:]+day.split('-')[:1])
		url = base+url_day

		content = get_soup(url).read()
		soup = BeautifulSoup(content, "html5lib")

		game_tables = soup.findAll('div', {'class': 'SLTables1'})
		if len(game_tables) == 0:
			print("No games, skipping day")

		for table in game_tables:
			game_info = {}
			time = table.find('td', {'class': 'viSubHeader1 cellBorderL1 headerTextHot padLeft'}).text

			if time.startswith('12:') or time.startswith('1:') or time.startswith('4:') or time.startswith('2:') and 'AM' in time :
				date = datetime.strptime(day, '%Y-%m-%d')
				newdate = date - timedelta(1)
				game_info['date'] = newdate.strftime('%Y-%m-%d')
			elif time == 'Postponed':
				continue
			else:
				game_info['date'] = day

			info = table.find('td', {'class': 'viBodyBorderNorm'}).table.tbody.contents
			away_info = info[4].contents[1::2]
			home_info = info[6].contents[1::2]

			try:
				class_search = 'tabletext' if year < 2014 else 'tableText'
				game_info['away'] = names_dict[away_info[0].a.text]
				game_info['home'] = names_dict[home_info[0].a.text]
				print(game_info['away'], game_info['home'])
			except:
				print('continuing on {} vs {}'.format(away_info[0].a.text, home_info[0].a.text))
				continue

			game_info['away_ats'] = re.sub('\s+','',away_info[3].text)
			game_info['home_ats'] = re.sub('\s+','',home_info[3].text)

			initial_favorite = 'away'
			if "-" in home_info[4].text or ("-" not in away_info[4].text and "-" in home_info[5].text):
				initial_favorite = 'home'

			if initial_favorite == 'away':
				game_info['open_line'] = re.sub('\s+','',away_info[4].text)
				game_info['close_line'] = re.sub('\s+','',away_info[5].text)
				game_info['over_under'] = re.sub('\s+','',home_info[5].text)

				if game_info['close_line'] == "" or float(game_info['close_line']) > 0:
					if '-' in home_info[5].text:
						game_info['close_line'] = float(re.sub('\s+','',home_info[5].text))
						game_info['over_under'] = re.sub('\s+','',away_info[5].text)
				else:
					game_info['close_line'] = abs(float(game_info['close_line']))

				if game_info['open_line'] != "":
					game_info['open_line'] = abs(float(game_info['open_line']))
			else:
				game_info['open_line'] = re.sub('\s+','',home_info[4].text)
				game_info['close_line'] = re.sub('\s+','',home_info[5].text)
				game_info['over_under'] = re.sub('\s+','',away_info[5].text)

				if game_info['close_line'] == "" or float(game_info['close_line']) > 0:
					if '-' in away_info[5].text:
						game_info['close_line'] = abs(float(re.sub('\s+','',away_info[5].text)))
						game_info['over_under'] = re.sub('\s+','',home_info[5].text)
				else:
					game_info['close_line'] = float(game_info['close_line'])

				if game_info['open_line'] != "":
					game_info['open_line'] = float(game_info['open_line'])

			if game_info['open_line'] == "":
				print("No open line, checking line logs")
				try:
					candidate_open = get_open_line(table)
				except:
					candidate_open = -1000
				print("Found open line: "+str(candidate_open))
				if candidate_open == -1000:
					game_info['open_line'] = game_info['close_line']
				else:
					game_info['open_line'] = candidate_open

			if str(game_info['open_line']) == str(game_info['close_line']) and \
					str(game_info['close_line']) == str(game_info['over_under']) and \
					game_info['over_under'] != "":
				game_info['open_line'] = 0.0
				game_info['close_line'] = 0.0

			if str(game_info['close_line'])==str(game_info['over_under']) and \
					game_info['over_under'] != "":
				game_info['close_line'] = 0.0

			if game_info['over_under'] != "":
				game_info['over_under'] = float(game_info['over_under'])

			game_info['away_side_pct'] = re.sub('\s+','',away_info[8].text.replace('%', ''))
			game_info['home_side_pct'] = re.sub('\s+','',home_info[8].text.replace('%', ''))
			game_info['over_pct'] = re.sub('\s+','',away_info[10].text.replace('%', ''))
			add = True
			for line in data:
				if ordered(line) == ordered(game_info):
					add = False
			if add:
				data.append(game_info)
	return data

if __name__ == '__main__':
	year = 2018
	data = get_data(year=year)
	json_path = os.path.join(my_path,'..','..','data','vi','{}.json'.format(year))
	with open(json_path,'w') as infile:
		json.dump(data,infile)
	# data = get_data(get_today = True)
	# with open('vegas_today.json', 'w') as outfile:
	# 	json.dump(data, outfile)
	# print("Updated vegas info for today")
