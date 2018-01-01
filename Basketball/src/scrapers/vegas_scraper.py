from datetime import datetime, timedelta, date
import re
import json
import os
from scrapers.shared import get_soup, make_season, get_season_year
import helpers as h
import sqlite3
import pandas as pd

my_path = h.path
names_dict = h.read_names()
info = ["home", "away", "open_line", "close_line", "date", "season", "home_ats", "away_ats",
		"over_under", "over_pct", "away_side_pct", "home_side_pct"]

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
		except Exception as e:
			print("Can't find {} in {} vs {}".format(e, teams[0].a.text, teams[1].a.text))
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


def get_data(days=[], today=False):
	data = []
	yesterday_could_not_find = list()
	today_can_not_find = list()
	base = "http://www.vegasinsider.com/college-basketball/matchups/matchups.cfm/date/"
	today = int(datetime.now().strftime('%Y%m%d'))
	for day in days:
		tomorrow = False
		day_int = int(day.replace('-',''))
		if day_int - today == 1 and today:
			tomorrow = True
		elif today < day_int:
			continue
		else:
			print(day)
		year = int(get_season_year(day))
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

			if (time.startswith('12:') or time.startswith('1:') or time.startswith('4:') or time.startswith('2:')) and 'AM' in time :
				if not tomorrow and today:
					continue
				date = datetime.strptime(day, '%Y-%m-%d')
				newdate = date - timedelta(1)
				game_info['date'] = newdate.strftime('%Y-%m-%d')
			elif time == 'Postponed':
				continue
			else:
				if tomorrow:
					continue
				game_info['date'] = day
			game_info['season'] = str(year)
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
			except Exception as e:
				try:
					#print(e)
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

	return pd.DataFrame(data)


def insert_games(vdf,edf,year):
	items = []
	vdf = vdf.drop_duplicates(['home','away','date'])
	i = 0
	for index, row in vdf.iterrows():
		matches = edf[(edf.Game_Home == row['home']) & (edf.Game_Away == row['away'])]
		key = -1
		flip = False
		for index2, match in matches.iterrows():
			if abs((datetime.strptime(row['date'], '%Y-%m-%d') - datetime.strptime(match['Game_Date'], '%Y-%m-%d')).days) <= 1:
				if key != -1:
					print("Found multiple results for {} vs {} on {}".format(row['away'],row['home'],row['date']))
					if row['date'] == match['Game_Date']:
						key = match['Game_ID']
				else:
					key = match['Game_ID']
		if key == -1:
			matches = edf[(edf.Game_Home == row['away']) & (edf.Game_Away == row['home'])]
			for index2, match in matches.iterrows():
				if abs((datetime.strptime(row['date'], '%Y-%m-%d') - datetime.strptime(match['Game_Date'], '%Y-%m-%d')).days) <= 1:
					if key != -1:
						print("Found multiple results for {} vs {} on {}".format(row['home'],row['away'],row['date']))
						if row['date'] == match['Game_Date']:
							key = match['Game_ID']
					else:
						key = match['Game_ID']
					flip = True
		if key == -1:
			#print("Match not found in vi: {} vs {} on {}".format(row['home'],row['away'],row['date']))
			i += 1
		values = None
		if flip:
			values = (row['away'], row['home'], -1 * row['open_line'], -1 * row['close_line'], row['date'],
				row['season'], row['away_ats'], row['home_ats'], row['over_under'], row['over_pct'],
				row['away_side_pct'], row['home_side_pct'], key)
		else:
			values = tuple([row[var] for var in info] + [key])
		items.append(values)
	print("Missed {}/{} games in {} in vi".format(i,len(vdf.index),year))
	return items


def create_table(cur):
	cur.execute('''DROP TABLE IF EXISTS vegas''')
	cur.execute('''CREATE TABLE vegas (home TEXT, away TEXT, 
		open_line REAL, close_line REAL, date TEXT, season TEXT,
		home_ats TEXT, away_ats TEXT, over_under TEXT, over_pct TEXT, 
		home_side_pct TEXT, away_side_pct TEXT, Game_ID INTEGER,
		FOREIGN KEY (Game_ID) REFERENCES espn(Game_ID))''')


def rescrape(year_list = h.all_years):
	year_list = h.all_years
	with sqlite3.connect(h.database) as db:
		cur = db.cursor()
		create_table(cur)
		for year in year_list:
			season_df = get_data(days=make_season(year))
			edf = pd.read_sql_query('''SELECT Game_ID, Game_Home, Game_Away, Game_Date FROM espn WHERE Season = ?''',db,params=(year,))
			items = insert_games(season_df,edf,year)
			cur.executemany('''INSERT INTO vegas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', items)
		db.commit()


def transfer_to_db():
	with sqlite3.connect(h.database) as db:
		cur = db.cursor()
		create_table(cur)
		for year in h.all_years:
			json_path = os.path.join(h.data_path,'vi','{}.json'.format(year))
			df = pd.read_json(json_path, convert_dates=False)
			edf = pd.read_sql_query('''SELECT Game_ID, Game_Home, Game_Away, Game_Date FROM espn WHERE Season = ?''',db,params=(year,))
			items = insert_games(df,edf,year)
			cur.executemany('''INSERT INTO vegas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', items)
		db.commit()


if __name__ == '__main__':
	'''
	year = 2018
	data = get_data(year=year)
	json_path = os.path.join(my_path,'..','..','data','vi','{}.json'.format(year))
	with open(json_path,'w') as infile:
		json.dump(data,infile)
	'''
	# data = get_data(get_today = True)
	# with open('vegas_today.json', 'w') as outfile:
	# 	json.dump(data, outfile)
	# print("Updated vegas info for today")
