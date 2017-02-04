import pandas as pd
import numpy as np
import json
import csv
import math
import sys
from datetime import datetime, timedelta


def create_games_with_espn():
	espn_years = []
	for year in range(2012,2018):
		espn_years.append(pd.read_csv('espn_data/game_info{}.csv'.format(year)))
	all_espn = pd.concat(espn_years, ignore_index=True)
	all_games = {}
	for idx, game in all_espn.iterrows():
		game_date = "{}-{}-{}".format(game.Game_Year,game.Game_Date.split('/')[0], game.Game_Date.split('/')[1])
		game_key = (game.Game_Away, game.Game_Home, game_date)
		game_dict = {}
		hour = int(game.Game_Tipoff.split(":")[0])
		central = hour-1 if hour != 0 else 23
		game_dict["tipstring"] = "{}:{} CT".format(central, game.Game_Tipoff.split(":")[1])
		game_dict["date"] = game_date
		game_dict["score_home"] = game.Home_Score
		game_dict["score_away"] = game.Away_Score
		game_dict["margin_home"] = game.Home_Score - game.Away_Score
		game_dict["home_winner"] = 1 if game_dict["margin_home"] > 0 else 0

		game_dict['true_home_game'] = int(not game.Neutral_Site)
		game_dict['conference_competition'] = int(game.Conference_Competition)
		game_dict['away_games_played'] = game.Away_Games_Played
		game_dict['home_games_played'] = game.Home_Games_Played

		all_games[str(game_key)] = game_dict
	return all_games

def add_spread_information(all_games):
	vegas_years = []
	for year in range(2012,2018):
		vegas_years.append(pd.read_json('vi_data/vegas_{}.json'.format(year), convert_dates=False))

	all_vegas = pd.concat(vegas_years, ignore_index=True)

	temp_date = None
	date_vegas = None
	keys_to_remove = []

	for game_key, game in all_games.items():
		elements = [element[1:-1] for element in game_key[1:-1].split(', ')]
		away = elements[0]
		home = elements[1]
		date = elements[2]

		if date != temp_date:
			temp_date = date
			vegas_date = all_vegas.ix[all_vegas['date'] == date]

		vegas_game = vegas_date.ix[(vegas_date['away']==away) & (vegas_date['home']==home)]

		switched = False
		if len(vegas_game.index)==0:
			vegas_game = vegas_date.ix[(vegas_date['away']==home) & (vegas_date['home']==away)]
			if len(vegas_game.index)==0:
				keys_to_remove.append(game_key)
				continue
			else:
				switched = True


		if len(vegas_game.index)>1:
			vegas_game=vegas_game.iloc[0]

		try:
			game['spread'] = vegas_game.iloc[0]['close_line']
			away_team = vegas_game.iloc[0]['away']
			home_team = vegas_game.iloc[0]['home']
			open_line = vegas_game.iloc[0]['open_line']
		except:
			game['spread'] = vegas_game['close_line']
			away_team = vegas_game['away']
			home_team = vegas_game['home']
			open_line = vegas_game['open_line']

		if switched:
			tmp = away_team
			away_team = home_team
			home_team = tmp

		if not isinstance(game['spread'], float) and not isinstance(game['spread'], int):
			keys_to_remove.append(game_key)
			print("continuing {} @ {} on {}".format(away,home,date))
			continue

		if game['spread'] + game['margin_home'] < 0:
			game['cover_team'] = away_team
			game['home_cover'] = -1
		elif game['spread'] + game['margin_home'] > 0:
			game['cover_team'] = home_team
			game['home_cover'] = 1
		else:
			game['cover_team'] = 'Push'
			game['home_cover'] = 0
		try:
			game['line_movement'] = 0 if open_line == "" else game['spread'] - open_line
		except:
			game['line_movement'] = None
		try:
			game["home_public_percentage"] = 50 if vegas_game.iloc[0]['home_side_pct'] == "" or vegas_game.iloc[0]['home_side_pct'] == "n/a" else vegas_game.iloc[0]['home_side_pct']
			game['ats_home'] = vegas_game.iloc[0]['home_ats'].split("-")
			game['ats_away'] = vegas_game.iloc[0]['away_ats'].split("-")
		except:
			game["home_public_percentage"] = 50 if vegas_game['home_side_pct'] == "" or vegas_game['home_side_pct'] == "n/a" else vegas_game['home_side_pct']
			game['ats_home'] = vegas_game['home_ats'].split("-")
			game['ats_away'] = vegas_game['away_ats'].split("-")
		game['ats_home'] = 0 if game['ats_home'][0] == "0" and game['ats_home'][1] == "0" else int(game['ats_home'][0]) / (int(game['ats_home'][0])+int(game['ats_home'][1]))
		game['ats_away'] = 0 if game['ats_away'][0] == "0" and game['ats_away'][1] == "0" else int(game['ats_away'][0]) / (int(game['ats_away'][0])+int(game['ats_away'][1]))
		if math.isnan(game['spread']):
			print("Found spread nan that wasn't \"\"")
			continue
	for key in keys_to_remove:
		all_games.pop(key)
	return all_games

