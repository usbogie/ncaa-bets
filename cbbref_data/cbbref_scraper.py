import urllib.request as request
import urllib.error as error
from bs4 import BeautifulSoup, Comment, Tag
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
			sys.exit()
	content = page.read()
	return BeautifulSoup(content, "html5lib")

def make_season(start_year=2016):
	months = ['11', '12', '01', '02', '03', '04']
	dates ={'11': list(range(31)[1:]), '12': list(range(32)[1:]),
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

def get_team_links(soup):
	links = []
	for school in soup.find('table', {'id': 'schools'}).tbody.contents[1::2]:
		if school.find('tr', {'class': 'thead'}) is not None:
			continue
		school_attrs = school.contents
		if school_attrs[4].string in "2017":
			links.append(school_attrs[1].a['href'])
	return links

def get_games_statistics(game_log_soup):
	info = ['team','opponent','team_score','opp_score','date','OT',
			'neutral', 'home_game', 'ORtg','DRtg','Pace','FTr','3PAr','TS%',
			'TRB%','AST%','STL%','BLK%','eFG%','TOV%','ORB%','FT/FGA',
			'Opp-eFG%','Opp-TOV%','Opp-ORB%','Opp-FT/FGA']
	team_name = game_log_soup.find('li', {'class': 'index '}).a.string.split(' School')[0]
	print(team_name)
	rows = []
	for row in game_log_soup.find('table', {'id': 'sgl-advanced'}).tbody.contents[1::2]:
		if row.find('tr',{'class':'over_header thead'}) or row.find('tr',{'class':'thead'}):
			continue
		data = np.array([np.arange(len(info))])
		game_df = pd.DataFrame(data, columns=info)
		data = row.contents
		game_df['team']=team_name
		game_df['opponent']=data[3].a.text
		game_df['team_score']=data[5].text
		game_df['opp_score']=data[6].text
		game_df['date']=data[1].a.text
		game_df['neutral'] = True if data[2].text == 'N' else False
		game_df['home_game'] = False if data[2].text == '@' else True
		game_df['ORtg']=data[7].text
		game_df['DRtg']=data[8].text
		game_df['Pace']=data[9].text
		game_df['FTr']=data[10].text
		game_df['3PAr']=data[11].text
		game_df['TS%']=data[12].text
		game_df['TRB%']=data[13].text
		game_df['AST%']=data[14].text
		game_df['STL%']=data[15].text
		game_df['BLK%']=data[16].text
		game_df['eFG%']=data[18].text
		game_df['TOV%']=data[19].text
		game_df['ORB%']=data[20].text
		game_df['FT/FGA']=data[21].text
		game_df['Opp-eFG%']=data[23].text
		game_df['Opp-TOV%']=data[24].text
		game_df['Opp-ORB%']=data[25].text
		game_df['Opp-FT/FGA']=data[26].text

		result = data[4].text
		if len(result) > 1:
			game_df['OT'] = result[3]
		else:
			game_df['OT'] = 0

		rows.append(game_df)
	return pd.concat(rows,ignore_index=True)

def get_games(year=2017):
	soup = get_soup("http://www.sports-reference.com/cbb/schools/")

	links = get_team_links(soup)
	base = 'http://www.sports-reference.com'

	all_team_logs = []
	for link in links:
		game_log_url = base+link+"{}-gamelogs-advanced.html".format(year)
		game_log_soup = get_soup(game_log_url)
		team_info = get_games_statistics(game_log_soup)
		all_team_logs.append(team_info)
	all_teams_df = pd.concat(all_team_logs,ignore_index=True)
	all_teams_df.to_csv("game_info{}.csv".format(year))
get_games()
