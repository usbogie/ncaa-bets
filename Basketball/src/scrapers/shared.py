import urllib.request as request
import urllib.error as error
from fake_useragent import UserAgent
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup
import sys

def get_soup(url):
    ua = UserAgent()
    try:
        page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
    except ConnectionResetError as e:
        try:
            wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
            time.sleep(wait_time)
            print("First attempt for %s failed. Trying again." % (url))
            page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
        except:
            print(e)
            sys.exit()
    except error.URLError as e:
        try:
            wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
            time.sleep(wait_time)
            print("First attempt for %s failed. Trying again." % (url))
            page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
        except:
            print(e)
            sys.exit()
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
    return BeautifulSoup(content, "html5lib")

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