def add_prior_team_splits(all_games):
	tr_split_years = []
	tr_stat_years = []
	cbbref_years = []
	for year in range(2012,2018):
		tr_split_years.append(pd.read_csv('tr_data/xeff_splits{}.csv'.format(year)))
		tr_stat_years.append(pd.read_csv('tr_data/xteam_stats{}.csv'.format(year)))
		cbbref_years.append(pd.read_csv('cbbref_data/game_info{}.csv'.format(year)))

	tr_splits = pd.concat(tr_split_years, ignore_index=True)
	tr_stats = pd.concat(tr_stat_years, ignore_index=True)
	all_cbbref = pd.concat(cbbref_years, ignore_index=True)


	keys_to_remove = []

	temp_date = None
	date_splits = None
	date_stats = None
	date_cbbref = None

	for game_key, game in all_games.items():
		elements = [element[1:-1] for element in game_key[1:-1].split(', ')]
		away = elements[0]
		home = elements[1]
		date = elements[2]

		if date != temp_date:
			temp_date = date
			date_splits = tr_splits.ix[tr_splits['date'] == date]
			date_stats = tr_stats.ix[tr_stats['date'] == date]
			date_cbbref = all_cbbref.ix[all_cbbref['date'] == date]

		away_team_split = date_splits.ix[date_splits['Name']==away]
		away_team_stats = date_stats.ix[date_stats['Name']==away]
		away_team_cbbref = date_cbbref.ix[date_cbbref['team']==away]

		home_team_split = date_splits.ix[date_splits['Name']==home]
		home_team_stats = date_stats.ix[date_stats['Name']==home]
		home_team_cbbref = date_cbbref.ix[date_cbbref['team']==home]

		if away_team_split.isnull().values.any():
			print(away_team_split)
		if away_team_stats.isnull().values.any():
			print(away_team_stats)
		if home_team_split.isnull().values.any():
			print(home_team_split)
		if home_team_stats.isnull().values.any():
			print(home_team_stats)

		if len(away_team_cbbref.index)==0 or len(home_team_cbbref.index)==0:
			# game happens really late at night, try previous day.
			tomorrow_date = (datetime.strptime(date,'%Y-%m-%d')+timedelta(1)).strftime('%Y-%m-%d')
			home_team_cbbref = all_cbbref.ix[(all_cbbref['date'] == tomorrow_date) & (all_cbbref['team'] == home)]
			away_team_cbbref = all_cbbref.ix[(all_cbbref['date'] == tomorrow_date) & (all_cbbref['team'] == away)]
			print(away_team_cbbref.to_string())
			print(home_team_cbbref.to_string())
			if len(away_team_cbbref.index) > 1:
				away_team_cbbref = away_team_cbbref.iloc[1:2]
			if len(home_team_cbbref.index) > 1:
				home_team_cbbref = home_team_cbbref.iloc[1:2]
			try:
				home_team_cbbref.iloc[0, home_team_cbbref.columns.get_loc('date')] = date
				away_team_cbbref.iloc[0, away_team_cbbref.columns.get_loc('date')] = date
			except:
				print(away_team_cbbref.to_string())
				print(home_team_cbbref.to_string())
				print(game_key)
				sys.exit()
			print(away_team_cbbref.to_string())
			print(home_team_cbbref.to_string())


		if len(away_team_split.index)==0 or len(home_team_split.index)==0 or len(away_team_stats.index)==0 or len(home_team_stats.index)==0 or len(away_team_cbbref.index)==0 or len(home_team_cbbref.index)==0:
			print(len(away_team_split.index))
			print(len(away_team_stats.index))
			print(len(away_team_cbbref.index))
			print(len(home_team_split.index))
			print(len(home_team_stats.index))
			print(len(home_team_cbbref.index))
			keys_to_remove.append(game_key)
			print('continuing ' + game_key)
			continue

		if str(away_team_stats.iloc[0][1]) != date or \
		   str(home_team_cbbref.iloc[0][4]) != date:
			print("SOMETHING WRONG")
			print(game_key)
			print(date)
			print(away_team_stats)
			print(home_team_cbbref)
			continue

		if len(away_team_split.index) > 1:
			away_team_split = away_team_split.iloc[0]
		if len(home_team_split.index) > 1:
			home_team_split = home_team_split.iloc[0]
		if len(away_team_stats.index) > 1:
			away_team_stats = away_team_stats.iloc[0]
		if len(home_team_stats.index) > 1:
			home_team_stats = home_team_stats.iloc[0]
		if len(away_team_cbbref.index) > 1:
			away_team_cbbref = away_team_cbbref.iloc[0]
		if len(home_team_cbbref.index) > 1:
			home_team_cbbref = home_team_cbbref.iloc[0]

		split_indices = ['ORTG','ORTGlast3','ORTGprevSeason','DRTG','DRTGlast3','DRTGprevSeason']

		stat_indices = ['FTO','FTOlast3','FTOprevSeason','FTD','FTDlast3','FTDprevSeason',
						'Three_O','Three_Olast3','Three_OprevSeason','Three_D','Three_Dlast3',
						'Three_DprevSeason','REBO','REBOlast3','REBOprevSeason','REBD',
						'REBDlast3','REBDprevSeason','REB','REBlast3','REBprevSeason',
						'TOP','TOPlast3','TOPprevSeason','TOFP','TOFPlast3',
						'TOFPprevSeason','POSS','POSSlast3','POSSprevSeason']

		cbbref_indices = ['ORtg','DRtg','Pace','FTr','3PAr','TSP','TRBP',
						'ASTP','STLP','BLKP','eFGP','TOVP','ORBP','FT']

		for stat in split_indices:
			game["away_"+stat] = float(away_team_split[stat])
			game["home_"+stat] = float(home_team_split[stat])
		for stat in stat_indices:
			game["away_"+stat] = float(away_team_stats[stat])
			game["home_"+stat] = float(home_team_stats[stat])
		for stat in cbbref_indices:
			game["result_away_"+stat] = float(away_team_cbbref[stat])
			game["result_home_"+stat] = float(home_team_cbbref[stat])

	for key in keys_to_remove:
		all_games.pop(key)

	return all_games


def main():
	all_games = create_games_with_espn()
	print("Got ESPN data")
	all_games = add_spread_information(all_games)
	print("Got Vegas Info")
	print(json.dumps(all_games, indent=2))
	all_games = add_prior_team_splits(all_games)
	print("Got team ranks info")

	all_games_list = []
	for key, game in all_games.items():
		elements = [element[1:-1] for element in key[1:-1].split(', ')]
		game['team_away'] = elements[0]
		game['team_home'] = elements[1]
		all_games_list.append(game)

	print(json.dumps(all_games_list, indent=2))

	with open('incremental_data.csv','w') as outfile:
		keys = list(all_games_list[0].keys())
		#removing and re-adding the keys is for the sake of readability of the csv files
		front_keys = ['date','tipstring','team_away','team_home','true_home_game','score_away','score_home','home_winner',
					'spread','margin_home','cover_team','home_cover']
		for key in front_keys:
			keys.remove(key)
		keys = front_keys + keys
		writer = csv.DictWriter(outfile,fieldnames=keys)
		writer.writeheader()
		for game in all_games_list:
			writer.writerow(game)

if __name__ == '__main__':
	main()
