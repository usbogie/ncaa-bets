from bs4 import NavigableString
import pandas as pd
import numpy as np
import sys
import json
import os
from helpers import get_soup

my_path = os.path.dirname(os.path.abspath(__file__))
names_path = os.path.join(my_path,'..','names.json')

with open(names_path,'r') as infile:
	names_dict = json.load(infile)

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
	info = ['team','opponent','team_score','opp_score','date','OT',
			'neutral', 'road_game', 'ORtg','DRtg','Pace','FTr','3PAr','TSP',
			'TRBP','ASTP','STLP','BLKP','eFGP','TOVP','ORBP','FT',
			'OeFGP','OTOVP','OORBP','OFT']
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
		data = np.array([np.arange(len(info))])
		game_df = pd.DataFrame(data, columns=info)
		data = row.contents
		game_df['team']=team_name
		try:
			game_df['opponent']=names_dict[data[3].text]
		except KeyError as e:
			continue
		game_df['team_score']=data[5].text
		game_df['opp_score']=data[6].text
		game_df['date']=data[1].text
		game_df['neutral'] = True if data[2].text == 'N' else False
		game_df['road_game'] = True if data[2].text == '@' else False
		game_df['ORtg']=data[7].text
		game_df['DRtg']=data[8].text
		game_df['Pace']=data[9].text
		game_df['FTr']=data[10].text
		game_df['3PAr']=data[11].text
		game_df['TSP']=data[12].text
		game_df['TRBP']=data[13].text
		game_df['ASTP']=data[14].text
		game_df['STLP']=data[15].text
		game_df['BLKP']=data[16].text
		game_df['eFGP']=data[18].text
		game_df['TOVP']=data[19].text
		game_df['ORBP']=data[20].text
		game_df['FT']=data[21].text
		game_df['OeFGP']=data[23].text
		game_df['OTOVP']=data[24].text
		game_df['OORBP']=data[25].text
		game_df['OFT']=data[26].text

		result = data[4].text
		if len(result) > 1:
			game_df['OT'] = result[3]
		else:
			game_df['OT'] = 0

		rows.append(game_df)
	try:
		df = pd.concat(rows, ignore_index=True)
	except:
		df = pd.DataFrame()
	return df

def get_games(year=2017):
	url = "http://www.sports-reference.com/cbb/schools/"
	soup = get_soup(url)

	links = get_team_links(soup, year)
	base = 'http://www.sports-reference.com'

	all_team_logs = []
	for link in links:
		game_log_url = base+link+"{}-gamelogs-advanced.html".format(year)
		game_log_soup = get_soup(game_log_url)
		if game_log_soup is None:
			continue
		team_info = get_games_statistics(game_log_soup, year)
		all_team_logs.append(team_info)
	try:
		all_teams_df = pd.concat(all_team_logs,ignore_index=True)
	except:
		all_teams_df = pd.DataFrame()
	return all_teams_df

if __name__ == '__main__':
	year = 2018
	cur_season = get_games(year=year)
	csv_path = os.path.join(my_path,'..','..','data','cbbref','{}.csv'.format(year))
	cur_season.to_csv(csv_path, index=False)
	print("Updated cbbref")
