import json
import sys
import os
import pandas as pd
from datetime import datetime, timedelta, date

path = os.path.dirname(os.path.abspath(__file__))
game_dict_path = os.path.join(path,'..','data','composite','game_dict.json')
games_path = os.path.join(path,'..','data','composite','games.csv')
teams_path = os.path.join(path,'..','data','composite','teams.json')
names_path = os.path.join(path,'organizers','names.json')
this_season = date.today().year + 1 if date.today().month > 4 else date.today().year
first_season = 2011

months = {
    11: 'November',
    12: 'December',
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April'
}

def refresh_game_dict():
    with open(game_dict_path,'w') as outfile:
        json.dump({}, outfile)


def read_game_dict():
    with open(game_dict_path,'r') as infile:
        return json.load(infile)


def write_game_dict(game_dict):
    with open(game_dict_path,'w') as outfile:
        json.dump(game_dict, outfile)


def refresh_games_csv():
    pd.DataFrame().to_csv(games_path)


def read_games_csv():
    return pd.read_csv(games_path)


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
    with open(teams_path,'r') as infile:
        return json.load(infile)


def write_teams(teams):
    with open(teams_path,'w') as outfile:
        return json.dump(teams, outfile)


def read_names():
    with open(names_path,'r') as infile:
        return json.load(infile)


def save():
    write_teams(teams)
    write_game_dict(game_dict)

game_dict = read_game_dict()
teams = read_teams()
gamesdf = read_games_csv()