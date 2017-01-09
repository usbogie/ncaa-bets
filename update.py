from espn_data import espn_daily_scraper as espn
import pandas as pd
import numpy as np
from kp_data import kp_scraper as kp
from lines_data import lines_scraper as lines
from sb_data import sportsbook_scraper as sb
from datetime import datetime, timedelta
import json

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

d = lines.get_data(get_yesterday=True)
with open('lines_data/lines2017.json', 'w+') as outfile:
	json.dump(d, outfile)
print("Updated Game Lines")

games = sb.get_todays_sportsbook_lines()
with open('sb_data/game_lines.json','w') as outfile:
	json.dump(games,outfile)
print("Updated new lines")
