from scrapers import espn_scraper as espn
from scrapers import vegas_scraper as vi
from scrapers import cbbref_scraper as cbbref
from scrapers import shared
from datetime import datetime, timedelta, date
import pandas as pd
import json
import sys
import os
import helpers as h
import sqlite3

this_season = h.this_season
data_path = h.data_path
teams_path = os.path.join(data_path,'teams_to_update.json')

def espn_today(cur):
	print("Getting today's ESPN data...")
	cur.execute('''DROP TABLE IF EXISTS espn_today''')
	cur.execute('''CREATE TABLE espn_today (Game_ID INTEGER PRIMARY KEY, Away_Abbrv TEXT,
		Home_Abbrv TEXT, Game_Away TEXT, Game_Home TEXT, Season TEXT, Game_Date TEXT,
		Game_Tipoff TEXT, Neutral_Site TEXT)''')
	info = ['Game_ID', 'Away_Abbrv', 'Home_Abbrv', 'Game_Away', 'Game_Home','Season',
		'Game_Date','Game_Tipoff', 'Neutral_Site']
	today_data = espn.get_tonight_info()
	if not today_data.empty:
		today_data = today_data.drop_duplicates().reset_index(drop=True)
	items = []
	for index, row in today_data.iterrows():
		values = [int(index) if var == 'Game_ID'
				  else shared.get_date_str(row['Season'],row[var]) if var == 'Game_Date'
		   		  else row[var] for var in info]
		items.append(tuple(values))
	cur.executemany('''INSERT INTO espn_today VALUES (?,?,?,?,?,?,?,?,?)''', items)
	print("Got today's ESPN data\n")


def update_espn(db, cur):
	print("Catching ESPN up to today...")
	df = pd.read_sql_query('''SELECT * FROM espn WHERE Season = ?''', db, params = (str(this_season), ))
	homes = []
	prev_day = date.today() - timedelta(1)
	days = [prev_day]
	season_days = shared.make_season(this_season)
	while not df.empty or str(prev_day) in season_days:
		day_df = df.ix[df['Game_Date']==str(prev_day)][['Game_Home','Home_Score','Away_Score']].set_index('Game_Home')
		if len(day_df.index):
			break
		prev_day -= timedelta(1)
		days = [str(prev_day)] + days
	teams = set()
	all_dfs = []
	for day in days:
		last_night_list = espn.update_espn_data(str(day))
		if day == days[0]:
			last_night_list = pd.concat(last_night_list, ignore_index=True)
			for index, ldf in last_night_list.iterrows():
				if not ldf['Game_Home'] in day_df.index:
					all_dfs.append(ldf)
				else:
					row = day_df.loc[ldf['Game_Home']]
					if row['Home_Score'] != ldf['Home_Score'] or row['Away_Score'] != ldf['Away_Score']:
						print("{} vs {} on {} had score of {}-{} in database, updating to {}-{}".format(
							ldf['Away_Abbrv'], ldf['Home_Abbrv'], ldf['Game_Date'], row['Away_Score'], row['Home_Score'],
							ldf['Away_Score'],ldf['Home_Score']))
						row['Home_Score'] = ldf['Home_Score']
						row['Away_Score'] = ldf['Away_Score']
						all_dfs.append(row)
		else:
			all_dfs += last_night_list
	if all_dfs:
		new_df = pd.DataFrame(all_dfs) if len(all_dfs) == 1 else pd.concat(all_dfs, ignore_index=True)
		espn.insert_games(cur, new_df, max(df['Game_ID'].tolist()) + 1)
		teams = list(set(new_df['Game_Home'].tolist() + new_df['Game_Away'].tolist()))
		try:
			with open(teams_path, 'r+') as file:
				old_teams = json.load(file)
				file.seek(0)
				teams = list(set(teams + old_teams))
				json.dump(teams, file)
				file.truncate()
		except FileNotFoundError:
			print("No file: {}", teams_path)
			print("Creating a new file with the teams that need updating...")
			with open(teams_path, 'w') as file:
				json.dump(teams, file)
		print("Updated ESPN Data\n")
	else:
		print("ESPN already up-to-date.\n")


