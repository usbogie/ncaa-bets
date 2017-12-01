import json
import sys
import os
from datetime import datetime, timedelta, date

path = os.path.dirname(os.path.abspath(__file__))
this_season = date.today().year + 1 if date.today().month > 4 else date.today().year

months = {
    11: 'November',
    12: 'December',
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April'
}

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
    with open(os.path.join(path,'organizers','names.json'),'r') as infile:
        return json.load(infile)

def save():
    write_teams(teams)
    write_games(game_dict)
game_dict = read_games()
teams = read_teams()
