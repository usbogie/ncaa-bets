from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup as bs
from pprint import PrettyPrinter as pp
import re
from subprocess import call
import sys
import json
import csv

VERBOSE = False
try:
    if sys.argv[1] == '-v':
        VERBOSE = True
    print VERBOSE
except:
    pass

def get_teamrankings(year_list = [2014,2015,2016,2017]):
    url = 'https://www.teamrankings.com/ncaa-basketball/stat/'
    links = ['ftm-per-100-possessions',
             'opponent-free-throw-rate',
             'three-pointers-made-per-game',
             'opponent-three-point-pct',
             'offensive-rebounding-pct',
             'defensive-rebounding-pct',
             'turnover-pct',
             'opponent-turnover-pct',
             'possessions-per-game']
    year_links = {2014: '?date=2014-04-07',
                  2015: '?date=2015-04-06',
                  2016: '?date=2016-04-05',
                  2017: ''}
    stats = ['FTO','FTD','Three_O','Three_D','REBO','REBD','TOP','TOFP','POSS']
    teams = {}
    for year in year_list:
        for i in range(len(links)): #TODO figure out how to get all matchup links, and also key entries by AWAY @ HOME
            if VERBOSE:
                print 'finding stat {}'.format(i)
            s = str(bs(urlopen('{}{}'.format(url,links[i],year_links[year]))))
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

                    index += 1
        if VERBOSE:
            p = pp(indent=4)
            p.pprint(data)
        team_list = []
        for key,value in teams.items():
            team_list.append(value)
        with open('team_stats'+str(year%100)+'.csv', 'w') as outfile:
            keys = list(team_list[0].keys())
            writer = csv.DictWriter(outfile,fieldnames=keys)
            writer.writeheader()
            for team in team_list:
                writer.writerow(team)

get_teamrankings()
