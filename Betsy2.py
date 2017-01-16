'''
information to know about each game:
    margin
    tempos
    true home game
probability percentage could be learned
figure out a recency bias
find sd of difference between prediction and actual margin for all games
use a consistency rating for probability, aka varianace in adjusted score margin, relate to average variance
'''
import numpy as np
import pandas as pd
import statsmodels.formula.api as sm
from datetime import date,timedelta
import json

with open('new_teams.json','r') as infile:
    teams = json.load(infile)
with open('new_game_dict.json','r') as infile:
    game_dict = json.load(infile)
with open('spread_dict.json','r') as infile:
    spread_dict = json.load(infile)
with open('kp_data/new_names_dict.json','r') as infile:
    kp_names = json.load(infile)
preseason_length = 5

def betsy():
    for key,team in teams.items():
        team["prev_games"] = []
    run_preseason()
    for key,team in teams.items():
        for i in range(preseason_length):
            del team["games"][0]
    gamedate = date(2013,11,8)
    x = 0
    margins = {}
    diffs = {}
    data_list = []
    # Trying to iterate through all of the games chronologically
    while gamedate < date(2017,1,15):
        averages = get_averages()
        for key,team in teams.items():
            year = gamedate.year
            if gamedate.month > 8:
                year += 1
            if year != team["year"]:
                continue
            if len(team["games"]) == 0:
                continue
            game = game_dict[team["games"][0]]
            if game["date"] == str(gamedate):
                home = teams[game["home"]+game["season"]]
                away = teams[game["away"]+game["season"]]
                predicted = False
                for result in team["prev_games"]:
                    if game["key"] == result["key"]:
                        predicted = True
                        x+=1
                        break
                if predicted:
                    del team["games"][0]
                    continue

                home_dict = {}
                away_dict = {}
                team_list = [home,away]
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
                        d["adj_ortg"] /= round(1 + i + (i * (i + 1)) / 20,1)
                        d["adj_drtg"] /= round(1 + i + (i * (i + 1)) / 20,1)
                        d["adj_temp"] /= round(1 + i + (i * (i + 1)) / 20,1)
                for index,d in enumerate(dicts):
                    for key,value in d.items():
                        team_list[index][key].append(value)

                # Prediction
                home_em = round(home["adj_ortg"][-1] - home["adj_drtg"][-1],6)
                away_em = round(away["adj_ortg"][-1] - away["adj_drtg"][-1],6)
                tempo = round(averages["t"+game["season"]] + .74 * (home["adj_temp"][-1] - averages["t"+game["season"]]) + .74 * (away["adj_temp"][-1] - averages["t"+game["season"]]))
                em_diff = round((home_em - away_em) / 100,6)
                pmargin = round(em_diff * tempo,6)
                pmargin = round(.7233 * pmargin + .0077 * pmargin ** 2,6)
                if game["true_home_game"] == 1:
                    # Try without advantage
                    home_em += round(home["home_o_adv"] - home["home_d_adv"])
                    away_em += round(away["away_o_adv"] - away["away_d_adv"])
                    tempo = round(averages["t"+game["season"]] + home_tempo_factor * (home["adj_temp"][-1] - averages["t"+game["season"]]) + away_tempo_factor * (away["adj_temp"][-1] - averages["t"+game["season"]]))
                    em_diff = round((home_em - away_em) / 100)
                    pmargin = round(.8263 * em_diff * tempo - .7450)
                data = {}
                data["pmargin"] = pmargin
                data["margin"] = game["margin"]
                data["true_home_game"] = game["true_home_game"]
                data["neutral"] = abs(game["true_home_game"] - 1)
                try:
                    data["spread"] = game["spread"]
                except:
                    pass
                data_list.append(data)
                try:
                    if pmargin + game["spread"] >= 0:
                        game["pick"] = game["home"]
                    else:
                        game["pick"] = game["away"]
                except:
                    pass

                try:
                    margins[int(pmargin)].append(game["margin"])
                    diffs[int(pmargin)].append(pmargin - game["margin"])
                except:
                    margins[int(pmargin)] = [game["margin"]]
                    diffs[int(pmargin)] = [pmargin - game["margin"]]

                # Store results
                home_results = {}
                home_results["key"] = game["key"]
                home_results["adj_ortg"] = round(game["home_ORtg"] - away["adj_drtg"][-1] + averages["o"+game["season"]],6)
                home_results["adj_drtg"] = round(game["home_DRtg"] - away["adj_ortg"][-1] + averages["d"+game["season"]],6)
                home_results["adj_temp"] = round(game["Pace"] - away["adj_temp"][-1] + averages["t"+game["season"]],6)
                away_results = {}
                away_results["key"] = game["key"]
                away_results["adj_ortg"] = round(game["away_ORtg"] - home["adj_drtg"][-1] + averages["o"+game["season"]],6)
                away_results["adj_drtg"] = round(game["away_DRtg"] - home["adj_ortg"][-1] + averages["d"+game["season"]],6)
                away_results["adj_temp"] = round(game["Pace"] - home["adj_temp"][-1] + averages["t"+game["season"]],6)
                if game["true_home_game"] == 1:
                    home_results["adj_ortg"] -= round(home["home_o_adv"],6)
                    home_results["adj_drtg"] -= round(home["home_d_adv"],6)
                    away_results["adj_ortg"] -= round(away["away_o_adv"],6)
                    away_results["adj_drtg"] -= round(away["away_d_adv"],6)
                if game["key"] in home["games"]:
                    home["prev_games"].append(home_results)
                    if home["games"][0] == game["key"]:
                        del home["games"][0]
                if game["key"] in away["games"]:
                    away["prev_games"].append(away_results)
                    if away["games"][0] == game["key"]:
                        del away["games"][0]
        gamedate += timedelta(1)
    # for key in sorted(margins.keys()):
    #     data = {}
    #     data["pred"] = key
    #     data["margmed"] = np.median(margins[key])
    #     data["diffmed"] = np.median(diffs[key])
    #     data["diffav"] = np.mean(diffs[key])
    #     if len(margins[key]) < 20:
    #         continue
    #     # data_list.append(data)
    #     print(str(key).rjust(5),str(data["margmed"]).rjust(5),str(data["diffmed"]).rjust(15),str(len(margins[key])).rjust(6))
    # gamesdf = pd.DataFrame.from_dict(data_list)
    # reg = sm.ols(formula = "margin ~ pmargin",data=gamesdf,missing='drop').fit()
    # print(reg.summary())
    print(x)
