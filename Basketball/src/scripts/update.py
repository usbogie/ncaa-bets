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

def espn_today():
	print("Getting today's ESPN data...")
	today_data = espn.get_tonight_info()
	if not today_data.empty:
		today_data = today_data.drop_duplicates()
	today_path = os.path.join(data_path,'today','espn.csv')
	today_data.to_csv(today_path, index_label='Game_ID')
	print("Got today's ESPN data\n")
	return today_data


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


def vegas_today(espn_data):
	print("Getting today's Vegas data...")
	today = str(date.today())
	tomorrow = str(date.today() + timedelta(1))
	data = vi.get_data(days=[today, tomorrow])
	# Fix up swtiched vi/espn info
	for index, row in espn_data.iterrows():
		if not row.Neutral_Site:
			continue

		espn_away = row.Game_Away
		espn_home = row.Game_Home
		for game in data:
			if espn_away == game['home'] and espn_home == game['away']:
				vi_home = game['home']
				game['home'] = game['away']
				game['away'] = vi_home

				vi_home_ats = game['home_ats']
				game['home_ats'] = game['away_ats']
				game['away_ats'] = vi_home_ats

				vi_home_pct = game['home_side_pct']
				game['home_side_pct'] = game['away_side_pct']
				game['away_side_pct'] = vi_home_pct

				game['open_line'] = game['open_line'] * -1
				game['close_line'] = game['close_line'] * -1

	vi_path = os.path.join(data_path,'today','vegas.csv')
	vidf = pd.DataFrame(data)
	vidf.to_csv(vi_path)
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
	for game in game_list:
		if game['date'] != days[0] or (not game['home'] in homes and not game['away'] in homes):
			#print(game)
			games_to_add.append(game)
	if games_to_add:
		vi.insert_games(db, cur, pd.DataFrame(games_to_add), year)
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
	espn_data = espn_today()
	vegas_today(espn_data)
	if not today_only:
		with sqlite3.connect(h.database) as db:
			cur = db.cursor()
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
