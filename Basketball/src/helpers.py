import urllib.request as request
import urllib.error as error
from fake_useragent import UserAgent
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup
import json
import sys
import os

path = os.path.dirname(os.path.abspath(__file__))
this_season = date.today().year + 1 if date.today().month > 4 else date.today().year

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

def refresh_games():
    with open(os.path.join(path,'..','data','composite','game_dict.json'),'w') as outfile:
        json.dump({}, outfile)

def read_games():
    with open(os.path.join(path,'..','data','composite','game_dict.json'),'r') as infile:
        return json.load(infile)

def write_games(game_dict):
    with open(os.path.join(path,'..','data','composite','game_dict.json'),'w') as outfile:
        json.dump(game_dict, outfile)

def refresh_teams(year_list=range(2011,this_season+1)):
    names_dict = read_names()
    teams = {}
    try:
        teams = read_teams()
    except:
        pass
    nameset = set(names_dict.values())
    new_teams = ["Grand Canyon", "UMass Lowell", "New Orleans", "Incarnate Word",
                "Abilene Christian", "Northern Kentucky", "Omaha"]
    for name in nameset:
        for i in year_list:
            if i <= 2013 and name in new_teams:
                if i == 2013 and name in ["Northern Kentucky", "Omaha"]:
                    pass
                else:
                    continue
            teams[name+str(i)] = {}
            teams[name+str(i)]["name"] = name
            teams[name+str(i)]["year"] = i
            teams[name+str(i)]["games"] = []
            teams[name+str(i)]["prev_games"] = []
    write_teams(teams)

def read_teams():
    with open(os.path.join(path,'..','data','composite','teams.json'),'r') as infile:
        return json.load(infile)

def write_teams(teams):
    with open(os.path.join(path,'..','data','composite','teams.json'),'w') as outfile:
        return json.dump(teams, outfile)

def read_names():
    with open(os.path.join(path,'names.json'),'r') as infile:
        return json.load(infile)

def save():
    write_teams(teams)
    write_games(game_dict)
game_dict = read_games()
teams = read_teams()