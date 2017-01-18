import numpy as np
import pandas as pd
import statsmodels.formula.api as sm
from datetime import date,timedelta
import json
from decimal import *
getcontext().prec = 10
getcontext().traps[FloatOperation] = True

with open('new_teams.json','r') as infile:
    teams = json.load(infile)
with open('new_game_dict.json','r') as infile:
    game_dict = json.load(infile)
with open('spread_dict.json','r') as infile:
    spread_dict = json.load(infile)
with open('kp_data/new_names_dict.json','r') as infile:
    kp_names = json.load(infile)
preseason_length = 5

game_date_dict = {}
for key,game in game_dict.items():
    try:
        if game["key"] not in game_date_dict[game["date"]]:
            game_date_dict[game["date"]].append(game["key"])
    except:
        game_date_dict[game["date"]] = [game["key"]]

for key,team in teams.items():
    team["variance"] = []

regress_games = []
new_games = []

def betsy():
    spread_std_list = []
    pmargin_std_list = []
    diff_std_list = []
    for key,team in teams.items():
        team["prev_games"] = []
    run_preseason()
    for key,team in teams.items():
        for i in range(preseason_length):
            del team["games"][0]
    gamedate = date(2013,11,8)
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
        for key in key_list:
            game = game_dict[key]
            try:
                game["home_ORtg"]
                game["away_ORtg"]
                game["Pace"]
            except:
                continue
            home = teams[game["home"]+game["season"]]
            away = teams[game["away"]+game["season"]]
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
            if len(home["prev_games"]) > 0 and len(away["prev_games"]) > 0:
                game["home_variance"] = np.std(home["variance"])
                game["away_variance"] = np.std(away["variance"])
                game["std_range"] = game["home_variance"] + game["away_variance"]

            # Prediction
            home_o = home["home_o_adv"] if game["true_home_game"] == 1 else 0
            away_o = away["away_o_adv"] if game["true_home_game"] == 1 else 0
            home_em = home["adj_ortg"][-1] - home["adj_drtg"][-1] + home_o
            away_em = away["adj_ortg"][-1] - away["adj_drtg"][-1] + away_o
            tempo = (home["adj_temp"][-1] + away["adj_temp"][-1]) / 2
            em_diff = (home_em - away_em) / 100
            pmargin = em_diff * tempo * .4
            game["em_diff"] = em_diff
            game["tempo"] = tempo
            game["pmargin"] = pmargin
            
            try:    
                spread_std_list.append(game["spread"] + game["margin"])
                pmargin_std_list.append(pmargin - game["margin"])
                diff_std_list.append(game["spread"] + pmargin)
            except:
                pass
            # Data collection for testing
            data = {}
            data["pmargin"] = float(pmargin)
            data["home_em"] = float(home_em) / 100
            data["away_em"] = float(away_em) / 100
            data["Pace"] = float(game["Pace"])
            data["home_adj_o"] = float(home["adj_ortg"][-1])
            data["home_adj_d"] = float(home["adj_drtg"][-1])
            data["away_adj_o"] = float(home["adj_ortg"][-1])
            data["away_adj_d"] = float(home["adj_drtg"][-1])
            data["home_proj_o"] = data["home_adj_o"] * .5 + data["away_adj_d"] * .5 + home_o
            data["away_proj_o"] = data["away_adj_o"] * .5 + data["home_adj_d"] * .5 + away_o
            data["home_o"] = game["home_ORtg"]
            data["away_o"] = game["away_ORtg"]
            data["home_adj_temp"] = float(home["adj_temp"][-1])
            data["away_adj_temp"] = float(away["adj_temp"][-1])
            data["home_temp_diff"] = float(home["adj_temp"][-1]) - float(averages["t"+game["season"]])
            data["away_temp_diff"] = float(away["adj_temp"][-1]) - float(averages["t"+game["season"]])
            data["Pace_diff"] = float(game["Pace"]) - float(averages["t"+game["season"]])
            data["avg_pace"] = float(averages["t"+game["season"]])
            data["margin"] = game["margin"]
            data["ptemp"] = game["tempo"]
            data["true_home_game"] = game["true_home_game"]
            data["neutral"] = abs(game["true_home_game"] - 1)
            try:
                data["spread"] = game["spread"]
                data_list.append(data)
            except:
                pass
            if game["true_home_game"] == 1:
                try:
                    margins[int(pmargin)].append(game["margin"])
                    diffs[int(pmargin)].append(pmargin - game["margin"])
                except:
                    margins[int(pmargin)] = [game["margin"]]
                    diffs[int(pmargin)] = [pmargin - game["margin"]]
            try:
                if len(home["prev_games"]) > 2 and len(away["prev_games"]) > 2:
                    if pmargin + game["spread"] >= 0:
                        game["vprob"] = (pmargin + game["spread"]) / (game["std_range"] * 2) + .5
                    else:
                        game["vprob"] = -1 * (pmargin + game["spread"]) / (game["std_range"] * 2) + .5
                game["fem_diff"] = float(game["em_diff"])
                game["home_em"] = float(home["adj_ortg"][-1]) - float(home["adj_drtg"][-1]) + home_o
                game["away_em"] = float(away["adj_ortg"][-1]) - float(away["adj_drtg"][-1]) + away_o
                game["home_ats"]
                game["away_ats"]
                if game["season"] != "2017":
                    regress_games.append(game)
                else:
                    new_games.append(game)
            except:
                pass

            # Store results
            home_results = {}
            home_results["key"] = game["key"]
            home_results["adj_ortg"] = 2 * game["home_ORtg"] - away["adj_drtg"][-1] - home_o
            home_results["adj_drtg"] = 2 * game["home_DRtg"] - away["adj_ortg"][-1] - away_o
            home_results["adj_temp"] = 2 * game["Pace"] - away["adj_temp"][-1]
            away_results = {}
            away_results["key"] = game["key"]
            away_results["adj_ortg"] = 2 * game["away_ORtg"] - home["adj_drtg"][-1] - home_o
            away_results["adj_drtg"] = 2 * game["away_DRtg"] - home["adj_ortg"][-1] - away_o
            away_results["adj_temp"] = 2 * game["Pace"] - home["adj_temp"][-1]
            if game["key"] in home["games"]:
                home["prev_games"].append(home_results)
                if home["games"][0] == game["key"]:
                    home["variance"].append(game["margin"] - pmargin)
                    del home["games"][0]
            else:
                # Game in this teams preseason
                del home["adj_ortg"][-1]
                del home["adj_drtg"][-1]
                del home["adj_temp"][-1]
            if game["key"] in away["games"]:
                away["prev_games"].append(away_results)
                if away["games"][0] == game["key"]:
                    away["variance"].append(pmargin - game["margin"])
                    del away["games"][0]
            else:
                # Game in this teams preseason
                del away["adj_ortg"][-1]
                del away["adj_drtg"][-1]
                del away["adj_temp"][-1]
        gamedate += timedelta(1)
    # for key in sorted(margins.keys()):
    #     data = {}
    #     data["pred"] = key
    #     data["margmed"] = np.median(margins[key])
    #     data["diffmed"] = np.median(diffs[key])
    #     data["count"] = len(margins[key])
    #     print(str(key).rjust(5),str(data["margmed"]).rjust(5),str(data["diffmed"]).rjust(15),str(len(margins[key])).rjust(6))
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
    # em_reg = sm.ols(formula = "margin ~ home_em:ptemp + away_em:ptemp -1",data=gamesdf,missing='drop').fit()
    # diff_list_em = []
    # for i in range(len(em_reg.predict())):
    #     diff_list_em.append(em_reg.predict()[i] - gamesdf.margin[i])
    # spread_reg = sm.ols(formula = "margin ~ spread -1",data=gamesdf,missing='drop').fit()
    # diff_list_sp = []
    # for i in range(len(spread_reg.predict())):
    #     diff_list_sp.append(spread_reg.predict()[i] - gamesdf.margin[i])
    # print(em_reg.summary())
    # print(spread_reg.summary())
    # print(np.std(diff_list_em))
    # print(np.std(diff_list_sp))
    print(np.std(pmargin_std_list))
    print(np.std(spread_std_list))
    print(np.std(diff_std_list))
    print(teams["Kentucky2015"]["adj_temp"][-1],teams["Villanova2015"]["adj_temp"][-1])

