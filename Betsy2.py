import statsmodels.formula.api as sm
import json
import csv
import numpy as np
import json
import ast
import pandas as pd
from datetime import date,timedelta
import math
from scipy.stats.mstats import zscore

teams = {}
with open('new_teams.json','r') as infile:
    teams = json.load(infile)
game_dict = {}
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
with open('espn_data/new_names_dict.json') as infile:
    espn_names = json.load(infile)

def get_sports_ref_data(year_list=[2011,2012,2013,2014,2015,2016,2017]):
    years = []
    for year in year_list:
        gamesdf = pd.read_csv('cbbref_data/game_info{}.csv'.format(year))
        years.append(gamesdf)
    x = 0
    y = 0
    for year in years:
        for i, row in year.iterrows():
            try:
                home_game = True
                if row.road_game:
                    home_game = False
                    try:
                        away = cbbr_names[row.team.strip()]
                        home = cbbr_names[row.opponent.strip()]
                    except:
                        away = espn_names[row.team.strip()]
                        home = espn_names[row.opponent.strip()]
                else:
                    try:
                        home = cbbr_names[row.team.strip()]
                        away = cbbr_names[row.opponent.strip()]
                    except:
                        home = espn_names[row.team.strip()]
                        away = espn_names[row.opponent.strip()]
                key = str((home,away,row.date))
                try:
                    game = game_dict[key]
                except:
                    try:
                        if row.neutral == True:
                            home_game = False
                            key = str((away,home,row.date))
                            game = game_dict[key]
                        else:
                            game = game_dict[key]
                    except:
                        try:
                            gamedate -= timedelta(1)
                            key = str((home,away,row.date))
                            game = game_dict[key]
                        except:
                            try:
                                key = str((away,home,row.date))
                                game = game_dict[key]
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
                print(row.team.strip(),row.opponent.strip())
                continue
    print(x)

def get_spreads(year_list=[2011,2012,2013,2014,2015,2016,2017]):
    print("Getting sportsbook info from Vegas Insider")
    years = []
    for year in year_list:
        vdf = pd.read_json('vi_data/vegas_{}.json'.format(year))
        years.append(vdf)
    for idx, year in enumerate(years):
        for i, row in year.iterrows():
            try:
                try:
                    home = sb_names[row.home]
                    away = sb_names[row.away]
                except:
                    home = espn_names[row.home]
                    away = espn_names[row.away]
                d = str(row.date).split(' ')
                d = d[0].split('-')
                game_year = year_list[idx] if int(d[1]) < 8 else year_list[idx] - 1
                key = str((home,away,str(row.date).split(' ')[0]))
                switch = 1
                try:
                    game = game_dict[key]
                except:
                    try:
                        switch = -1
                        key = str((away,home,str(row.date).split(' ')[0]))
                        game = game_dict[key]
                    except:
                        switch = 1
                        key = str((home,away,str(row.date+timedelta(1)).split(' ')[0]))
                        game = game_dict[key]
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

def get_old_games(year_list = [2011,2012,2013,2014,2015,2016,2017]):
    print("Getting old games from ESPN")
    years = []
    for year in year_list:
        gamesdf = pd.read_csv('espn_data/game_info{}.csv'.format(year))
        years.append(gamesdf)
    for idx, year in enumerate(years):
        print(str(year_list[idx]))
        for i, row in year.iterrows():
            try:
                game = {}
                game["home"] = espn_names[row.Game_Home.strip()]
                game["away"] = espn_names[row.Game_Away.strip()]
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

def make_teams_dict(year_list = [2011,2012,2013,2014,2015,2016,2017]):
    nameset = set()
    new_teams = ["Grand Canyon", "UMass Lowell", "New Orleans", "Incarnate Word", "Abilene Christian", "Northern Kentucky", "Omaha"]
    for kp,espn in kp_names.items():
        nameset.add(espn)
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