def vegas_today(db,cur):
	print("Getting today's Vegas data...")
	cur.execute('''DROP TABLE IF EXISTS vegas_today''')
	cur.execute('''CREATE TABLE vegas_today (home TEXT, away TEXT, 
		open_line REAL, close_line REAL, date TEXT, season TEXT,
		home_ats TEXT, away_ats TEXT, over_under TEXT, over_pct TEXT, 
		home_side_pct TEXT, away_side_pct TEXT, Game_ID INTEGER,
		FOREIGN KEY (Game_ID) REFERENCES espn(Game_ID))''')
	espn_data = pd.read_sql_query('''SELECT * FROM espn_today''',db)
	today = str(date.today())
	tomorrow = str(date.today() + timedelta(1))
	data = vi.get_data(days=[today, tomorrow])
	items = vi.insert_games(data,espn_data,h.this_season)
	cur.executemany('''INSERT INTO vegas_today VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', items)
	print("Updated Vegas Insider for today\n")


def update_vegas(db,cur,year):
	print("Catching Vegas up to today...")
	df = pd.read_sql_query('''SELECT home, away, date FROM vegas WHERE season = ?''', db, params = (str(year), ))
	homes = []
	prev_day = date.today() - timedelta(1)
	days = [str(prev_day)]
	season_days = shared.make_season(year)
	while not df.empty or str(prev_day) in season_days:
		homes = df.ix[df['date']==str(prev_day)]['home'].tolist()
		if homes:
			break
		prev_day -= timedelta(1)
		days = [str(prev_day)] + days
	games_to_add = []
	game_list = vi.get_data(days=days)
	for i, game in game_list.iterrows():
		if game['date'] != days[0] or (not game['home'] in homes and not game['away'] in homes):
			#print(game)
			games_to_add.append(game)
	if games_to_add:
		edf = pd.read_sql_query('''SELECT Game_ID, Game_Home, Game_Away, Game_Date FROM espn WHERE Season = ?''',db,params=(year,))
		items = vi.insert_games(pd.DataFrame(games_to_add), edf, year)
		cur.executemany('''INSERT INTO vegas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', items)
		print("Updated Vegas Data\n")
	else:
		print("Vegas Data already up-to-date.\n")


def update_cbbref(db,cur,year,get_all=False):
	print("Catching CBBRef up to today...")
	df = pd.read_sql_query('''SELECT team, opponent, date FROM cbbref WHERE season = ?''', db, params = (str(year), ))
	with open(teams_path, 'r+') as file:
		teams = json.load(file)
		if teams or get_all:
			cur_season = cbbref.get_games(this_season, teams, get_all)
			games_to_add = []
			for team_df in cur_season:
				team = team_df['team'].ix[0]
				old_count = len(df.ix[df['team'] == team].index)
				new_count = len(team_df.index) - old_count
				if new_count > 0:
					try:
						teams.remove(team)
					except Exception as e:
						if not get_all:
							raise e
					games_to_add.append(team_df.tail(new_count))
			if games_to_add:
				cbbref.insert_games(db,cur,pd.concat(games_to_add, ignore_index=True),year)
			print("Updated cbbref\n")
			file.seek(0)
			json.dump(teams,file)
			file.truncate()
		else:
			print("CBBRef already up-to-date.\n")


def run(today_only=False):
	with sqlite3.connect(h.database) as db:
		cur = db.cursor()
		espn_data = espn_today(cur)
		vegas_today(db,cur)
		if not today_only:	
			update_espn(db,cur)
			update_vegas(db,cur,this_season)
			update_cbbref(db,cur,this_season)
			db.commit()


def rescrape(year_list=h.all_years,espn=True,vi=True,cbbref=True):
	if espn:
		espn.rescrape(year_list)
	if vi:
		vi.rescrape(year_list)
	if cbbref:
		cbbref.rescrape(year_list)


def transfer_to_db():
	#espn.transfer_to_db()
	cbbref.transfer_to_db()
	vi.transfer_to_db()
