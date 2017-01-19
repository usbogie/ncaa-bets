"""
    from sports reference:
        date
        opp
        tm
        opp
        ortg
        drtg
        pace
        ftr
        tpar
        ts
        trb
        ast
        stl
        blk
        efg
        tov
        orb
        ft
        d_efg
        d_tov
        d_drb
        d_ft
"""
import numpy as np
import json
import pandas as pd
from datetime import date,timedelta
import math
from scipy.stats.mstats import zscore

with open('new_teams.json','r') as infile:
    teams = json.load(infile)
with open('new_game_dict.json','r') as infile:
    game_dict = json.load(infile)
with open('vi_data/new_names_dict.json','r') as infile:
    sb_names = json.load(infile)
with open('kp_data/new_names_dict.json','r') as infile:
    kp_names = json.load(infile)
with open('cbbref_data/new_names_dict.json','r') as infile:
    cbbr_names = json.load(infile)
with open('tr_data/new_names_dict.json','r') as infile:
    tr_names = json.load(infile)
with open('espn_data/names_dict.json') as infile:
    espn_names = json.load(infile)

def get_sports_ref_data(year_list=[2014,2015,2016,2017]):
    years = []
    csvs = ["game_info2014.csv","game_info2015.csv","game_info2016.csv","game_info2017.csv"]
    for i, csv in enumerate(csvs):
        if i + 2014 in year_list:
            gamesdf = pd.read_csv('cbbref_data/' + csv)
            years.append(gamesdf)
    x = 0
    y = 0
    for year in years:
        for i, row in year.iterrows():
            try:
                home_game = True
                if not row.home_game:
                    home_game = False
                    away = cbbr_names[row.team.strip()]
                    home = cbbr_names[row.opponent.strip()]
                else:
                    home = cbbr_names[row.team.strip()]
                    away = cbbr_names[row.opponent.strip()]
                gamedate = row.date.split("/")
                gamedate = date(int(gamedate[2]),int(gamedate[0]),int(gamedate[1]))
                key = str((home,away,str(gamedate)))
                try:
                    game = game_dict[key]
                except:
                    try:
                        if row.neutral == True:
                            home_game = False
                            key = str((away,home,str(gamedate)))
                            game = game_dict[key]
                        else:
                            game = game_dict[key]
                    except:
                        try:
                            gamedate -= timedelta(1)
                            key = str((home,away,str(gamedate)))
                            game = game_dict[key]
                        except:
                            try:
                                key = str((away,home,str(gamedate)))
                                game = game_dict[key]
                            except:
                                x += 1
                                continue
                loc = "home_" if home_game else "away_"
                game[loc+'ORtg'] = row.ORtg
                game[loc+'DRtg'] = row.DRtg
                game['Pace'] = row.Pace
                game[loc+'FTr'] = row.FTr
                game[loc+'tPAr'] = row.tPAr
                game[loc+'TSP'] = row.TSP
                game[loc+'TRBP'] = row.TRBP
                game[loc+'ASTP'] = row.ASTP
                game[loc+'STLP'] = row.STLP
                game[loc+'BLKP'] = row.BLKP
                game[loc+'eFGP'] = row.eFGP
                game[loc+'TOVP'] = row.TOVP
                game[loc+'ORBP'] = row.ORBP
                game[loc+'FT'] = row.FT
            except:
                continue
    print(x)

def get_spreads(year_list=[2014,2015,2016,2017]):
    print("Getting sportsbook info from Vegas Insider")
    years = []
    jsons = ['vegas_2014.json','vegas_2015.json','vegas_2016.json','vegas_2017.json']
    folder = 'vi_data/'
    for i, json in enumerate(jsons):
        if i + 2014 in year_list:
            vdf = pd.read_json(folder + json)
            years.append(vdf)

    for idx, year in enumerate(years):
        for i, row in year.iterrows():
            try:
                home = sb_names[row.home]
                away = sb_names[row.away]
                d = row.date.split("/")
                game_year = year_list[idx] if int(d[0]) < 8 else year_list[idx] - 1
                datearray = [game_year,int(d[0]),int(d[1])]
                gamedate = date(datearray[0],datearray[1],datearray[2])
                key = str((home,away,str(gamedate)))
                game = game_dict[key]
                if rowclose_line == "":
                    continue
                game["spread"] = float(row.close_line)
                if game["spread"] > 65 or game["spread"] < -65:
                    print("Found big spread, probably an over/under")
                if game["spread"] + game["margin"] < 0:
                    game["cover"] = game["away"]
                    game["home_cover"] = -.5
                elif game["spread"] + game["margin"] > 0:
                    game["cover"] = game["home"]
                    game["home_cover"] = .5
                else:
                    game["cover"] = "Tie"
                    game["home_cover"] = 0
                game["line_movement"] = 0 if row.open_line == "" else game["spread"] - float(row.open_line)
                game["home_public_percentage"] = 50 if row.home_side_pct == "" else float(row.home_side_pct)
                game["home_ats"] = row.home_ats.split("-")
                game["away_ats"] = row.away_ats.split("-")
                game["home_ats"] = 0 if game["home_ats"][0] == "0" and game["home_ats"][1] == "0" else int(game["home_ats"][0]) / (int(game["home_ats"][0])+int(game["home_ats"][1]))
                game["away_ats"] = 0 if game["away_ats"][0] == "0" and game["away_ats"][1] == "0" else int(game["away_ats"][0]) / (int(game["away_ats"][0])+int(game["away_ats"][1]))
                if math.isnan(game["spread"]):
                    print("Found spread nan that wasn't \"\"")
                    continue
            except:
                continue

