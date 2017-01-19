import urllib.request as request
from bs4 import BeautifulSoup as bs
from pprint import PrettyPrinter as pp
import re
from subprocess import call
import pandas as pd
import sys
import json
import csv

def get_season_dates(start_year):
    games = pd.read_json('../vi_data/vegas_{}.json'.format(start_year+1))

    dates = games['date']
    seen = set()
    seen_add = seen.add
    dates_list = [x for x in dates.tolist() if not (x in seen or seen_add(x))]

    all_season = []
    for date in dates_list:
        year = start_year
        if date[:2] in ['01','02','03','04']:
            year += 1
        all_season.append('{}-{}-{}'.format(year, date[:2], date[-2:]))
    return all_season

def get_teamrankings(year=2017, get_today=False):
    url = 'https://www.teamrankings.com/ncaa-basketball/stat/'
    links = ['ftm-per-100-possessions',
             'opponent-free-throw-rate',
             'three-pointers-made-per-game',
             'opponent-three-point-pct',
             'offensive-rebounding-pct',
             'defensive-rebounding-pct',
             'total-rebounding-percentage',
             'turnover-pct',
             'opponent-turnover-pct',
             'possessions-per-game']
    stats = ['FTO','FTD','Three_O','Three_D','REBO','REBD','REB','TOP','TOFP','POSS']

    team_stats = []
    season_dates = get_season_dates(year-1)
    for date in season_dates:
        datestr = "/".join(date.split('-')[1:]+date.split('-')[:1])
        teams={}
        for i in range(len(links)): #TODO figure out how to get all matchup links, and also key entries by AWAY @ HOME
            s = str(bs(request.urlopen(request.Request('{}{}?date={}'.format(url,links[i],date))),"html5lib"))
            match = 'data-sort="'
            index = 0
            name = ""
            for j in range(len(s)-len(match)):
                if s[j:j+11] == match:
                    if index % 8 == 1:
                        for k in range(len(s)-j):
                            if s[j+11+k] == "\"":
                                name = s[j+11:j+11+k].replace("amp;","")
                                if i == 0:
                                    teams[name] = {}
                                    teams[name]['Name'] = name
                                    teams[name]['date'] = datestr
                                break
                    if index % 8 == 2:
                        for k in range(len(s)-j):
                            if s[j+11+k] == "\"":
                                teams[name][stats[i]] = float(s[j+11:j+11+k])
                                break

                    index += 1
        for key,value in teams.items():
            team_stats.append(value)
            print(value)
    return team_stats

def get_home_away(year_list = [2012,2013,2014,2015,2016,2017]):
    url = 'https://www.teamrankings.com/ncaa-basketball/stat/'
    links = ['offensive-efficiency',
             'defensive-efficiency']
    year_links = {2012: '?date=2012-04-02',
                  2013: '?date=2013-04-08',
                  2014: '?date=2014-04-07',
                  2015: '?date=2015-04-06',
                  2016: '?date=2016-04-05',
                  2017: ''}
    stats = ['ORTG','DRTG']
    teams = {}
    for year in year_list:
        for i in range(len(links)): #TODO figure out how to get all matchup links, and also key entries by AWAY @ HOME
            s = str(bs(request.urlopen(request.Request('{}{}{}'.format(url,links[i],year_links[year]))),"html5lib"))
            # s = str(bs(request.urlopen(request.Request('http://kenpom.com/index.php'+year_str)).read(), "html5lib"))
            match = 'data-sort="'
            index = 0
            name = ""
            for j in range(len(s)-len(match)):
                if s[j:j+11] == match:
                    if index % 8 == 1:
                        for k in range(len(s)-j):
                            if s[j+11+k] == "\"":
                                name = s[j+11:j+11+k].replace("amp;","")
                                if i == 0:
                                    teams[name] = {}
                                    teams[name]['Name'] = name
                                break
                    if index % 8 == 2:
                        for k in range(len(s)-j):
                            if s[j+11+k] == "\"":
                                teams[name][stats[i]] = float(s[j+11:j+11+k])
                                break
                    if index % 8 == 5:
                        for k in range(len(s)-j):
                            if s[j+11+k] == "\"":
                                teams[name]['home_'+stats[i]] = float(s[j+11:j+11+k])
                                break
                    if index % 8 == 6:
                        for k in range(len(s)-j):
                            if s[j+11+k] == "\"":
                                teams[name]['away_'+stats[i]] = float(s[j+11:j+11+k])
                                break

                    index += 1
        team_list = []
        for key,value in teams.items():
            team_list.append(value)
        with open('eff_splits{}.json'.format(str(year)),'w') as outfile:
            json.dump(team_list,outfile)
team_list = get_teamrankings(2017)
with open('xteam_stats17.csv', 'w') as outfile:
    keys = list(team_list[0].keys())
    writer = csv.DictWriter(outfile,fieldnames=keys)
    writer.writeheader()
    for team in team_list:
        writer.writerow(team)