def get_averages():
    averages = {}
    for key,team in teams.items():
        year = key[-4:]
        averages["o"+year] = round(averages.get("o"+year,0) + team["adj_ortg"][-1] / 351,6)
        averages["d"+year] = round(averages.get("d"+year,0) + team["adj_drtg"][-1] / 351,6)
        averages["t"+year] = round(averages.get("t"+year,0) + team["adj_temp"][-1] / 351,6)
    return averages

def run_preseason():
    if not check_chron():
        print("Preseason won't work")
    for key,team in teams.items():
        team["adj_ortg"] = []
        team["adj_drtg"] = []
        team["adj_temp"] = []
        game_list = team["games"]
        if len(game_list) < preseason_length:
            print(team+" doesn't have {} games in ".format(preseason_length)+key[-4:])
        for i in range(preseason_length):
            try:
                game = game_dict[game_list[i]]
                team["pre_adj_temp"] = round(game["Pace"] / preseason_length,6)
                if game["home"] == team["name"]:
                    if i == 0:
                        team["pre_adj_ortg"] = round(game["home_ORtg"] / preseason_length,6)
                        team["pre_adj_drtg"] = round(game["home_DRtg"] / preseason_length,6)
                    else:
                        team["pre_adj_ortg"] += round(game["home_ORtg"] / preseason_length,6)
                        team["pre_adj_drtg"] += round(game["home_DRtg"] / preseason_length,6)
                else:
                    if i == 0:
                        team["pre_adj_ortg"] = round(game["away_ORtg"] / preseason_length,6)
                        team["pre_adj_drtg"] = round(game["away_DRtg"] / preseason_length,6)
                    else:
                        team["pre_adj_ortg"] += round(game["away_ORtg"] / preseason_length,6)
                        team["pre_adj_drtg"] += round(game["away_DRtg"] / preseason_length,6)
            except:
                print(game)
    year_averages = {}
    for key,team in teams.items():
        year_averages["ortg"+key[-4:]] = round(year_averages.get("ortg"+key[-4:],0) + team["pre_adj_ortg"] / 351,6)
        year_averages["drtg"+key[-4:]] = round(year_averages.get("drtg"+key[-4:],0) + team["pre_adj_drtg"] / 351,6)
        year_averages["temp"+key[-4:]] = round(year_averages.get("temp"+key[-4:],0) + team["pre_adj_temp"] / 351,6)
    for key,team in teams.items():
        game_list = team["games"]
        for i in range(preseason_length):
            game = game_dict[game_list[i]]
            if game["home"] == team["name"]:
                team["pre_adj_ortg"] -= round((teams[game["away"]+key[-4:]]["pre_adj_drtg"] + teams[game["home"]+key[-4:]]["home_o_adv"]) / preseason_length,6)
                team["pre_adj_drtg"] -= round((teams[game["away"]+key[-4:]]["pre_adj_ortg"] + teams[game["home"]+key[-4:]]["home_d_adv"]) / preseason_length,6) # Positive drtg good, amount of points fewer they gave up than expected
                team["pre_adj_temp"] -= round(teams[game["away"]+key[-4:]]["pre_adj_temp"] / preseason_length,6)
            else:
                team["pre_adj_ortg"] -= round((teams[game["home"]+key[-4:]]["pre_adj_drtg"] + teams[game["away"]+key[-4:]]["away_o_adv"]) / preseason_length,6)
                team["pre_adj_drtg"] -= round((teams[game["home"]+key[-4:]]["pre_adj_ortg"] + teams[game["away"]+key[-4:]]["away_d_adv"]) / preseason_length,6) # Positive drtg good, amount of points fewer they gave up than expected
                team["pre_adj_temp"] -= round(teams[game["home"]+key[-4:]]["pre_adj_temp"] / preseason_length,6)
        team["pre_adj_ortg"] += round(year_averages["ortg"+key[-4:]],6)
        team["pre_adj_drtg"] += round(year_averages["drtg"+key[-4:]],6)
        team["pre_adj_temp"] += round(year_averages["temp"+key[-4:]],6)
        team["adj_ortg"].append(team["pre_adj_ortg"])
        team["adj_drtg"].append(team["pre_adj_drtg"])
        team["adj_temp"].append(team["pre_adj_temp"])