def get_averages(year):
    averages = {}
    for key,team in teams.items():
        team_year = key[-4:]
        if team_year != str(year):
            continue
        averages["o"+team_year] = averages.get("o"+team_year,0) + team["adj_ortg"][-1] / 351
        averages["t"+team_year] = averages.get("t"+team_year,0) + team["adj_temp"][-1] / 351
    return averages

def run_preseason():
    if not check_chron():
        print("Preseason won't work")
    for key,team in teams.items():
        team["adj_ortg"] = []
        team["adj_drtg"] = []
        team["adj_temp"] = []
        if len(team["games"]) < preseason_length:
            print(team+" doesn't have {} games in ".format(preseason_length)+key[-4:])
        for i in range(preseason_length):
            game = game_dict[team["games"][i]]
            home = teams[game["home"]+game["season"]]
            away = teams[game["away"]+game["season"]]
            team["pre_adj_temp"] = team.get("pre_adj_temp",0) + game["Pace"] / preseason_length
            if game["home"] == team["name"]:
                team["pre_adj_ortg"] = team.get("pre_adj_ortg",0) + game["home_ORtg"] / preseason_length
                team["pre_adj_drtg"] = team.get("pre_adj_drtg",0) + game["home_DRtg"] / preseason_length
            else:
                team["pre_adj_ortg"] = team.get("pre_adj_ortg",0) + game["away_ORtg"] / preseason_length
                team["pre_adj_drtg"] = team.get("pre_adj_drtg",0) + game["away_DRtg"] / preseason_length
        team["adj_ortg"].append(team["pre_adj_ortg"])
        team["adj_drtg"].append(team["pre_adj_drtg"])
        team["adj_temp"].append(team["pre_adj_temp"])
    year_averages = {}
    for key,team in teams.items():
        year_averages["ortg"+key[-4:]] = year_averages.get("ortg"+key[-4:],0) + team["adj_ortg"][-1] / 351
        year_averages["temp"+key[-4:]] = year_averages.get("temp"+key[-4:],0) + team["adj_temp"][-1] / 351
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
                home_o = home["home_o_adv"] if game["true_home_game"] == 1 else 0
                away_o = away["away_o_adv"] if game["true_home_game"] == 1 else 0
                if game["home"] == team["name"]:
                    pre_adj_off += (2 * game["home_ORtg"] - away["adj_drtg"][-1] - home_o) / preseason_length
                    pre_adj_def += (2 * game["home_DRtg"] - away["adj_ortg"][-1] - away_o) / preseason_length # Positive drtg good, amount of points fewer they gave up than expected
                    pre_adj_tempo += (2 * game["Pace"] - home["adj_temp"][-1]) / preseason_length
                else:
                    pre_adj_off += (2 * game["away_ORtg"] - home["adj_drtg"][-1] - away_o) / preseason_length
                    pre_adj_def += (2 * game["away_DRtg"] - home["adj_ortg"][-1] - home_o) / preseason_length # Positive drtg good, amount of points fewer they gave up than expected
                    pre_adj_tempo += (2 * game["Pace"] - home["adj_temp"][-1]) / preseason_length
            team["adj_ortg"].append(pre_adj_off)
            team["adj_drtg"].append(pre_adj_def)
            team["adj_temp"].append(pre_adj_tempo)
        #print(teams["Vanderbilt2014"]["adj_ortg"][-1],teams["Vanderbilt2014"]["adj_drtg"][-1],teams["Vanderbilt2014"]["adj_temp"][-1])
    team["pre_adj_ortg"] = team["adj_ortg"][-1]
    team["pre_adj_drtg"] = team["adj_drtg"][-1]
    team["pre_adj_temp"] = team["adj_temp"][-1]

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

