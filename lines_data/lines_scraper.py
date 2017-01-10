import urllib.request as request
import urllib.error as error
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime, timedelta
import sys
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

def get_data(get_yesterday=False, year=2017):
	all_dates = make_season(year-1)
	with open('lines' + str(year) + '.json','r+') as infile:
 		data = json.load(infile)
	base = "http://www.lines.com/odds/ncaab/spreads-totals/"
	today = int((datetime.now() - timedelta(1)).strftime('%Y-%m-%d').replace('-',''))
	for day in all_dates:
		if today < int(day.replace('-','')):
			continue
		if get_yesterday:
			if today - int(day.replace('-','')) != 1:
				continue
		print (day)
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

		if soup.find('div',{'class': 'nogames'}) is not None:
			continue

		table = soup.find('table', {'id': 'odds-1league-14'})
		data = []
		entries = [tr.findAll('td') for tr in table.tbody.findAll('tr')]
		for entry in entries:
			game_info = {}
			game_info['date'] = entry[1].div.contents[0]
			if len(entry[2].a.contents) < 3 and entry[2].a.contents[0] == 'High Point':
				game_info['away'],game_info['home'] = 'Longwood','High Point'
			else:
				game_info['away'],game_info['home'] = entry[2].a.contents[0], entry[2].a.contents[2]
			if entry[3].find('strong', {'class': 'postponed'}) is not None:
				continue
			spans = entry[3].find('div', {'class': 'score last'})
			if spans is None:
				continue
			away_score, home_score = spans.contents[0].text, spans.contents[1].text
			bet365 = entry[7].contents
			game_info['total'] = bet365[0].text.replace(u"½", u".5").split('\xa0')[0].strip()
			if game_info['total'] == '-':
				game_info['total'] = None
			game_info['spread'] = bet365[3].text.replace(u"½", u".5").replace('+','').split('\xa0')[0].strip()
			if game_info['spread'] == '-' or game_info['spread'] == 'PK':
				game_info['spread'] = '0'
			if float(away_score) - float(home_score) > float(game_info['spread']):
				game_info['ats'] = 'L'
			else:
				game_info['ats'] = 'W'
			data.append(game_info)
	return data
