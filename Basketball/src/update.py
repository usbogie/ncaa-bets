from Data.ESPN import espn_daily_scraper as espn
from Data.VI import vegas_scraper as vi
from Data.CBBRef import cbbref_scraper as cbbref
from datetime import datetime, timedelta
import pandas as pd
import json
import sys

if __name__ == '__main__':
	try:
		update_lines_only = sys.argv[1]
	except:
		update_lines_only = False

	data = vi.get_data(get_today = True)
	with open('Data/VI/vegas_today.json', 'w') as outfile:
		json.dump(data, outfile)
	print("Updated Vegas info for today")

	if not update_lines_only:
		last_night = espn.update_espn_data()
		cur_season = pd.read_csv('Data/ESPN/game_info2017.csv', index_col='Game_ID')
		cur_season_indices = [str(idx) for idx in list(cur_season.index.values)]
		for index, row in last_night.iterrows():
			if index not in cur_season_indices:
				cur_season = cur_season.append(row)
		cur_season = cur_season[~cur_season.index.duplicated(keep='first')]
		cur_season.to_csv('Data/ESPN/game_info2017.csv', index_label='Game_ID')

		today_data = espn.get_tonight_info()
		if not today_data.empty:
			today_data = today_data.drop_duplicates()
		today_data.to_csv('Data/ESPN/upcoming_games.csv', index_label='Game_ID')
		print("Updated ESPN Data")

		# get yesterday's vegas_insider info
		with open('Data/VI/vegas_2017.json', 'r+') as vegasfile:
			gamelines = json.load(vegasfile)
			yesterday_games = vi.get_data(data=gamelines, get_yesterday=True)
			vegasfile.seek(0)
			vegasfile.truncate()
			json.dump(yesterday_games, vegasfile)
		print("Updated Yesterday Vegas Insider")

		cur_season = cbbref.get_games(year=2017)
		cur_season.to_csv('Data/CBBRef/game_info2017.csv', index=False)
		print("Updated cbbref")

import Data.Betsy2