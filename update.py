from espn_data import espn_daily_scraper as espn
import pandas as pd
import numpy as np
from kp_data import kp_scraper as kp
from lines_data import lines_scraper as lines
from sb_data import sportsbook_scraper as sb
from tr_data import tr_scraper as tr
from datetime import datetime, timedelta
import json
import csv

last_night = espn.update_espn_data()
cur_season = pd.read_csv('espn_data/game_info2017.csv', index_col='Game_ID')
cur_season_indices = [int(idx) for idx in list(cur_season.index.values)]
for index, row in last_night.iterrows():
	if int(index) not in list(cur_season.index.values):
		cur_season.append(row)
cur_season = pd.concat([cur_season,last_night])
cur_season = cur_season[~cur_season.index.duplicated(keep='first')]
cur_season.to_csv('espn_data/game_info2017.csv', index_label='Game_ID')

today_data = espn.get_tonight_info()
today_data.drop_duplicates().to_csv('espn_data/upcoming_games.csv', index_label='Game_ID')
print("Updated ESPN Data")


teams = kp.extract_kenpom(2017)
with open('kp_data/kenpom17.json', 'w+') as outfile:
	json.dump(teams, outfile)
print("Updated KenPom")

with open('lines_data/lines2017.json', 'r+') as linesfile:
	gamelines = json.load(linesfile)
	d = lines.get_data(get_yesterday=True,data=gamelines)
	json.dump(d, linesfile)
print("Updated Game Lines")

games = sb.get_todays_sportsbook_lines()
with open('sb_data/game_lines.json','w') as outfile:
	json.dump(games,outfile)
print("Updated new lines")

team_list = tr.get_teamrankings([2017])
with open('tr_data/team_stats17.csv', 'w') as outfile:
	keys = list(team_list[0].keys())
	writer = csv.DictWriter(outfile,fieldnames=keys)
	writer.writeheader()
	for team in team_list:
		writer.writerow(team)
print("Updated team stats")