def get_old_games(year_list = [2014,2015,2016,2017]):
    print("Getting old games from ESPN")
    years = []
    csvs = ["game_info2014.csv","game_info2015.csv","game_info2016.csv","game_info2017.csv"]
    for i, csv in enumerate(csvs):
        if i + 2014 in year_list:
            gamesdf = pd.read_csv('espn_data/' + csv)
            years.append(gamesdf)
    for idx, year in enumerate(years):
        for i, row in year.iterrows():
            try:
                game = {}
                game["home"] = row.Game_Home.strip()
                game["away"] = row.Game_Away.strip()
                game["season"] = str(year_list[idx])
                d = row.Game_Date.split("/")
                d.append(row.Game_Year)
                gameday = date(int(d[2]),int(d[0]),int(d[1]))
                game["tipoff"] = row.Game_Tipoff
                hour = int(game["tipoff"].split(":")[0])
                if hour < 5:
                    gameday -= timedelta(1)
                game["date"] = str(gameday)
                central = hour-1 if hour != 0 else 23
                game["tipstring"] = "{}:{} {}M CT".format((str(central%12) if central != 12 else str(12)),game["tipoff"].split(":")[1],("A" if central//12 == 0 else "P"))
                key = str((game["home"],game["away"],game["date"]))
                if key not in set(game_dict.keys()):
                    game_dict[key] = game
                else:
                    continue
                game["key"] = key
                game["home_score"] = float(row.Home_Score)
                game["away_score"] = float(row.Away_Score)
                game["margin"] = float(game["home_score"] - game["away_score"])
                if game["margin"] > 0:
                    game["winner"] = game["home"]
                else:
                    game["winner"] = game["away"]
                game["true_home_game"] = 1 if not row.Neutral_Site else 0
                game["conf"] = 1 if row.Conference_Competition else 0
                home = teams[game["home"]+game["season"]]
                away = teams[game["away"]+game["season"]]
                if key not in home["games"]:
                    home["games"].append(key)
                if key not in away["games"]:
                    away["games"].append(key)
            except:
                continue

def make_teams_dict():
    nameset = set()
    for kp,espn in kp_names.items():
        nameset.add(espn)
    for name in nameset:
        for i in range(4):
            teams[name+str(2014+i)] = {}
            teams[name+str(2014+i)]["name"] = name
            teams[name+str(2014+i)]["year"] = 2014+i
            teams[name+str(2014+i)]["games"] = []
            teams[name+str(2014+i)]["prev_games"] = []

def get_kp_stats(year_list = [2014,2015,2016,2017]):
    print("Getting kp stats")
    years = []
    jsons = ['kenpom14.json','kenpom15.json','kenpom16.json','kenpom17.json']
    for i, json in enumerate(jsons):
        if i + 2014 in year_list:
            kpdf = pd.read_json('kp_data/' + json)
            years.append(kpdf)
    for i, year in enumerate(years):
        for j, row in year.iterrows():
            name = kp_names[row.name] + str(year_list[i])
            teams[name]["kp_o"] = row.adjO
            teams[name]["kp_d"] = row.adjD
            teams[name]["kp_t"] = row.adjT
            teams[name]["kp_em"] = row.adjO - row.adjD

def get_home_splits(year_list = [2014,2015,2016]):
    print("Getting home splits")
    years = []
    jsons = ['eff_splits2014.json','eff_splits2015.json','eff_splits2016.json','eff_splits2017.json']
    for i, json in enumerate(jsons):
        if i + 2014 in year_list:
            trdf = pd.read_json('tr_data/' + json)
            years.append(trdf)

    for i, year in enumerate(years):
        for j, row in year.iterrows():
            name = tr_names[row.Name] + str(year_list[i])
            teams[name]["ORTG"] = row.ORTG
            teams[name]["DRTG"] = row.DRTG
            teams[name]["home_ORTG"] = row.home_ORTG
            teams[name]["away_ORTG"] = row.away_ORTG
            teams[name]["home_DRTG"] = row.home_DRTG
            teams[name]["away_DRTG"] = row.away_DRTG
            teams[name]["home_o_adv"] = teams[name]["home_ORTG"] - teams[name]["ORTG"]
            teams[name]["home_d_adv"] = teams[name]["home_DRTG"] - teams[name]["DRTG"]
            teams[name]["away_o_adv"] = teams[name]["away_ORTG"] - teams[name]["ORTG"]
            teams[name]["away_d_adv"] = teams[name]["away_DRTG"] - teams[name]["DRTG"]

    for name in espn_names.keys():
        home_o_adv = 0
        home_d_adv = 0
        away_o_adv = 0
        away_d_adv = 0
        for i in range(3):
            team = teams[name+str(year_list[i])]
            home_o_adv += team["home_o_adv"] / 3
            home_d_adv += team["home_d_adv"] / 3
            away_o_adv += team["away_o_adv"] / 3
            away_d_adv += team["away_d_adv"] / 3
        for i in range(4):
            team = teams[name+str(2014+i)]
            team["home_o_adv"] = home_o_adv * 100
            team["home_d_adv"] = home_d_adv * 100
            team["away_o_adv"] = away_o_adv * 100
            team["away_d_adv"] = away_d_adv * 100
# make_teams_dict()
# get_kp_stats()
# get_old_games([2017])
# get_spreads([2017])
# get_sports_ref_data([2017])
get_home_splits()

with open('new_teams.json', 'w') as outfile:
    json.dump(teams,outfile)
with open('new_game_dict.json','w') as outfile:
    json.dump(game_dict,outfile)
