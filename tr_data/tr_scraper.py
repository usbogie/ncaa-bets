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

def get_teamrankings():
    url = 'https://www.teamrankings.com/ncaa-basketball/stat/'
    links = ['percent-of-points-from-free-throws',
             'opponent-free-throw-rate',
             'percent-of-points-from-3-pointers',
             'three-point-pct',
             'opponent-three-point-pct',
             'offensive-rebounding-pct',
             'defensive-rebounding-pct',
             'turnover-pct',
             'opponent-turnover-pct']
    stats = ['FTO','FTD','Three_O','perc3','Three_D','REBO','REBD','TOP','TOFP']
    teams = {}
    for i in range(len(links)): #TODO figure out how to get all matchup links, and also key entries by AWAY @ HOME
        if VERBOSE:
            print 'finding stat {}'.format(i)
        s = str(bs(urlopen('{}{}'.format(url,links[i]))))
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
    with open('team_stats17.csv', 'w') as outfile:
        keys = list(team_list[0].keys())
        writer = csv.DictWriter(outfile,fieldnames=keys)
        writer.writeheader()
        for team in team_list:
            writer.writerow(team)

get_teamrankings()