# Checks the chronological ordering of games in the game lists
def check_chron():
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

def margin_analysis():
    margins = {}
    diffs = {}
    for key,game in game_dict.items():
        home = teams[game["home"]+game["season"]]
        away = teams[game["away"]+game["season"]]
        home_em_adv = home["home_o_adv"] - home["home_d_adv"]
        away_em_adv = away["away_o_adv"] - away["away_d_adv"]
        game["em_diff"] = (home["kp_em"]  - away["kp_em"] + home_em_adv - away_em_adv) / 100
        game["tempo"] = kp_averages["kp_t"+game["season"]] + home_tempo_factor * (home["kp_t"] - kp_averages["kp_t"+game["season"]]) + away_tempo_factor * (away["kp_t"] - kp_averages["kp_t"+game["season"]])
        game["pmargin"] = game["em_diff"] * game["tempo"] - 3
        try:
            margins[game["pmargin"]//5].append(game["margin"])
            diffs[game["pmargin"]//5].append(game["pmargin"] - game["margin"])
        except:
            margins[game["pmargin"]//5] = [game["margin"]]
            diffs[game["pmargin"]//5] = [game["pmargin"] - game["margin"]]
    for key in sorted(margins.keys()):
        margmed = np.median(margins[key])
        diffmed = np.median(diffs[key])
        diffav = np.mean(diffs[key])
        if len(margins[key]) < 20:
            continue
        print(str(key*5).rjust(5),str(margmed).rjust(5),str(diffmed).rjust(15),str(len(margins[key])).rjust(6))
    spread_margins = {}
    spread_diffs = {}
    for key,game in spread_dict.items():
        try:
            spread_margins[game["spread"]//5].append(game["margin"])
            spread_diffs[game["spread"]//5].append(game["spread"] + game["margin"])
        except:
            spread_margins[game["spread"]//5] = [game["margin"]]
            spread_diffs[game["spread"]//5] = [game["spread"] + game["margin"]]
    for key in sorted(spread_margins.keys()):
        smargmed = np.median(spread_margins[key])
        sdiffmed = np.median(spread_diffs[key])
        if len(spread_margins[key]) < 20:
            continue
        print(str(key*5).rjust(5),str(smargmed).rjust(5),str(sdiffmed).rjust(15),str(len(spread_margins[key])).rjust(6))

def calc_home_tempo_factor():
    # games = []
    # for key,game in game_dict.items():
    #     games.append(game)
    # gamesdf = pd.DataFrame.from_dict(games)
    # gamesdf["home_tempo_diff"] = gamesdf.home_tempo - kp_averages["kp_t"]
    # gamesdf["away_tempo_diff"] = gamesdf.away_tempo - kp_averages["kp_t"]
    # gamesdf["pace_diff"] = gamesdf.Pace - kp_averages["kp_t"]
    # gamesdf["neutral"] = abs(gamesdf.true_home_game - 1)
    # result = sm.ols(formula = "pace_diff ~ home_tempo_diff:neutral + away_tempo_diff:neutral -1",data=gamesdf,missing='drop').fit()
    # print(result.summary())
    return (.7362,.7968)

def calc_home_advantage():
    espnset = set()
    for kp,espn in kp_names.items():
        espnset.add(espn)
    x = 0
    y = 0
    for name in espnset:
        home_o = []
        home_d = []
        away_o = []
        away_d = []
        home = False
        away = False
        for i in range(4):
            team = teams[name+str(2014+i)]
            for key in team["games"]:
                game = game_dict[key]
                try:
                    game["home_ORtg"]
                    game["away_ORtg"]
                    game["Pace"]
                    x += 1
                except:
                    y += 1
                    team["games"].remove(key)
                    continue
                if game["true_home_game"] == 1:
                    if game["home"] == name:
                        home = True
                        home_o.append(round(game["home_ORtg"]-teams[game["away"]+str(2014+i)]["kp_d"],1)) # How many more points per 100 possessions scored than an average team
                        home_d.append(round(game["home_DRtg"]-teams[game["away"]+str(2014+i)]["kp_o"],1)) # How many more points given up per...
                    else:
                        away = True
                        away_o.append(round(game["away_ORtg"]-teams[game["home"]+str(2014+i)]["kp_d"],1))
                        away_d.append(round(game["away_DRtg"]-teams[game["home"]+str(2014+i)]["kp_o"],1))
        if home:
            home_o_avg = np.median(home_o)
            home_d_avg = np.median(home_d)
        else:
            print("NO HOME GAMES",name)
        if away:
            away_o_avg = np.median(away_o)
            away_d_avg = np.median(away_d)
        else:
            print("NO ROAD GAMES",name)
        for i in range(4):
            team = teams[name+str(2014+i)]
            normalo = round(team["kp_o"] - kp_averages["kp_o"+str(2014+i)],6)
            normald = round(team["kp_d"] - kp_averages["kp_d"+str(2014+i)],6)
            team["home_o_adv"] = round(home_o_avg - normalo,6)
            team["home_d_adv"] = round(home_d_avg - normald,6)
            team["away_o_adv"] = round(away_o_avg - normalo,6)
            team["away_d_adv"] = round(away_d_avg - normald,6)
    print(x,y)

def calc_kp_averages():
    for key,team in teams.items():
        year = key[-4:]
        kp_averages["kp_o"+year] = round(kp_averages.get("kp_o"+year,0) + team["kp_o"] / 351,6)
        kp_averages["kp_d"+year] = round(kp_averages.get("kp_d"+year,0) + team["kp_o"] / 351,6)
        kp_averages["kp_t"+year] = round(kp_averages.get("kp_t"+year,0) + team["kp_t"] / 351,6)
        kp_averages["kp_o"] = round(kp_averages.get("kp_o",0) + team["kp_o"] / 1404,6)
        kp_averages["kp_d"] = round(kp_averages.get("kp_d",0) + team["kp_d"] / 1404,6)
        kp_averages["kp_t"] = round(kp_averages.get("kp_t",0) + team["kp_t"] / 1404,6)

def test_betsy():
    wins = 0
    total = 0
    profit = 0
    for key,game in game_dict.items():
        try:
            if game["pick"] == game["cover"]:
                profit += 1
                wins += 1
                total += 1
            elif game["cover"] == "Tie":
                pass
            else:
                profit -= 1.1
                total += 1
        except:
            pass
    print(profit,wins,total)

kp_averages = {}
calc_kp_averages()
home_tempo_factor, away_tempo_factor = calc_home_tempo_factor()
calc_home_advantage()
# margin_analysis()
betsy()
test_betsy()

# with open('new_teams.json','w') as outfile:
#     json.dump(teams,outfile)
# with open('new_game_dict.json','w') as outfile:
#     json.dump(game_dict,outfile)
# with open('spread_dict.json','w') as outfile:
#     json.dump(spread_dict,outfile)
