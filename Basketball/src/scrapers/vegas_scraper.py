from datetime import datetime, timedelta, date
import re
import json
import os
from scrapers.shared import get_soup, make_season

my_path = os.path.dirname(os.path.abspath(__file__))
names_path = os.path.join(my_path,'..','organizers','names.json')

with open(names_path,'r') as infile:
	names_dict = json.load(infile)

def ordered(obj):
	if isinstance(obj, dict):
		return sorted((k, ordered(v)) for k, v in obj.items())
	if isinstance(obj, list):
		return sorted(ordered(x) for x in obj)
	else:
		return obj

def add_open_lines(games, day, yesterday_could_not_find, today_can_not_find):
	yesterday_could_not_find = today_can_not_find[:]
	for match in yesterday_could_not_find:
		found = False
		for game in games:
			if game['home'] == match['home'] and game['away'] == match['away']:
				game['open_line'] = match['open_line']
				found = True
				print('Found and updated yesterday line: {} at {} as {}'.format(match['away'], match['home'], match['open_line']))
				break
		if not found:
			print('Cannot update yesterday line: {} at {} as {}'.format(match['away'], match['home'], match['open_line']))

	today_can_not_find = []
	base = "https://www.sportsbookreview.com/betting-odds/ncaa-basketball/?date="
	url = base + day.replace('-','')

	soup = get_soup(url)

	matches = soup.find_all('div', {'class': 'event-holder holder-complete'})

	for match in matches:
		teams = match.find('div', {'class': 'el-div eventLine-team'}).find_all('div', {'class': 'eventLine-value'})
		try:
			away = names_dict[teams[0].a.text]
			home = names_dict[teams[1].a.text]
		except:
			print("Can't find {} or {}".format(teams[0].a.text, teams[1].a.text))
			continue

		open_line = match.find('div', {'class': 'el-div eventLine-opener'}).find_all('div', {'class': 'eventLine-book-value'})
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
		found = False
		for game in games:
			if game['home'] == home and game['away'] == away:
				game['open_line'] = home_open_line
				found = True
				print('Found and updated: {} at {} as {}'.format(away, home, home_open_line))
				break
		if not found:
			missing_game = {}
			missing_game['home'] = home
			missing_game['away'] = away
			missing_game['open_line'] = home_open_line
			today_can_not_find.append(missing_game)
			print('Cannot update: {} at {} as {}'.format(away, home, home_open_line))

	return yesterday_could_not_find, today_can_not_find


def get_data(data=[],get_yesterday=False,get_today=False,year=2018):
	yesterday_could_not_find = list()
	today_can_not_find = list()
	all_dates = make_season(year)
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

		soup = get_soup(url)

		game_tables = soup.findAll('div', {'class': 'SLTables1'})
		if len(game_tables) == 0:
			print("No games, skipping day")

		games = []

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
				try:
					game_info['away'] = names_dict[away_info[0].a.text]
				except:
					game_info['away'] = names_dict[away_info[0].font.text]
				game_info['home'] = names_dict[home_info[0].a.text]
				print(game_info['away'], game_info['home'])
			except:
				try:
					print('continuing on {} vs {}'.format(away_info[0].a.text, home_info[0].a.text))
				except:
					pass
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
				game_info['open_line'] = game_info['close_line']

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
				games.append(game_info)

		yesterday_could_not_find, today_can_not_find = add_open_lines(games, day, yesterday_could_not_find, today_can_not_find)
		data += games

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
