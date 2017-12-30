from fuzzywuzzy import fuzz
import pandas as pd
import json
import os

def get_espn():
    name_set = set()
    for y in range(first_season, season + 1):
        gamesdf = pd.read_csv(os.path.join(path,'..','data','espn','{}.csv'.format(y)))
        for i, row in gamesdf.iterrows():
            name_set.add(row.Game_Home.strip())
            name_set.add(row.Game_Away.strip())
    return name_set

def get_cbbr():
    name_set = set()
    for y in range(first_season, season + 1):
        gamesdf = pd.read_csv(os.path.join(path,'..','data','cbbref','{}.csv'.format(y)))
        for i, row in gamesdf.iterrows():
            name_set.add(row.team.strip())
            name_set.add(row.opponent.strip())
    return name_set

def get_vi():
    name_set = set()
    for y in range(first_season, season + 1):
        gamesdf = pd.read_json(os.path.join(path,'..','data','vi','{}.json'.format(y)))
        for i, row in gamesdf.iterrows():
            name_set.add(row.home.strip())
            name_set.add(row.away.strip())
    return name_set

def find_new_names():
    # Get every variation of name
    name_set = get_espn() | get_cbbr() | get_vi()
    print(len(name_set))
    # Remove names already in dict
    teamset = set()
    for alt,reg in names.items():
        teamset.add(alt)
        teamset.add(reg)
        if alt in name_set:
            name_set.remove(alt)
        if reg in name_set:
            name_set.remove(reg)

    # Analyze each name
    check_later = set()
    for team in sorted(name_set):
        ratio = 0
        t = ""
        for t2 in teamset:
            if fuzz.ratio(team,t2) > ratio:
                ratio = fuzz.ratio(team,t2)
                t = t2
        print(team,t,ratio)
        s = input("Type 'y' if names match, 'n' if not d1")
        if s == 'y':
            check_later.add((team,t))
        elif s == 'n':
            pass
        else:
            espn_name = input("Type ESPN name:")
            check_later.add((team,espn_name))
    for team,espn in check_later:
        names[team] = espn
    print(len(set(names.values())))

    with open('names.json', 'w') as outfile:
        json.dump(names, outfile)

with open('names.json','r') as infile:
    names = json.load(infile)
first_season = 2011
season = 2018
path = os.path.dirname(os.path.abspath(__file__))
find_new_names()
