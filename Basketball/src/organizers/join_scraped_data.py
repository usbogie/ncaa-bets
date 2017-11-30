import pandas as pd
from datetime import date,timedelta
import helpers as h
import math
import os

this_season = h.this_season
path = h.path

def get_sports_ref_data(year_list=[this_season]):
    years = []
    for year in year_list:
        data_path = os.path.join(path,'..','data','cbbref','{}.csv'.format(year))
        gamesdf = pd.read_csv(data_path)
        years.append(gamesdf)
    x = 0
    for year in years:
        for i, row in year.iterrows():
            try:
                home_game = True
                if row.road_game:
                    home_game = False
                    away = row.team
                    home = row.opponent
                else:
                    home = row.team
                    away = row.opponent
                key = str((home,away,row.date))
                try:
                    game = h.game_dict[key]
                except:
                    try:
                        if row.neutral == True:
                            home_game = False
                            key = str((away,home,row.date))
                            game = h.game_dict[key]
                        else:
                            game = h.game_dict[key]
                    except:
                        try:
                            gamedate -= timedelta(1)
                            key = str((home,away,row.date))
                            game = h.game_dict[key]
                        except:
                            try:
                                key = str((away,home,row.date))
                                game = h.game_dict[key]
                            except:
                                x += 1
                                continue
                loc = "home_" if home_game else "away_"
                game[loc+'ORtg'] = row.ORtg
                game[loc+'DRtg'] = row.DRtg
                game['Pace'] = row.Pace
                game[loc+'FTr'] = row.FTr
                game[loc+'tPAr'] = row['3PAr']
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
                print(row.team,row.opponent)
                continue
    print(x)

def get_spreads(year_list=[this_season]):
    print("Getting sportsbook info from Vegas Insider")
    years = []
    for year in year_list:
        data_path = os.path.join(path,'..','data','vi','{}.json'.format(year))
        vdf = pd.read_json(data_path)
        years.append(vdf)
    for idx, year in enumerate(years):
        for i, row in year.iterrows():
            try:
                home = row.home
                away = row.away
                d = str(row.date).split(' ')
                d = d[0].split('-')
                game_year = year_list[idx] if int(d[1]) < 8 else year_list[idx] - 1
                key = str((home,away,str(row.date).split(' ')[0]))
                switch = 1
                try:
                    game = h.game_dict[key]
                except:
                    try:
                        switch = -1
                        key = str((away,home,str(row.date).split(' ')[0]))
                        game = h.game_dict[key]
                    except:
                        switch = 1
                        key = str((home,away,str(row.date+timedelta(1)).split(' ')[0]))
                        game = h.game_dict[key]
                if row.close_line == "":
                    continue
                game["spread"] = float(row.close_line) * switch
                if game["spread"] > 65 or game["spread"] < -65:
                    print("Found big spread, probably an over/under")
                    continue
                if game["spread"] + game["margin"] < 0:
                    game["cover"] = game["away"]
                    game["home_cover"] = -1
                elif game["spread"] + game["margin"] > 0:
                    game["cover"] = game["home"]
                    game["home_cover"] = 1
                else:
                    game["cover"] = "Tie"
                    game["home_cover"] = 0
                game["line_movement"] = 0 if row.open_line == "" else game["spread"] - float(row.open_line) * switch
                game["home_public_percentage"] = 50 if row.home_side_pct == "" else float(row.home_side_pct)
                game["home_ats"] = row.home_ats.split("-")
                game["away_ats"] = row.away_ats.split("-")
                game["home_ats"] = 0 if game["home_ats"][0] == "0" and game["home_ats"][1] == "0" else int(game["home_ats"][0]) / (int(game["home_ats"][0])+int(game["home_ats"][1]))
                game["away_ats"] = 0 if game["away_ats"][0] == "0" and game["away_ats"][1] == "0" else int(game["away_ats"][0]) / (int(game["away_ats"][0])+int(game["away_ats"][1]))
                if switch == -1:
                    game["home_public_percentage"] = 100 - game["home_public_percentage"]
                    tmp = game["home_ats"]
                    game["home_ats"] = game["away_ats"]
                    game["away_ats"] = tmp
                try:
                    game["total"] = float(row.over_under)
                    game["over"] = .5 if game["home_score"] + game["away_score"] > game["total"] else -.5
                    game["over"] = 0 if game["home_score"] + game["away_score"] == game["total"] else game["over"]
                    game["over_pct"] = float(row.over_pct)
                except:
                    pass
                if math.isnan(game["spread"]):
                    print("Found spread nan that wasn't \"\"")
                    continue
            except:
                continue

def get_old_games(year_list=[this_season]):
    print("Getting old games from ESPN")
    years = []
    for year in year_list:
        data_path = os.path.join(path,'..','data','espn','{}.csv'.format(year))
        gamesdf = pd.read_csv(data_path)
        years.append(gamesdf)
    for idx, year in enumerate(years):
        print(str(year_list[idx]))
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
                h.game_dict[key] = game
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
                home = h.teams[game["home"]+game["season"]]
                away = h.teams[game["away"]+game["season"]]
                if key not in home["games"]:
                    home["games"].append(key)
                if key not in away["games"]:
                    away["games"].append(key)
            except:
                continue
