from espn_data import espn_daily_scraper as espn
import pandas as pd
import numpy as np
from kp_data import kp_scraper as kp
from sb_data import sportsbook_scraper as sb
from tr_data import tr_scraper as tr
from vi_data import vegas_scraper as vi
from lines_data import lines_scraper as lines
from datetime import datetime, timedelta
import record_results
import json
import csv

games = sb.get_todays_sportsbook_lines()
with open('sb_data/game_lines.json','w') as outfile:
	json.dump(games,outfile)
print("Updated new lines for today")

data = vi.get_data(get_today = True)
with open('vi_data/vegas_today.json', 'w') as outfile:
	json.dump(data, outfile)
print("Updated vegas info for today")

already_run = False
if games[0]['date'][1:-1] == str(datetime.now().strftime('%B %d, %Y')):
	already_run = True

if not already_run:
	last_night = espn.update_espn_data()
	cur_season = pd.read_csv('espn_data/game_info2017.csv', index_col='Game_ID')
	cur_season_indices = [str(idx) for idx in list(cur_season.index.values)]
	for index, row in last_night.iterrows():
		if index not in cur_season_indices:
			cur_season.append(row)
	cur_season = cur_season[~cur_season.index.duplicated(keep='first')]
	cur_season.to_csv('espn_data/game_info2017.csv', index_label='Game_ID')

	today_data = espn.get_tonight_info()
	today_data.drop_duplicates().to_csv('espn_data/upcoming_games.csv', index_label='Game_ID')
	print("Updated ESPN Data")


	teams = kp.extract_kenpom(2017)
	with open('kp_data/kenpom17.json', 'w+') as outfile:
		json.dump(teams, outfile)
	print("Updated KenPom")

	all_lines = []
	with open('lines_data/lines2017.json', 'r+') as linesfile:
		gamelines = json.load(linesfile)
		all_lines = lines.get_data(gamelines, get_yesterday=True)
		linesfile.seek(0)
		linesfile.truncate()
		json.dump(all_lines, linesfile)
	print("Updated Past games lines")

	team_list = tr.get_teamrankings([2017])
	with open('tr_data/team_stats17.csv', 'w') as outfile:
		keys = list(team_list[0].keys())
		writer = csv.DictWriter(outfile,fieldnames=keys)
		writer.writeheader()
		for team in team_list:
			writer.writerow(team)
	print("Updated team stats")

	#get yesterday's vegas_insider info
	with open('vi_data/vegas_2017.json', 'r+') as vegasfile:
		gamelines = json.load(vegasfile)
		yesterday_games = vi.get_data(data=gamelines, get_yesterday=True)
		vegasfile.seek(0)
		vegasfile.truncate()
		json.dump(yesterday_games, vegasfile)
	print("Updated Vegas Insider")

	with open('results.json', 'r+') as resultsfile:
		past_results = json.load(resultsfile)
		print(past_results)
		results = record_results.add_yesterday(last_night,all_lines)
		total = past_results+results
		print(total)
		resultsfile.seek(0)
		resultsfile.truncate()
		json.dump(total, resultsfile)
	print("Updated record jsons")
