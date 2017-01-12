import urllib.request as request
import urllib.error as error
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime, timedelta, date
import sys
import re
import json

ua = UserAgent()

def make_season(start_year=2016):
	months = ['11', '12', '01', '02', '03', '04']

	dates = {'11': list(range(31)[1:]), '12': list(range(32)[1:]), '01': list(range(32)[1:]), '02': list(range(29)[1:]),
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

def ordered(obj):
	if isinstance(obj, dict):
		return sorted((k, ordered(v)) for k, v in obj.items())
	if isinstance(obj, list):
		return sorted(ordered(x) for x in obj)
	else:
		return obj

def get_data(data=[],get_yesterday=False,get_today=False, year=2017):
	all_dates = make_season(year-1)
	base = "http://www.vegasinsider.com/college-basketball/matchups/matchups.cfm/date/"
	today = int((datetime.now() - timedelta(1)).strftime('%Y-%m-%d').replace('-',''))
	if get_today:
		today = int((datetime.now()).strftime('%Y-%m-%d').replace('-',''))
		d = datetime.now()
		month = str(d.month) if d.month >= 10 else "0" + str(d.month)
		day = str(d.day) if d.day >= 10 else "0" + str(d.day)
		all_dates = ["{}-{}-{}".format(d.year,month,day)]
	for day in all_dates:
		if today < int(day.replace('-','')):
			continue
		if get_yesterday and today - int(day.replace('-','')) != 0:
			continue
		if get_today and today - int(day.replace('-','')) != 0:
			continue
		print (day)
		url_day = "-".join(day.split('-')[1:]+day.split('-')[:1])
		url = base+day

		try:
			page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
		except error.HTTPError as e:
			try:
				wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
				time.sleep(wait_time)
				print("First attempt for %s failed. Trying again." % (url))
				page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
			except:
				print(e)
				sys.exit()

		content = page.read()
		soup = BeautifulSoup(content, "html5lib")

		game_tables = soup.findAll('div', {'class': 'SLTables1'})
		if len(game_tables) == 0:
			print("No games, skipping day")

		for table in game_tables:
			game_info = {}
			info = table.find('td', {'class': 'viBodyBorderNorm'}).table.tbody.contents
			away_info = info[4].contents[1::2]
			home_info = info[6].contents[1::2]
			game_info['date'] = "/".join(day.split('-')[1:])

			try:
				game_info['away'] = away_info[0].find('a', {'class': 'tableText'}).text
				game_info['home'] = home_info[0].find('a', {'class': 'tableText'}).text
			except:
				continue

			game_info['away_ats'] = re.sub('\s+','',away_info[3].text)
			game_info['home_ats'] = re.sub('\s+','',home_info[3].text)
			favorite = 'away'
			if '-' in home_info[5].text:
				favorite = 'home'
			if favorite == 'away':
				game_info['open_line'] = re.sub('\s+','',away_info[4].text)
				game_info['close_line'] = re.sub('\s+','',away_info[5].text)
				game_info['over_under'] = re.sub('\s+','',home_info[5].text)
				if game_info['close_line'] == "":
					pass
				elif float(game_info['close_line']) > 0:
					game_info['close_line'] = ""
				else:
					game_info['close_line'] = abs(float(game_info['close_line']))
				if game_info['open_line'] == "":
					if '-' in home_info[4]:
						game_info['open_line'] = float(re.sub('\s+','',home_info[4].text))
				elif float(game_info['open_line']) > 0:
					game_info['open_line'] = ""
				else:
					game_info['open_line'] = abs(float(game_info['open_line']))
			else:
				game_info['open_line'] = re.sub('\s+','',home_info[4].text)
				game_info['close_line'] = re.sub('\s+','',home_info[5].text)
				game_info['over_under'] = re.sub('\s+','',away_info[5].text)
				if game_info['close_line'] != "":
					game_info['close_line'] = float(game_info['close_line'])
				if game_info['open_line'] == "":
					if '-' in away_info[4]:
						game_info['open_line'] = abs(float(re.sub('\s+','',away_info[4].text)))
			game_info['away_side_pct'] = re.sub('\s+','',away_info[8].text.replace('%', ''))
			game_info['home_side_pct'] = re.sub('\s+','',home_info[8].text.replace('%', ''))
			add = True
			for line in data:
				if ordered(line) == ordered(game_info):
					add = False
			if add:
				data.append(game_info)
	return data
