from scrapers import espn_daily_scraper as espn
from scrapers import vegas_scraper as vi
from scrapers import cbbref_scraper as cbbref
from datetime import datetime, timedelta
import pandas as pd
import json
import sys
import os

this_season = datetime.now().year + 1 if datetime.now().month > 4 else datetime.now().year

if __name__ == '__main__':
	my_path = os.path.dirname(os.path.abspath(__file__))

	try:
		update_lines_only = sys.argv[1]
	except:
		update_lines_only = False

	today_data = espn.get_tonight_info()
	if not today_data.empty:
		today_data = today_data.drop_duplicates()

	if not update_lines_only:
		last_night = espn.update_espn_data()
		csv_path = os.path.join(my_path,'..','data','espn','{}.csv'.format(this_season))
		cur_season = pd.read_csv(csv_path, index_col='Game_ID')
		cur_season_indices = [str(idx) for idx in list(cur_season.index.values)]
		for index, row in last_night.iterrows():
			if index not in cur_season_indices:
				cur_season = cur_season.append(row)
		cur_season = cur_season[~cur_season.index.duplicated(keep='first')]
		cur_season.to_csv(csv_path, index_label='Game_ID')

		today_path = os.path.join(my_path,'..','data','espn','upcoming_games.csv')
		today_data.to_csv(today_path, index_label='Game_ID')
		print("Updated ESPN Data")

		# get yesterday's vegas_insider info
		vi_path = os.path.join(my_path,'..','data','vi','{}.json'.format(this_season))
		with open(vi_path, 'r+') as vegasfile:
			gamelines = json.load(vegasfile)
			yesterday_games = vi.get_data(data=gamelines, get_yesterday=True)
			vegasfile.seek(0)
			vegasfile.truncate()
			json.dump(yesterday_games, vegasfile)
		print("Updated Yesterday Vegas Insider")

		cur_season = cbbref.get_games(year=this_season)
		cbbref_path = os.path.join(my_path,'..','data','cbbref','{}.csv'.format(this_season))
		cur_season.to_csv(cbbref_path, index=False)
		print("Updated cbbref")

	data = vi.get_data(get_today = True)

	# Fix up swtiched vi/espn info
	for index, row in today_data.iterrows():
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

	vi_path = os.path.join(my_path,'..','data','vi','vegas_today.json')
	with open(vi_path, 'w') as outfile:
		json.dump(data, outfile)
	print("Updated Vegas info for today")
