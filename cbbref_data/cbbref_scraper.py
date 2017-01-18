import urllib.request as request
import urllib.error as error
from bs4 import BeautifulSoup, Comment, Tag, NavigableString
from fake_useragent import UserAgent
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import sys
import json

ua = UserAgent()

def get_soup(url):
	try:
		page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
	except error.HTTPError as e:
		try:
			wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
			time.sleep(wait_time)
			print("First attempt for %s failed. Trying again." % (d))
			page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
		except:
			print(e)
			return None
	content = page.read()
	return BeautifulSoup(content, "html5lib")

def make_season(start_year=2016):
	months = ['11', '12', '01', '02', '03', '04']
	dates = {'11': list(range(31)[1:]), '12': list(range(32)[1:]),
			'01': list(range(32)[1:]), '02': list(range(29)[1:]),
			'03': list(range(32)[1:]), '04': list(range(9)[1:])}
	all_season = []
	for month in months:
		if month in ['01', '02', '03', '04']:
			year = start_year + 1
			if year % 4 == 0:
				dates['02'].append(29)
		else:
			year = start_year
		for d in dates[month]:
			day = str(d)
			if len(day) == 1:
				day = '0'+day
			all_season.append("{}-{}-{}".format(str(year),month,day))
	return all_season

def get_team_links(soup, year):
	links = []
	for school in soup.find('table', {'id': 'schools'}).tbody.contents[1::2]:
		if school.find('tr', {'class': 'thead'}) is not None:
			continue
		school_attrs = school.contents
		if school_attrs[4].string in "2017" and int(school_attrs[3].string)<=year:
			links.append(school_attrs[1].a['href'])
	return links

def get_games_statistics(game_log_soup, year):
	info = ['team','opponent','team_score','opp_score','date','OT',
			'neutral', 'home_game', 'ORtg','DRtg','Pace','FTr','3PAr','TS%',
			'TRB%','AST%','STL%','BLK%','eFG%','TOV%','ORB%','FT/FGA',
			'Opp-eFG%','Opp-TOV%','Opp-ORB%','Opp-FT/FGA']
	team_name = game_log_soup.find('li', {'class': 'index '}).a.string.split(' School')[0]
	print(team_name)
	rows = []
	game_rows = game_log_soup.find('table', {'id': 'sgl-advanced'}).tbody.contents
	for row in game_rows:
		if isinstance(row,NavigableString) or 'Offensive Four Factors' in row.text or 'Date' in row.text:
			continue
		data = np.array([np.arange(len(info))])
		game_df = pd.DataFrame(data, columns=info)
		data = row.contents
		game_df['team']=team_name
		game_df['opponent']=data[3].text
		game_df['team_score']=data[5].text
		game_df['opp_score']=data[6].text
		game_df['date']=data[1].text
		game_df['neutral'] = True if data[2].text == 'N' else False
		game_df['road_game'] = True if data[2].text == '@' else False
		game_df['ORtg']=data[7].text
		game_df['DRtg']=data[8].text
		game_df['Pace']=data[9].text
		game_df['FTr']=data[10].text
		game_df['tPAr']=data[11].text
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
	return pd.concat(rows,ignore_index=True)

def get_games(year=2017):
	soup = get_soup("http://www.sports-reference.com/cbb/schools/")

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
	all_teams_df = pd.concat(all_team_logs,ignore_index=True)
	all_teams_df.to_csv("game_info{}.csv".format(year), index=False)

if __name__ == '__main__':
	get_games(year=2012)