def betsy():
    home_ortg_std_list = []
    away_ortg_std_list = []
    home_score_std_list = []
    away_score_std_list = []
    spread_std_list = []
    pmargin_std_list = []
    diff_std_list = []
    home_count = 0
    away_count = 0
    correct = 0
    for key,team in teams.items():
        team["prev_games"] = []
    run_preseason()
    for key,team in teams.items():
        for i in range(preseason_length):
            del team["games"][0]
    for key,team in teams.items():
        team["variance"] = []
    gamedate = date(2010,11,1)
    margins = {}
    diffs = {}
    data_list = []
    # Trying to iterate through all of the games chronologically
    year_list = []
    averages = {}
    while gamedate < date.today():
        try:
            key_list = game_date_dict[str(gamedate)]
        except:
            if gamedate.year == 2017:
                print(gamedate)
            gamedate += timedelta(1)
            continue
        year = gamedate.year
        if gamedate.month > 8:
            year += 1
        if year not in year_list:
            year_list.append(year)
            print(year)
        averages = get_averages(year)
        FT_std,tPAr_std,TRBP_std,TOVP_std,opp_TOVP_std,FT_avg,tPAr_avg,TRBP_avg,TOVP_avg,opp_TOVP_avg = get_standard_deviations_averages(year)
        for key in key_list:
            game = game_dict[key]
            try:
                game["home_ORtg"]
                game["away_ORtg"]
                game["Pace"]
            except:
                continue
            try:
                home = teams[game["home"]+game["season"]]
                away = teams[game["away"]+game["season"]]
            except:
                continue
            team_list = [home,away]
            try:
                home_regseason = True if home["games"][0] == game["key"] else False
                away_regseason = True if away["games"][0] == game["key"] else False
            except:
                print(game["home"],game["away"])
                continue
            if not home_regseason and not away_regseason:
                continue

            home_dict = {}
            away_dict = {}
            dicts = [home_dict,away_dict]
            # Update stats
            for index,d in enumerate(dicts):
                d["adj_ortg"] = team_list[index]["pre_adj_ortg"]
                d["adj_drtg"] = team_list[index]["pre_adj_drtg"]
                d["adj_temp"] = team_list[index]["pre_adj_temp"]
                i = 0
                for result in team_list[index]["prev_games"]:
                    i += 1
                    d["adj_ortg"] += result["adj_ortg"] * (1 + .1 * i)
                    d["adj_drtg"] += result["adj_drtg"] * (1 + .1 * i)
                    d["adj_temp"] += result["adj_temp"] * (1 + .1 * i)
                if len(team_list[index]["prev_games"]) > 0:
                    d["adj_ortg"] /= 1 + i + (i * (i + 1) / 20)
                    d["adj_drtg"] /= 1 + i + (i * (i + 1) / 20)
                    d["adj_temp"] /= 1 + i + (i * (i + 1) / 20)
            for index,d in enumerate(dicts):
                for key,value in d.items():
                    team_list[index][key].append(value)

            # Prediction
            game["home_adj_o"] = home["adj_ortg"][-1]
            game["home_adj_d"] = home["adj_drtg"][-1]
            game["away_adj_o"] = away["adj_ortg"][-1]
            game["away_adj_d"] = away["adj_drtg"][-1]
            game["home_temp"] = home["adj_temp"][-1]
            game["away_temp"] = away["adj_temp"][-1]

            game["home_o"] = 3 if game["true_home_game"] == 1 else 0
            game["home_em"] = home["adj_ortg"][-1] - home["adj_drtg"][-1]
            game["away_em"] = away["adj_ortg"][-1] - away["adj_drtg"][-1]
            game["tempo"] = (home["adj_temp"][-1] + away["adj_temp"][-1]) / 2
            game["em_diff"] = (4 * game["home_o"] + game["home_em"] - game["away_em"]) / 100
            game["pmargin"] = game["em_diff"] * game["tempo"] * .5
            game["home_portg"] = .5 * (2 * game["home_o"] + home["adj_ortg"][-1] + away["adj_drtg"][-1])
            game["away_portg"] = .5 * (-2 * game["home_o"] + away["adj_ortg"][-1] + home["adj_drtg"][-1])
            game["ptotal"] = round((game["home_portg"] + game["away_portg"]) / 100 * game["tempo"])
            game["pmargin"] *= .9
            if game["pmargin"] > 0 and game["pmargin"] <= 6 and game["true_home_game"] == 0:
                game["pmargin"] += 1
            if game["pmargin"] < 0 and game["pmargin"] >= -6:
                game["pmargin"] -= 1
            if abs(game["pmargin"]) <= .5:
                if game["pmargin"] < 0:
                    game["pmargin"] = -1
                else:
                    game["pmargin"] = 1
            game["pmargin"] = round(game["pmargin"])

            # Decision Tree Stuff
            try:
                if game["home_cover"] != 0:
                    game["DT_home_winner"] = 1 if game["pmargin"] + game["spread"] > 0 else 0
                    game["DT_home_big"] = 1 if game["spread"] <= -10 else 0
                    game["DT_away_big"] = 1 if game["spread"] >= 7 else 0
                    game["DT_spread_diff"] = 1 if abs(game["pmargin"] + game["spread"]) >= 3 else 0
                    game["DT_home_fav"] = 1 if game["pmargin"] + game["spread"] >= 2 else 0
                    game["DT_away_fav"] = 1 if game["pmargin"] + game["spread"] <= -2 else 0
                    game["DT_home_movement"] = 1 if game["line_movement"] <= -1 else 0
                    game["DT_away_movement"] = 1 if game["line_movement"] >= 1 else 0
                    game["DT_home_public"] = 1 if game["home_public_percentage"] >= 60 else 0
                    game["DT_away_public"] = 1 if game["home_public_percentage"] <= 40 else 0
                    game["DT_home_ats"] = 1 if game["home_ats"] > .55 else 0
                    game["DT_away_ats"] = 1 if game["away_ats"] > .55 else 0
                    game["DT_home_FT"] = 1 if np.mean(home["FT"]) > FT_avg + FT_std / 2 else 0
                    game["DT_away_FT"] = 1 if np.mean(away["FT"]) > FT_avg + FT_std / 2 else 0
                    game["DT_home_tPAr"] = 1 if np.mean(home["tPAr"]) > tPAr_avg + tPAr_std / 2 else 0
                    game["DT_away_tPAr"] = 1 if np.mean(away["tPAr"]) > tPAr_avg + tPAr_std / 2 else 0
                    game["DT_home_reb"] = 1 if np.mean(home["TRBP"]) > np.mean(away["TRBP"]) + TRBP_std/2 else 0
                    game["DT_away_reb"] = 1 if np.mean(away["TRBP"]) > np.mean(home["TRBP"]) + TRBP_std/2 else 0
                    game["DT_home_TOVP"] = 1 if np.mean(home["TOVP"]) > TOVP_avg and np.mean(away["opp_TOVP"]) > opp_TOVP_avg else 0
                    game["DT_away_TOVP"] = 1 if np.mean(away["TOVP"]) > TOVP_avg and np.mean(home["opp_TOVP"]) > opp_TOVP_avg else 0
                    game_list.append(game)
                    try:
                        game["DT_over_pct"] = 1 if game["over_pct"] >= 50 else 0
                        game["DT_home_over"] = home["over_rec"][0] / (home["over_rec"][0] + home["over_rec"][1])
                        game["DT_away_over"] = away["over_rec"][0] / (away["over_rec"][0] + away["over_rec"][1])
                        game["DT_pover"] = 1 if game["ptotal"] > game["total"] else 0
                        game["DT_total_diff"] = 1 if abs(game["ptotal"] - game["total"]) > 4 else 0
                        over_games.append(game)
                    except:
                        pass
            except:
                pass

            # Data collection for testing
            h_proj_o = (home["adj_ortg"][-1] + away["adj_drtg"][-1]) / 2 + game["home_o"]
            a_proj_o = (away["adj_ortg"][-1] + home["adj_drtg"][-1]) / 2 + game["home_o"]
            try:
                home_ortg_std_list.append(h_proj_o - game["home_ORtg"])
                away_ortg_std_list.append(a_proj_o - game["away_ORtg"])
                home_score_std_list.append(h_proj_o * game["tempo"] / 100 - game["home_score"])
                away_score_std_list.append(a_proj_o * game["tempo"] / 100 - game["away_score"])
                spread_std_list.append(game["spread"] + game["margin"])
                pmargin_std_list.append(game["pmargin"] - game["margin"])
                diff_std_list.append(abs(game["pmargin"] + game["spread"]))
                if game["true_home_game"]:
                    if (game["pmargin"] > 0 and game["margin"] > 0) or (game["pmargin"] < 0 and game["margin"] < 0):
                        home_count += 1
                    else:
                        away_count += 1
            except:
                pass

            # data = {}
            # data["pmargin"] = game["pmargin"]
            # data["home_em"] = game["home_em"] / 100
            # data["away_em"] = game["away_em"] / 100
            # data["Pace"] = game["Pace"]
            # data["home_adj_o"] = home["adj_ortg"][-1]
            # data["home_adj_d"] = home["adj_drtg"][-1]
            # data["away_adj_o"] = home["adj_ortg"][-1]
            # data["away_adj_d"] = home["adj_drtg"][-1]
            # data["home_proj_o"] = data["home_adj_o"] * .5 + data["away_adj_d"] * .5 + game["home_o"]
            # data["away_proj_o"] = data["away_adj_o"] * .5 + data["home_adj_d"] * .5 + game["home_o"]
            # data["home_o"] = game["home_ORtg"]
            # data["away_o"] = game["away_ORtg"]
            # data["home_adj_temp"] = home["adj_temp"][-1]
            # data["away_adj_temp"] = away["adj_temp"][-1]
            # data["home_temp_diff"] = home["adj_temp"][-1] - averages["t"+game["season"]]
            # data["away_temp_diff"] = away["adj_temp"][-1] - averages["t"+game["season"]]
            # data["Pace_diff"] = game["Pace"] - averages["t"+game["season"]]
            # data["avg_pace"] = averages["t"+game["season"]]
            # data["margin"] = game["margin"]
            # data["ptemp"] = game["tempo"]
            # data["true_home_game"] = game["true_home_game"]
            # data["neutral"] = abs(game["true_home_game"] - 1)
            # try:
            #     data["spread"] = game["spread"]
            #     data_list.append(data)
            # except:
            #     pass
            # try:
            #     margins[game["pmargin"] // 5].append(game["margin"])
            #     diffs[game["pmargin"] // 5].append(game["pmargin"] - game["margin"])
            # except:
            #     margins[game["pmargin"] // 5] = [game["margin"]]
            #     diffs[game["pmargin"] // 5] = [game["pmargin"] - game["margin"]]
            # try:
            #     game["home_ats"]
            #     game["away_ats"]
            #     if game["season"] != "2017":
            #         regress_games.append(game)
            #     else:
            #         new_games.append(game)
            # except:
            #     pass

            # Store results
            home["FT"].append(game["home_FT"])
            home["tPAr"].append(game["home_tPAr"])
            home["TRBP"].append(game["home_TRBP"])
            home["TOVP"].append(game["home_TOVP"])
            home["opp_TOVP"].append(game["away_TOVP"])
            away["FT"].append(game["away_FT"])
            away["tPAr"].append(game["away_tPAr"])
            away["TRBP"].append(game["away_TRBP"])
            away["TOVP"].append(game["away_TOVP"])
            away["opp_TOVP"].append(game["home_TOVP"])
            try:
                if game["over"] == .5:
                    home["over_rec"][0] += 1
                    away["over_rec"][0] += 1
                elif game["over"] == -.5:
                    home["over_rec"][1] += 1
                    away["over_rec"][1] += 1
            except:
                pass
            home_results = {}
            home_o_diff = (home["adj_ortg"][-1] - away["adj_drtg"][-1]) / 2
            away_o_diff = (away["adj_ortg"][-1] - home["adj_drtg"][-1]) / 2
            temp_diff = (home["adj_temp"][-1] - away["adj_temp"][-1]) / 2
            home_results["key"] = game["key"]
            home_results["adj_ortg"] = game["home_ORtg"] + home_o_diff - game["home_o"]
            home_results["adj_drtg"] = game["home_DRtg"] - away_o_diff + game["home_o"]
            home_results["adj_temp"] = game["Pace"] + temp_diff
            away_results = {}
            away_results["key"] = game["key"]
            away_results["adj_ortg"] = game["away_ORtg"] + away_o_diff + game["home_o"]
            away_results["adj_drtg"] = game["away_DRtg"] - home_o_diff - game["home_o"]
            away_results["adj_temp"] = game["Pace"] - temp_diff
            if game["key"] in home["games"]:
                home["prev_games"].append(home_results)
                if home["games"][0] == game["key"]:
                    del home["games"][0]
            else:
                # Game in this team's preseason
                del home["adj_ortg"][-1]
                del home["adj_drtg"][-1]
                del home["adj_temp"][-1]
            if game["key"] in away["games"]:
                away["prev_games"].append(away_results)
                if away["games"][0] == game["key"]:
                    del away["games"][0]
            else:
                # Game in this team's preseason
                del away["adj_ortg"][-1]
                del away["adj_drtg"][-1]
                del away["adj_temp"][-1]
        gamedate += timedelta(1)
    for key in sorted(margins.keys()):
        data = {}
        data["pred"] = key
        data["margmed"] = np.median(margins[key])
        data["diffmed"] = np.median(diffs[key])
        data["count"] = len(margins[key])
        print(str(key * 5).rjust(5),str(data["margmed"]).rjust(5),str(data["diffmed"]).rjust(15),str(len(margins[key])).rjust(6))

    # compare_strategies(data_list)

    print("Standard deviation of Home Offensive Rating prediction:".ljust(60),np.std(home_ortg_std_list))
    print("Standard deviation of Away Offensive Rating prediction:".ljust(60),np.std(away_ortg_std_list))
    print("Standard deviation of Home Score prediction:".ljust(60),np.std(home_score_std_list))
    print("Standard deviation of Away Score prediction:".ljust(60),np.std(away_score_std_list))
    print("Standard deviation of Scoring Margin prediction:".ljust(60),np.std(pmargin_std_list))
    print("Standard deviation of Scoring Margin and Spread:".ljust(60),np.std(spread_std_list))
    print("Standard deviation of Predicted Scoring Margin and Spread:".ljust(60),np.std(diff_std_list))
    print("Home count:",home_count)
    print("Away count:",away_count)
    print("Correct:", home_count/(home_count+away_count))
    print("Ties:",correct)
    # print(teams["The Citadel2017"])

