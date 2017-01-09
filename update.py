from espn_data import espn_daily_scraper as espn
import pandas as pd
import numpy as np
from kp_data import kp_scraper as kp
from os_data import os_scraper as oddsshark
from sb_data import sportsbook_scraper as sb

last_night = espn.update_espn_data()
cur_season = pd.read_csv('espn_data/game_info2017.csv', index_col='Game_ID')
print(cur_season.index.values[0])
cur_season_indices = [int(idx) for idx in list(cur_season.index.values)]
for index, row in last_night.iterrows():
	if int(index) not in list(cur_season.index.values):
		cur_season.append(row)
cur_season = pd.concat([cur_season,last_night])
cur_season = cur_season[~cur_season.index.duplicated(keep='first')]
cur_season.to_csv('espn_data/game_info2017.csv', index_label='Game_ID')

today_data = espn.get_tonight_info()
today_data.drop_duplicates().to_csv('espn_data/upcoming_games.csv', index_label='Game_ID')

kp.extract_kenpom(2017)

links = []
names = []
for link,name in oddsshark.get_links():
    links.append(link)
    names.append(name)
for i in range(4):
	oddsshark.get_oddsshark(2017,links,names)
