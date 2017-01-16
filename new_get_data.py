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
with open('spread_dict.json','r') as infile:
    spread_dict = json.load(infile)
with open('vi_data/new_names_dict.json','r') as infile:
    sb_names = json.load(infile)
with open('kp_data/new_names_dict.json','r') as infile:
    kp_names = json.load(infile)
with open('cbbref_data/new_names_dict.json','r') as infile:
    cbbr_names = json.load(infile)
spread_dict = {}
teams = {}
game_dict = {}
def get_sports_ref_data(year_list=[2014,2015,2016,2017]):
    years = []
    csvs = ["game_info2014.csv","game_info2015.csv","game_info2016.csv","game_info2017.csv"]
    for i in range(len(csvs)):
        if i + 2014 in year_list:
            gamesdf = pd.read_csv('cbbref_data/' + csvs[i])
            years.append(gamesdf)
    x = 0
    y = 0
    for year in range(len(years)):
        for i in range(len(years[year].team)):
            try:
                home_game = True
                if not years[year].home_game[i]:
                    home_game = False
                    away = cbbr_names[years[year].team[i].strip()]
                    home = cbbr_names[years[year].opponent[i].strip()]
                else:
                    home = cbbr_names[years[year].team[i].strip()]
                    away = cbbr_names[years[year].opponent[i].strip()]
                gamedate = years[year].date[i].split("/")
                gamedate = date(int(gamedate[2]),int(gamedate[0]),int(gamedate[1]))
                key = str((home,away,str(gamedate)))
                try:
                    game = game_dict[key]
                except:
                    try:
                        if years[year].neutral[i] == True:
                            home_game = False
                            key = str((away,home,str(gamedate)))
                            game = game_dict[key]
                        else:
                            game_dict[key]
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
                loc = "home_"
                if not home_game:
                    loc = "away_"
                game[loc+'ORtg'] = years[year].ORtg[i]
                game[loc+'DRtg'] = years[year].DRtg[i]
                game['Pace'] = years[year].Pace[i]
                game[loc+'FTr'] = years[year].FTr[i]
                game[loc+'tPAr'] = years[year].tPAr[i]
                game[loc+'TSP'] = years[year].TSP[i]
                game[loc+'TRBP'] = years[year].TRBP[i]
                game[loc+'ASTP'] = years[year].ASTP[i]
                game[loc+'STLP'] = years[year].STLP[i]
                game[loc+'BLKP'] = years[year].BLKP[i]
                game[loc+'eFGP'] = years[year].eFGP[i]
                game[loc+'TOVP'] = years[year].TOVP[i]
                game[loc+'ORBP'] = years[year].ORBP[i]
                game[loc+'FT'] = years[year].FT[i]
            except:
                continue
    print(x)

def get_spreads(year_list=[2014,2015,2016,2017]):
    print("Getting sportsbook info from Vegas Insider")
    years = []
    jsons = ['vegas_2014.json','vegas_2015.json','vegas_2016.json','vegas_2017.json']
    folder = 'vi_data/'
    for i in range(len(jsons)):
        if i + 2014 in year_list:
            vdf = pd.read_json(folder + jsons[i])
            years.append(vdf)
    for year in range(len(years)):
        for i in range(len(years[year].home)):
            try:
                home = sb_names[years[year].home[i]]
                away = sb_names[years[year].away[i]]
                d = years[year].date[i].split("/")
                game_year = year_list[year] if int(d[0]) < 8 else year_list[year] - 1
                datearray = [game_year,int(d[0]),int(d[1])]
                gamedate = date(datearray[0],datearray[1],datearray[2])
                key = str((home,away,str(gamedate)))
                try:
                    spread_dict[key]
                    continue
                except:
                    pass
                game = game_dict[key]
                if years[year].close_line[i] == "":
                    continue
                game["spread"] = float(years[year].close_line[i])
                if game["spread"] > 65 or game["spread"] < -65:
                    print("Found big spread, probably an over/under")
                if game["spread"] + game["margin"] < 0:
                    game["cover"] = game["away"]
                elif game["spread"] + game["margin"] > 0:
                    game["cover"] = game["home"]
                else:
                    game["cover"] = "Tie"
                if math.isnan(game["spread"]):
                    print("Found spread nan that wasn't \"\"")
                    continue
                spread_dict[key] = game
            except:
                continue
def get_old_games(year_list = [2014,2015,2016,2017]):
    print("Getting old games from ESPN")
    years = []
    csvs = ["game_info2014.csv","game_info2015.csv","game_info2016.csv","game_info2017.csv"]
    for i in range(len(csvs)):
        if i + 2014 in year_list:
            gamesdf = pd.read_csv('espn_data/' + csvs[i])
            years.append(gamesdf)
    for year in range(len(years)):
        for i in range(len(years[year].Game_Away)):
            try:
                game = {}
                game["home"] = years[year].Game_Home[i].strip()
                game["away"] = years[year].Game_Away[i].strip()
                game["season"] = str(year_list[year])
                home = teams[game["home"]+game["season"]]
                away = teams[game["away"]+game["season"]]
                d = years[year].Game_Date[i].split("/")
                d.append(years[year].Game_Year[i])
                gameday = date(int(d[2]),int(d[0]),int(d[1]))
                game["tipoff"] = years[year].Game_Tipoff[i]
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
                game["home_score"] = float(years[year].Home_Score[i])
                game["away_score"] = float(years[year].Away_Score[i])
                game["margin"] = float(game["home_score"] - game["away_score"])
                if game["margin"] > 0:
                    game["winner"] = game["home"]
                else:
                    game["winner"] = game["away"]
                game["true_home_game"] = 1 if not years[year].Neutral_Site[i] else 0
                game["conf"] = 1 if years[year].Conference_Competition[i] else 0
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

def set_game_attributes():
    for key,game in game_dict.items():
        game["home_tempo"] = teams[game["home"]+game["season"]]["kp_t"]
        game["away_tempo"] = teams[game["away"]+game["season"]]["kp_t"]

def get_kp_stats(year_list = [2014,2015,2016,2017]):
    print("Getting kp stats")
    years = []
    jsons = ['kenpom14.json','kenpom15.json','kenpom16.json','kenpom17.json']
    for i in range(len(jsons)):
        if i + 2014 in year_list:
            kpdf = pd.read_json('kp_data/' + jsons[i])
            years.append(kpdf)
    for i in range(len(years)):
        teams_count = len(years[i])
        for j in range(teams_count):
            name = kp_names[years[i].name[j]] + str(year_list[i])
            teams[name]["kp_o"] = years[i].adjO[j]
            teams[name]["kp_d"] = years[i].adjD[j]
            teams[name]["kp_t"] = years[i].adjT[j]
            teams[name]["kp_em"] = teams[name]["kp_o"] - teams[name]["kp_d"]

make_teams_dict()
get_kp_stats()
get_old_games()
get_spreads()
get_sports_ref_data()
set_game_attributes()

with open('new_teams.json', 'w') as outfile:
    json.dump(teams,outfile)
with open('new_game_dict.json','w') as outfile:
    json.dump(game_dict,outfile)
with open('spread_dict.json','w') as outfile:
    json.dump(spread_dict,outfile)