def get_standard_deviations_averages(year):
    FT_list = []
    tPAr_list = []
    TRBP_list = []
    TOVP_list = []
    opp_TOVP_list = []
    for key,team in teams.items():
        if team["year"] == year:
            FT_list.append(np.mean(team["FT"]))
            tPAr_list.append(np.mean(team["tPAr"]))
            TRBP_list.append(np.mean(team["TRBP"]))
            TOVP_list.append(np.mean(team["TOVP"]))
            opp_TOVP_list.append(np.mean(team["opp_TOVP"]))
    return (np.std(FT_list),np.std(tPAr_list),np.std(TRBP_list),np.std(TOVP_list),np.std(opp_TOVP_list),np.mean(FT_list),np.mean(tPAr_list),np.mean(TRBP_list),np.mean(TOVP_list),np.mean(opp_TOVP_list))

# Compare strategies for projecting Pace and Margin
def compare_strategies(data_list):
    gamesdf = pd.DataFrame.from_dict(data_list)
    # temp_reg = sm.ols(formula = "Pace ~ home_adj_temp + away_adj_temp -1",data=gamesdf,missing='drop').fit()
    # diff_list = []
    # for i in range(len(temp_reg.predict())):
    #     diff_list.append(temp_reg.predict()[i] - gamesdf.Pace[i])
    # temp_reg2 = sm.ols(formula = "Pace_diff ~ home_temp_diff + away_temp_diff -1",data=gamesdf,missing='drop').fit()
    # diff_list2 = []
    # for i in range(len(temp_reg2.predict())):
    #     diff_list2.append(temp_reg.predict()[i] - gamesdf.Pace[i] + gamesdf.avg_pace[i])
    # print(temp_reg.summary())
    # print(temp_reg2.summary())
    # print(np.std(diff_list))
    # print(np.std(diff_list2))

    # em_reg = sm.ols(formula = "margin ~ pmargin",data=gamesdf,missing='drop').fit()
    # diff_list_em = []
    # for i in range(len(em_reg.predict())):
    #     diff_list_em.append(em_reg.predict()[i] - gamesdf.margin[i])
    # spread_reg = sm.ols(formula = "margin ~ spread -1",data=gamesdf,missing='drop').fit()
    # diff_list_sp = []
    # for i in range(len(spread_reg.predict())):
    #     diff_list_sp.append(spread_reg.predict()[i] - gamesdf.margin[i])
    # print(em_reg.summary())
    # print(spread_reg.summary())
    # print(np.std(gamesdf.margin))
    # print(np.std(diff_list_em))
    # print(np.std(diff_list_sp))

