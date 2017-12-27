from bs4 import NavigableString
import pandas as pd
import sys
import json
import os
from scrapers.shared import get_soup, get_season_year
from datetime import datetime, timedelta, date
import helpers as h
import sqlite3

my_path = h.path
names_dict = h.read_names()
info = ['team','opponent','team_score','opp_score','date','season','OT',
		'ORtg','DRtg','Pace','FTr','3PAr','TSP',
		'TRBP','ASTP','STLP','BLKP','eFGP','TOVP','ORBP','FT',
		'OeFGP','OTOVP','OORBP','OFT']

def get_team_links(soup, year):
	links = []
	for school in soup.find('table', {'id': 'schools'}).tbody.contents[1::2]:
		if school.find('tr', {'class': 'thead'}) is not None:
			continue
		school_attrs = school.contents
		if school_attrs[4].string in "2018" and int(school_attrs[3].string)<=year:
			links.append(school_attrs[1].a['href'])
	return links

def get_games_statistics(game_log_soup, year):
	team_name = names_dict[game_log_soup.find('li', {'class': 'index '}).a.string.split(' School')[0]]
	rows = []
	print(team_name)
	try:
		game_rows = game_log_soup.find('table', {'id': 'sgl-advanced'}).tbody.contents
	except:
		game_rows = []
	for row in game_rows:
		if isinstance(row,NavigableString) or 'Offensive Four Factors' in row.text or 'Date' in row.text:
			continue
		game_dict = {}
		data = row.contents
		game_dict['team']=team_name
		try:
			game_dict['opponent']=names_dict[data[3].text]
		except KeyError as e:
			continue
		game_dict['team_score']=data[5].text
		game_dict['opp_score']=data[6].text
		game_dict['date']=data[1].text
		game_dict['season']= get_season_year(game_dict['date'])
		game_dict['neutral'] = True if data[2].text == 'N' else False
		game_dict['road_game'] = True if data[2].text == '@' else False
		game_dict['ORtg']=data[7].text
		game_dict['DRtg']=data[8].text
		game_dict['Pace']=data[9].text
		game_dict['FTr']=data[10].text
		game_dict['3PAr']=data[11].text
		game_dict['TSP']=data[12].text
		game_dict['TRBP']=data[13].text
		game_dict['ASTP']=data[14].text
		game_dict['STLP']=data[15].text
		game_dict['BLKP']=data[16].text
		game_dict['eFGP']=data[18].text
		game_dict['TOVP']=data[19].text
		game_dict['ORBP']=data[20].text
		game_dict['FT']=data[21].text
		game_dict['OeFGP']=data[23].text
		game_dict['OTOVP']=data[24].text
		game_dict['OORBP']=data[25].text
		game_dict['OFT']=data[26].text

		result = data[4].text
		if len(result) > 1:
			game_dict['OT'] = result[3]
		else:
			game_dict['OT'] = 0

		rows.append(game_dict)
	return pd.DataFrame(rows)


def parse_link(link):
	names = link.split('/')[-2].split('-')
	name = []
	for lower in names:
		name += [lower[0].upper() + lower[1:]]
	name = " ".join(name)
	return name


def get_games(year, teams, get_all=False):
	url = "http://www.sports-reference.com/cbb/schools/"
	soup = get_soup(url)

	links = get_team_links(soup, year)
	base = 'http://www.sports-reference.com'

	team_logs = []
	for link in links:
		if not get_all and not names_dict[parse_link(link)] in teams:
			continue
		game_log_url = base+link+"{}-gamelogs-advanced.html".format(year)
		game_log_soup = get_soup(game_log_url)
		if game_log_soup is None:
			continue
		team_info = get_games_statistics(game_log_soup, year)
		team_logs.append(team_info)
	return team_logs


def insert_games(db,cur,df,year):
	items = []
	edf = pd.read_sql_query('''SELECT Game_ID, Game_Home, Game_Away, Game_Date FROM espn WHERE Season = ?''',db,params=(year,))
	i = 0
	for index, row in df.iterrows():
		matches = edf[(edf.Game_Home == row['team']) & (edf.Game_Away == row['opponent']) |
			(edf.Game_Home == row['opponent']) & (edf.Game_Away == row['team'])]
		key = -1
		for index2, match in matches.iterrows():
			if abs((datetime.strptime(row['date'], '%Y-%m-%d') - datetime.strptime(match['Game_Date'], '%Y-%m-%d')).days) <= 1:
				if key != -1:
					print("Found multiple results for {} vs {} on {}".format(row['opponent'],row['team'],row['date']))
					if row['date'] == match['Game_Date']:
						key = match['Game_ID']
				else:
					key = match['Game_ID']
		if key == -1:
			#print("Match not found in vi: {} vs {} on {}".format(row['team'],row['opponent'],row['date']))
			i += 1
		values = tuple([row[var] for var in info] + [key])
		items.append(values)
	print("Missed {}/{} games in {} in cb".format(i,len(df.index),year))
	cur.executemany('''INSERT INTO cbbref VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', items)


def create_table(cur):
	cur.execute('''DROP TABLE IF EXISTS cbbref''')
	cur.execute('''CREATE TABLE cbbref (team TEXT, opponent TEXT, team_score INTEGER, opp_score INTEGER,
	 	date TEXT, season TEXT, OT TEXT, ORtg REAL, DRtg REAL, Pace REAL, FTr REAL, tPAr REAL, TSP REAL,
		TRBP REAL, ASTP REAL, STLP REAL, BLKP REAL, eFGP REAL, TOVP REAL, ORBP REAL, FT REAL, OeFGP REAL,
		OTOVP REAL, OORBP REAL, OFT REAl, Game_ID INTEGER,
		FOREIGN KEY (Game_ID) REFERENCES espn(Game_ID))''')


def rescrape_all():
	with sqlite3.connect(h.database) as db:
		cur = db.cursor()
		create_table(cur)
		for year in range(h.first_season, h.this_season+1):
			final_info = get_games(year)
			season_df = pd.DataFrame(final_info)
			insert_games(db,cur,season_df,year)
		db.commit()


def transfer_to_db():
	with sqlite3.connect(h.database) as db:
		cur = db.cursor()
		create_table(cur)
		for year in range(h.first_season, h.this_season + 1):
			csv_path = os.path.join(h.data_path,'cbbref','{}.csv'.format(year))
			df = pd.read_csv(csv_path)
			insert_games(db,cur,df,year)
		db.commit()


if __name__ == '__main__':
	'''
	year = 2018
	cur_season = get_games(year=year)
	csv_path = os.path.join(my_path,'..','..','data','cbbref','{}.csv'.format(year))
	cur_season.to_csv(csv_path, index=False)
	print("Updated cbbref")
	'''
