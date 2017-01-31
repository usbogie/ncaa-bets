import urllib.request as request
from bs4 import BeautifulSoup as bs
from pprint import PrettyPrinter as pp
from datetime import datetime, timedelta, date
import re
from subprocess import call
import pandas as pd
import time
import sys
import json
import csv

with open('new_names_dict.json','r') as infile:
    names_dict = json.load(infile)

def get_season_dates(start_year):
    games = pd.read_json('../vi_data/vegas_{}.json'.format(start_year+1), convert_dates=False)

    dates = games['date']
    seen = set()
    seen_add = seen.add
    dates_list = [x for x in dates.tolist() if not (x in seen or seen_add(x))]

    all_season = []
    for date in dates_list:
        year = start_year
        if date.split('-')[1] in ['01','02','03','04']:
            year += 1
        all_season.append(date)
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
        if int((datetime.now() - timedelta(1)).strftime('%Y-%m-%d').replace('-','')) < int(date.replace('-','')):
            continue
        teams={}
        for i in range(len(links)):
            try:
                soup = bs(request.urlopen(request.Request('{}{}?date={}'.format(url,links[i],date))),"html5lib")
            except:
                time.sleep(10)
                soup = bs(request.urlopen(request.Request('{}{}?date={}'.format(url,links[i],date))),"html5lib")
            name = ""
            table_contents = soup.find('table', {'class': 'tr-table datatable scrollable'}).tbody.contents[1::2]
            for row in table_contents:
                row_contents = row.contents[1::2]
                try:
                    name = names_dict[row_contents[1].text.replace("amp;","")]
                except:
                    continue
                if i == 0:
                    teams[name] = {}
                    teams[name]['Name'] = name
                    teams[name]['date'] = date
                teams[name][stats[i]] = row_contents[2]['data-sort']
                teams[name][stats[i]+'last3'] = row_contents[3]['data-sort']
                teams[name][stats[i]+'prevSeason'] = row_contents[7]['data-sort']

        for key,value in teams.items():
            team_stats.append(value)
            print(value['Name'], value['date'])
    return team_stats

def get_home_away(year, get_today=False):
    url = 'https://www.teamrankings.com/ncaa-basketball/stat/'
    links = ['offensive-efficiency',
             'defensive-efficiency']
    stats = ['ORTG','DRTG']

    team_list = []
    season_dates = get_season_dates(year-1)
    for date in season_dates:
        if int((datetime.now() - timedelta(1)).strftime('%Y-%m-%d').replace('-','')) < int(date.replace('-','')):
            continue
        teams={}
        for i in range(len(links)):
            try:
                soup = bs(request.urlopen(request.Request('{}{}?date={}'.format(url,links[i],date))),"html5lib")
            except:
                time.sleep(10)
                soup = bs(request.urlopen(request.Request('{}{}?date={}'.format(url,links[i],date))),"html5lib")
            name = ""
            table_contents = soup.find('table', {'class': 'tr-table datatable scrollable'}).tbody.contents[1::2]
            for row in table_contents:
                row_contents = row.contents[1::2]
                try:
                    name = names_dict[row_contents[1].text.replace("amp;","")]
                except:
                    continue
                if i == 0:
                    teams[name] = {}
                    teams[name]['Name'] = name
                    teams[name]['date'] = date
                teams[name][stats[i]] = row_contents[2]['data-sort']
                teams[name][stats[i]+'last3'] = row_contents[3]['data-sort']
                teams[name]['home_'+stats[i]] = row_contents[5]['data-sort']
                teams[name]['away_'+stats[i]] = row_contents[6]['data-sort']
                teams[name][stats[i]+'prevSeason'] = row_contents[7]['data-sort']

        for key,value in teams.items():
            team_list.append(value)
            print(value['Name'], value['date'])
    return team_list

team_list = get_teamrankings(2017)
with open('xteam_stats{}.csv'.format(2017), 'w') as outfile:
    keys = list(team_list[0].keys())
    writer = csv.DictWriter(outfile,fieldnames=keys)
    writer.writeheader()
    for team in team_list:
        writer.writerow(team)