# Get averages for a certain point in the year
# Used in "kenpom" style computations for comparison
def get_averages(year):
    averages = {}
    for key,team in teams.items():
        team_year = key[-4:]
        if team_year != str(year):
            continue
        averages["o"+team_year] = averages.get("o"+team_year,0) + team["adj_ortg"][-1] / 351
        averages["t"+team_year] = averages.get("t"+team_year,0) + team["adj_temp"][-1] / 351
    return averages

# Gets starting stats for a team in the year
# These games will not be predicted
def run_preseason():
    if not check_chronological():
        print("Preseason won't work")
    for key,team in teams.items():
        team["adj_ortg"] = []
        team["adj_drtg"] = []
        team["adj_temp"] = []
        team["FT"] = []
        team["tPAr"] = []
        team["TRBP"] = []
        team["TOVP"] = []
        team["opp_TOVP"] = []
        team["over_rec"] = [0,0]
        if len(team["games"]) < preseason_length:
            print("{} doesn't have {} games in ".format(team,preseason_length)+key[-4:])
        # Get average of each stat for each team
        for i in range(preseason_length):
            game = game_dict[team["games"][i]]
            home = teams[game["home"]+game["season"]]
            away = teams[game["away"]+game["season"]]
            team["pre_adj_temp"] = team.get("pre_adj_temp",0) + game["Pace"] / preseason_length
            try:
                team["over_rec"][0] += 1 if game["over"] == .5 else 0
                team["over_rec"][1] += 1 if game["over"] == -.5 else 0
            except:
                pass
            if game["home"] == team["name"]:
                team["pre_adj_ortg"] = team.get("pre_adj_ortg",0) + game["home_ORtg"] / preseason_length
                team["pre_adj_drtg"] = team.get("pre_adj_drtg",0) + game["home_DRtg"] / preseason_length
                team["FT"].append(game["home_FT"])
                team["tPAr"].append(game["home_tPAr"])
                team["TRBP"].append(game["home_TRBP"])
                team["TOVP"].append(game["home_TOVP"])
                team["opp_TOVP"].append(game["away_TOVP"])
            else:
                team["pre_adj_ortg"] = team.get("pre_adj_ortg",0) + game["away_ORtg"] / preseason_length
                team["pre_adj_drtg"] = team.get("pre_adj_drtg",0) + game["away_DRtg"] / preseason_length
                team["FT"].append(game["away_FT"])
                team["tPAr"].append(game["away_tPAr"])
                team["TRBP"].append(game["away_TRBP"])
                team["TOVP"].append(game["away_TOVP"])
                team["opp_TOVP"].append(game["home_TOVP"])
        # Averages will be initial stats before we level them off
        team["adj_ortg"].append(team["pre_adj_ortg"])
        team["adj_drtg"].append(team["pre_adj_drtg"])
        team["adj_temp"].append(team["pre_adj_temp"])

    # Run five times to try to level off each teams's stats to correct values
    for j in range(5):
        for key,team in teams.items():
            game_list = team["games"]
            pre_adj_off = 0
            pre_adj_def = 0
            pre_adj_tempo = 0
            for i in range(preseason_length):
                game = game_dict[game_list[i]]
                home = teams[game["home"]+game["season"]]
                away = teams[game["away"]+game["season"]]
                # Home court advantage values taken into account only if true home game
                home_o = 3 if game["true_home_game"] == 1 else 0
                home_o_diff = (home["adj_ortg"][-1] - away["adj_drtg"][-1]) / 2
                away_o_diff = (away["adj_ortg"][-1] - home["adj_drtg"][-1]) / 2
                temp_diff = (home["adj_temp"][-1] - away["adj_temp"][-1]) / 2
                # Best predictor of Ratings and Pace is an average of the two, so must reverse calculate a team's adjusted rating for the game
                if game["home"] == team["name"]:
                    pre_adj_off += (game["home_ORtg"] + home_o_diff - home_o) / preseason_length
                    pre_adj_def += (game["home_DRtg"] - away_o_diff + home_o) / preseason_length # Positive drtg good, amount of points fewer they gave up than expected
                    pre_adj_tempo += (game["Pace"] - home["adj_temp"][-1]) / preseason_length
                else:
                    pre_adj_off += (game["away_ORtg"] + away_o_diff + home_o) / preseason_length
                    pre_adj_def += (game["away_DRtg"] - home_o_diff - home_o) / preseason_length # Positive drtg good, amount of points fewer they gave up than expected
                    pre_adj_tempo += (game["Pace"] - home["adj_temp"][-1]) / preseason_length
            team["adj_ortg"].append(pre_adj_off)
            team["adj_drtg"].append(pre_adj_def)
            team["adj_temp"].append(pre_adj_tempo)
        # print(teams["Vanderbilt2014"]["adj_ortg"][-1],teams["Vanderbilt2014"]["adj_drtg"][-1],teams["Vanderbilt2014"]["adj_temp"][-1])
            team["pre_adj_ortg"] = team["adj_ortg"][-1]
            team["pre_adj_drtg"] = team["adj_drtg"][-1]
            team["pre_adj_temp"] = team["adj_temp"][-1]