def calc_kp_averages():
    for key,team in teams.items():
        year = key[-4:]
        kp_averages["kp_o"+year] = kp_averages.get("kp_o"+year,0) + team["kp_o"] / 351
        kp_averages["kp_t"+year] = kp_averages.get("kp_t"+year,0) + team["kp_t"] / 351
        kp_averages["kp_o"] = kp_averages.get("kp_o",0) + team["kp_o"] / 1404
        kp_averages["kp_t"] = kp_averages.get("kp_t",0) + team["kp_t"] / 1404

def test_betsy():
    print("Testing")
    gamesdf = pd.DataFrame.from_dict(regress_games)
    print(len(gamesdf.spread))
    variables = ["home_em","away_em"]
    temp_variables = ["true_home_game"]
    form = ""
    for var in variables:
        form += "{} + ".format(var)
    for var in temp_variables:
        form += "{}:tempo + ".format(var)
    form = form[:-2] + "-1"
    reg = sm.ols(formula = "margin ~ " + form,data=gamesdf,missing='drop').fit()
    print(reg.summary())
    for index,game in enumerate(regress_games):
        game["prob"] = reg.predict()[index]
        #game["prob"] += .5
        #if game["prob"] >= .5:
        if game["prob"] + game["spread"] >= 0:
           game["pick"] = game["home"]
        else:
            game["pick"] = game["away"]
            #game["prob"] = 1 - game["prob"]
    for game in new_games:
        game["prob"] = 0
        for index,var in enumerate(variables):
            game["prob"] += reg.params[index] * game[var]
        for index,var in enumerate(temp_variables):
            game["prob"] += reg.params[index + len(variables)] * game[var] * game["tempo"]
        #game["prob"] += .5
        if game["prob"] + game["spread"] >= 0:
            game["pick"] = game["home"]
        else:
            game["pick"] = game["away"]
            #game["prob"] = 1 - game["prob"]
    wins = 0
    total = 0
    profit = 0
    for game in regress_games:
        #if game["prob"] > .5:
        if game["pick"] == game["cover"]:
            profit += 1
            wins += 1
            total += 1
        elif game["cover"] == "Tie":
            pass
        else:
            profit -= Decimal('1.1')
            total += 1
    newwins = 0
    newtotal = 0
    newprofit = 0
    for game in new_games:
        #if game["prob"] > .5:
        if game["pick"] == game["cover"]:
            newprofit += 1
            newwins += 1
            newtotal += 1
        elif game["cover"] == "Tie":
            pass
        else:
            newprofit -= Decimal('1.1')
            newtotal += 1
    print(profit,wins,total)
    print(newprofit,newwins,newtotal)

def eliminate_games_missing_data():
    for key,team in teams.items():
        for key in team["games"]:
            game = game_dict[key]
            try:
                game["home_ORtg"]
                game["away_ORtg"]
                game["Pace"]
            except:
                team["games"].remove(key)


kp_averages = {}
eliminate_games_missing_data()
calc_kp_averages()
betsy()
#test_betsy()

#with open('new_teams.json','w') as outfile:
#    json.dump(teams,outfile)
#with open('new_game_dict.json','w') as outfile:
#    json.dump(game_dict,outfile)