# Checks the chronological ordering of games in the game lists
def check_chronological():
    flag = True
    for key,team in teams.items():
        game_list = team["games"]
        for i in range(len(game_list)-1):
            date1 = game_list[i].split(",")[2].strip().replace("'","").replace(")","").split("-")
            date2 = game_list[i+1].split(",")[2].strip().replace("'","").replace(")","").split("-")
            for j in range(3):
                if int(date1[j]) < int(date2[j]):
                    break
                elif int(date1[j]) > int(date2[j]):
                    flag = False
                    break
                if j == 2:
                    print(game_list[i],date1)
                    print(game_list[i+1],date2)
                    print("Duplicate")
        if flag == False:
            print("Not Chronological")
            break
    return flag

# Eliminates games that don't have Offensive Rating stats for both teams, or Pace
def eliminate_games_missing_data():
    keys_to_remove = set()
    for key,team in teams.items():
        for key in team["games"]:
            game = game_dict[key]
            try:
                dummy1 = game["home_ORtg"]
                dummy2 = game["away_ORtg"]
                dummy3 = game["Pace"]
            except:
                keys_to_remove.add(key)
    for key in keys_to_remove:
        game = game_dict[key]
        try:
            teams[game["home"]+game["season"]]["games"].remove(key)
            teams[game["away"]+game["season"]]["games"].remove(key)
        except:
            print("just curious")
    for key,team in teams.items():
        if len(team["games"]) <= 5:
            print(team)

# Creates game dictionary that facilitates getting games played on the same date
def get_game_date_dict():
    game_date_dict = {}
    for key,game in game_dict.items():
        try:
            if game["key"] not in game_date_dict[game["date"]]:
                game_date_dict[game["date"]].append(game["key"])
        except:
            game_date_dict[game["date"]] = [game["key"]]
    return game_date_dict

def get_new_games(season='2017'):
    print("Getting new games")
    gamesdf = pd.read_csv('espn_data/upcoming_games.csv')
    upcoming_games = {}
    new_games = []
    new_over_games = []
    for i, row in gamesdf.iterrows():
        try:
            game = {}
            game["home"] = espn_names[row.Game_Home.strip()]
            game["away"] = espn_names[row.Game_Away.strip()]
            game["tipoff"] = row.Game_Tipoff
            hour = int(game["tipoff"].split(":")[0])
            central = hour-1 if hour != 0 else 23
            game["tipstring"] = "{}:{} {}M CT".format((str(central%12) if central != 12 else str(12)),game["tipoff"].split(":")[1],("A" if central//12 == 0 else "P"))
            key = str((game["home"],game["away"]))
            if key not in set(upcoming_games.keys()):
                upcoming_games[key] = game
            else:
                continue
            game["true_home_game"] = 1 if not row.Neutral_Site else 0
            game["conf"] = 1 if row.Conference_Competition else 0
        except:
            print(row.Game_Home,row.Game_Away)
            continue

    with open('vi_data/vegas_today.json','r') as infile:
        vegas_info = json.load(infile)
    for game in vegas_info:
        try:
            home = espn_names[game['home']]
            away = espn_names[game['away']]
            key = str((home,away))
            new_game = upcoming_games[key]
            new_game['key'] = key
            new_game['spread_home'] = (float(game['close_line']),-110)
            new_game['spread'] = new_game['spread_home'][0]
            new_game["line_movement"] = 0 if game["open_line"] == "" else new_game["spread"] - float(game["open_line"])
            new_game["home_public_percentage"] = 50 if game["home_side_pct"] == "" else float(game["home_side_pct"])
            new_game["home_ats"] = game["home_ats"].split("-")
            new_game["away_ats"] = game["away_ats"].split("-")
            new_game["home_ats"] = 0 if new_game["home_ats"][0] == "0" and new_game["home_ats"][1] == "0" else int(new_game["home_ats"][0]) / (int(new_game["home_ats"][0])+int(new_game["home_ats"][1]))
            new_game["away_ats"] = 0 if new_game["away_ats"][0] == "0" and new_game["away_ats"][1] == "0" else int(new_game["away_ats"][0]) / (int(new_game["away_ats"][0])+int(new_game["away_ats"][1]))
            try:
                new_game["total"] = float(game["over_under"])
                new_game["over_pct"] = float(game["over_pct"])
            except:
                new_game["over_pct"] = 50
            new_games.append(new_game)
        except:
            print("In vegas info, no game matched:",game["home"],game["away"])

    for game in new_games:
        home = teams[espn_names[game["home"]]+season]
        away = teams[espn_names[game["away"]]+season]

        team_list = [home,away]
        home_dict = {}
        away_dict = {}
        dicts = [home_dict,away_dict]
        # Update stats
        for index,d in enumerate(dicts):
            d["adj_ortg"] = team_list[index]["pre_adj_ortg"]
            d["adj_drtg"] = team_list[index]["pre_adj_drtg"]
            d["adj_temp"] = team_list[index]["pre_adj_temp"]
            i = 0
            for result in team_list[index]["prev_games"]:
                i += 1
                d["adj_ortg"] += result["adj_ortg"] * (1 + .1 * i)
                d["adj_drtg"] += result["adj_drtg"] * (1 + .1 * i)
                d["adj_temp"] += result["adj_temp"] * (1 + .1 * i)
            if len(team_list[index]["prev_games"]) > 0:
                d["adj_ortg"] /= 1 + i + (i * (i + 1) / 20)
                d["adj_drtg"] /= 1 + i + (i * (i + 1) / 20)
                d["adj_temp"] /= 1 + i + (i * (i + 1) / 20)
        for index,d in enumerate(dicts):
            for key,value in d.items():
                team_list[index][key].append(value)

        game["home_adj_o"] = home["adj_ortg"][-1]
        game["home_adj_d"] = home["adj_drtg"][-1]
        game["away_adj_o"] = away["adj_ortg"][-1]
        game["away_adj_d"] = away["adj_drtg"][-1]
        game["home_temp"] = home["adj_temp"][-1]
        game["away_temp"] = away["adj_temp"][-1]

        game["home_o"] = 3 if game["true_home_game"] == 1 else 0
        game["home_em"] = home["adj_ortg"][-1] - home["adj_drtg"][-1]
        game["away_em"] = away["adj_ortg"][-1] - away["adj_drtg"][-1]
        game["tempo"] = (home["adj_temp"][-1] + away["adj_temp"][-1]) / 2
        game["em_diff"] = (4 * game["home_o"] + game["home_em"] - game["away_em"]) / 100
        game["pmargin"] = game["em_diff"] * game["tempo"] * .5
        if game["pmargin"] > 0 and game["true_home_game"] == 1:
            game["pmargin"] = game["pmargin"] * .9
        if game["pmargin"] > 0 and game["pmargin"] <= 6 and game["true_home_game"] == 0:
            game["pmargin"] += 1
        if game["pmargin"] < 0 and game["pmargin"] >= -6:
            game["pmargin"] -= 1
        if abs(game["pmargin"]) <= .5:
            if game["pmargin"] < 0:
                game["pmargin"] = -1
            else:
                game["pmargin"] = 1
        game["pmargin"] = round(game["pmargin"])
        game["home_portg"] = .5 * (2 * game["home_o"] + home["adj_ortg"][-1] + away["adj_drtg"][-1])
        game["away_portg"] = .5 * (-2 * game["home_o"] + away["adj_ortg"][-1] + home["adj_drtg"][-1])
        game["ptotal"] = round((game["home_portg"] + game["away_portg"]) / 100 * game["tempo"])

        FT_std,tPAr_std,TRBP_std,TOVP_std,opp_TOVP_std,FT_avg,tPAr_avg,TRBP_avg,TOVP_avg,opp_TOVP_avg = get_standard_deviations_averages(int(season))
        game["DT_home_winner"] = 1 if game["pmargin"] + game["spread"] > 0 else 0
        game["DT_home_big"] = 1 if game["spread"] <= -10 else 0
        game["DT_away_big"] = 1 if game["spread"] >= 7 else 0
        game["DT_spread_diff"] = 1 if abs(game["pmargin"] + game["spread"]) >= 3 else 0
        game["DT_home_fav"] = 1 if game["pmargin"] + game["spread"] >= 2 else 0
        game["DT_away_fav"] = 1 if game["pmargin"] + game["spread"] <= -2 else 0
        game["DT_home_movement"] = 1 if game["line_movement"] <= -1 else 0
        game["DT_away_movement"] = 1 if game["line_movement"] >= 1 else 0
        game["DT_home_public"] = 1 if game["home_public_percentage"] >= 60 else 0
        game["DT_away_public"] = 1 if game["home_public_percentage"] <= 40 else 0
        game["DT_home_ats"] = 1 if game["home_ats"] > .55 else 0
        game["DT_away_ats"] = 1 if game["away_ats"] > .55 else 0
        game["DT_home_FT"] = 1 if np.mean(home["FT"]) > FT_avg + FT_std / 2 else 0
        game["DT_away_FT"] = 1 if np.mean(away["FT"]) > FT_avg + FT_std / 2 else 0
        game["DT_home_tPAr"] = 1 if np.mean(home["tPAr"]) > tPAr_avg + tPAr_std / 2 else 0
        game["DT_away_tPAr"] = 1 if np.mean(away["tPAr"]) > tPAr_avg + tPAr_std / 2 else 0
        game["DT_home_reb"] = 1 if np.mean(home["TRBP"]) > np.mean(away["TRBP"]) + TRBP_std/2 else 0
        game["DT_away_reb"] = 1 if np.mean(away["TRBP"]) > np.mean(home["TRBP"]) + TRBP_std/2 else 0
        game["DT_home_TOVP"] = 1 if np.mean(home["TOVP"]) > TOVP_avg and np.mean(away["opp_TOVP"]) > opp_TOVP_avg else 0
        game["DT_away_TOVP"] = 1 if np.mean(away["TOVP"]) > TOVP_avg and np.mean(home["opp_TOVP"]) > opp_TOVP_avg else 0
        try:
            game["DT_home_over"] = home["over_rec"][0] / (home["over_rec"][0] + home["over_rec"][1])
            game["DT_away_over"] = away["over_rec"][0] / (away["over_rec"][0] + away["over_rec"][1])
            game["DT_pover"] = 1 if game["ptotal"] > game["total"] else 0
            game["DT_total_diff"] = 1 if abs(game["ptotal"] - game["total"]) > 4 else 0
            game["DT_over_pct"] = 1 if game["over_pct"] >= 50 else 0
            new_over_games.append(game)
        except:
            pass

        print("Found:",game["home"],game["away"])
    with open('todays_games.csv','w') as outfile:
        keys = list(new_games[0].keys())
        writer = csv.DictWriter(outfile,fieldnames = keys)
        writer.writeheader()
        for game in new_games:
            writer.writerow(game)

    with open('todays_over_games.csv','w') as outfile:
        keys = list(new_over_games[0].keys())
        writer = csv.DictWriter(outfile,fieldnames = keys)
        writer.writeheader()
        for game in new_over_games:
            writer.writerow(game)

# make_teams_dict()
# get_old_games()
#
# get_spreads()
# get_sports_ref_data()
#
# with open('new_teams.json','w') as outfile:
#     json.dump(teams,outfile)
# with open('new_game_dict.json','w') as outfile:
#     json.dump(game_dict,outfile)

# Number of games used to create starting stats for teams
preseason_length = 5

regress_games = []
new_games = []

eliminate_games_missing_data()
game_date_dict = get_game_date_dict()
over_games = []
game_list = []
betsy()
key_list = set()
for key, game in game_dict.items():
    for k in game.keys():
        key_list.add(k)
print(len(game_list))

get_new_games()
test_betsy()

with open('games.csv','w') as outfile:
    writer = csv.DictWriter(outfile,fieldnames = list(key_list))
    writer.writeheader()
    for game in game_list:
        writer.writerow(game)

# with open('over_games.csv','w') as outfile:
#     keys = list(over_games[0].keys())
#     writer = csv.DictWriter(outfile,fieldnames = keys)
#     writer.writeheader()
#     for game in over_games:
#         writer.writerow(game)
