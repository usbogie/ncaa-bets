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

def betsy():
    for key,team in teams.items():
        team["prev_games"] = []
    run_preseason()
    for key,team in teams.items():
        for i in range(preseason_length):
            del team["games"][0]
    gamedate = date(2013,11,8)
    x = 0
    y = 0
    margins = {}
    diffs = {}
    data_list = []
    # Trying to iterate through all of the games chronologically
    year_list = []
    while gamedate < date.today():
        try:
            key_list = game_date_dict[str(gamedate)]
        except:
            gamedate += timedelta(1)
            continue
        year = gamedate.year
        if gamedate.month > 8:
            year += 1
        if year not in year_list:
            year_list.append(year)
            print(year)
            print("==================================")
        print(gamedate,len(key_list))
        averages = get_averages(year)
        for key in key_list:
            game = game_dict[key]
            home = teams[game["home"]+game["season"]]
            away = teams[game["away"]+game["season"]]
            team_list = [home,away]
            try:
                home_regseason = True if home["games"][0] == game["key"] else False
                away_regseason = True if away["games"][0] == game["key"] else False
            except:
                y += 1
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
                    d["adj_ortg"] += result["adj_ortg"] * Decimal(str(1 + .1 * i))
                    d["adj_drtg"] += result["adj_drtg"] * Decimal(str(1 + .1 * i))
                    d["adj_temp"] += result["adj_temp"] * Decimal(str(1 + .1 * i))
                if len(team_list[index]["prev_games"]) > 0:
                    d["adj_ortg"] /= Decimal(str(1 + i + (i * (i + 1)) / 20))
                    d["adj_drtg"] /= Decimal(str(1 + i + (i * (i + 1)) / 20))
                    d["adj_temp"] /= Decimal(str(1 + i + (i * (i + 1)) / 20))
            for index,d in enumerate(dicts):
                for key,value in d.items():
                    team_list[index][key].append(value)

            # Prediction
            home_em = home["adj_ortg"][-1] - home["adj_drtg"][-1]
            away_em = away["adj_ortg"][-1] - away["adj_drtg"][-1]
            tempo = averages["t"+game["season"]] + Decimal('74') * (home["adj_temp"][-1] - averages["t"+game["season"]]) + Decimal('.74') * (away["adj_temp"][-1] - averages["t"+game["season"]])
            em_diff = (home_em - away_em) / 100
            pmargin = em_diff * tempo
            if game["true_home_game"] == 1:
                # Try without advantage
                home_em += home["home_o_adv"] - home["home_d_adv"]
                away_em += away["away_o_adv"] - away["away_d_adv"]
                tempo = averages["t"+game["season"]] + home_tempo_factor * (home["adj_temp"][-1] - averages["t"+game["season"]]) + away_tempo_factor * (away["adj_temp"][-1] - averages["t"+game["season"]])
                em_diff = (home_em - away_em) / 100
                pmargin = em_diff * tempo
            data = {}
            data["pmargin"] = pmargin
            data["margin"] = Decimal(str(game["margin"]))
            data["true_home_game"] = game["true_home_game"]
            data["neutral"] = abs(game["true_home_game"] - 1)
            try:
                data["spread"] = Decimal(str(game["spread"]))
            except:
                pass
            data_list.append(data)
            try:
                if pmargin + Decimal(str(game["spread"])) >= 0:
                    game["pick"] = game["home"]
                else:
                    game["pick"] = game["away"]
            except:
                pass

            try:
                margins[int(pmargin)].append(Decimal(str(game["margin"])))
                diffs[int(pmargin)].append(pmargin - Decimal(str(game["margin"])))
            except:
                margins[int(pmargin)] = [Decimal(str(game["margin"]))]
                diffs[int(pmargin)] = [pmargin - Decimal(str(game["margin"]))]

            # Store results
            home_results = {}
            home_results["key"] = game["key"]
            home_results["adj_ortg"] = Decimal(str(game["home_ORtg"])) - away["adj_drtg"][-1] + averages["o"+game["season"]]
            home_results["adj_drtg"] = Decimal(str(game["home_DRtg"])) - away["adj_ortg"][-1] + averages["d"+game["season"]]
            home_results["adj_temp"] = Decimal(str(game["Pace"])) - away["adj_temp"][-1] + averages["t"+game["season"]]
            away_results = {}
            away_results["key"] = game["key"]
            away_results["adj_ortg"] = Decimal(str(game["away_ORtg"])) - home["adj_drtg"][-1] + averages["o"+game["season"]]
            away_results["adj_drtg"] = Decimal(str(game["away_DRtg"])) - home["adj_ortg"][-1] + averages["d"+game["season"]]
            away_results["adj_temp"] = Decimal(str(game["Pace"])) - home["adj_temp"][-1] + averages["t"+game["season"]]
            if game["true_home_game"] == 1:
                home_results["adj_ortg"] -= home["home_o_adv"]
                home_results["adj_drtg"] -= home["home_d_adv"]
                away_results["adj_ortg"] -= away["away_o_adv"]
                away_results["adj_drtg"] -= away["away_d_adv"]
            if game["key"] in home["games"]:
                home["prev_games"].append(home_results)
                if home["games"][0] == game["key"]:
                    del home["games"][0]
                else:
                    x += 1
            else:
                # Game in this teams preseason
                del home["adj_ortg"][-1]
                del home["adj_drtg"][-1]
                del home["adj_temp"][-1]
            if game["key"] in away["games"]:
                away["prev_games"].append(away_results)
                if away["games"][0] == game["key"]:
                    del away["games"][0]
                else:
                    x += 1
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
    #     data["diffav"] = np.mean(diffs[key])
    #     if len(margins[key]) < 20:
    #         continue
    #     # data_list.append(data)
    #     print(str(key).rjust(5),str(data["margmed"]).rjust(5),str(data["diffmed"]).rjust(15),str(len(margins[key])).rjust(6))
    # gamesdf = pd.DataFrame.from_dict(data_list)
    # reg = sm.ols(formula = "margin ~ pmargin",data=gamesdf,missing='drop').fit()
    # print(reg.summary())
    print(x,y)
def get_averages(year):
    averages = {}
    for key,team in teams.items():
        team_year = key[-4:]
        if team_year != str(year):
            continue
        averages["o"+team_year] = averages.get("o"+team_year,0) + team["adj_ortg"][-1] / 351
        averages["d"+team_year] = averages.get("d"+team_year,0) + team["adj_drtg"][-1] / 351
        averages["t"+team_year] = averages.get("t"+team_year,0) + team["adj_temp"][-1] / 351
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
                team["pre_adj_temp"] = Decimal(str(game["Pace"])) / preseason_length
                if game["home"] == team["name"]:
                    if i == 0:
                        team["pre_adj_ortg"] = Decimal(str(game["home_ORtg"])) / preseason_length
                        team["pre_adj_drtg"] = Decimal(str(game["home_DRtg"])) / preseason_length
                    else:
                        team["pre_adj_ortg"] += Decimal(str(game["home_ORtg"])) / preseason_length
                        team["pre_adj_drtg"] += Decimal(str(game["home_DRtg"])) / preseason_length
                else:
                    if i == 0:
                        team["pre_adj_ortg"] = Decimal(str(game["away_ORtg"])) / preseason_length
                        team["pre_adj_drtg"] = Decimal(str(game["away_DRtg"])) / preseason_length
                    else:
                        team["pre_adj_ortg"] += Decimal(str(game["away_ORtg"])) / preseason_length
                        team["pre_adj_drtg"] += Decimal(str(game["away_DRtg"])) / preseason_length
            except:
                print(game)
    year_averages = {}
    for key,team in teams.items():
        year_averages["ortg"+key[-4:]] = year_averages.get("ortg"+key[-4:],0) + team["pre_adj_ortg"] / 351
        year_averages["drtg"+key[-4:]] = year_averages.get("drtg"+key[-4:],0) + team["pre_adj_drtg"] / 351
        year_averages["temp"+key[-4:]] = year_averages.get("temp"+key[-4:],0) + team["pre_adj_temp"] / 351
    for key,team in teams.items():
        game_list = team["games"]
        for i in range(preseason_length):
            game = game_dict[game_list[i]]
            if game["home"] == team["name"]:
                team["pre_adj_ortg"] -= (teams[game["away"]+key[-4:]]["pre_adj_drtg"] + teams[game["home"]+key[-4:]]["home_o_adv"]) / preseason_length
                team["pre_adj_drtg"] -= (teams[game["away"]+key[-4:]]["pre_adj_ortg"] + teams[game["home"]+key[-4:]]["home_d_adv"]) / preseason_length # Positive drtg good, amount of points fewer they gave up than expected
                team["pre_adj_temp"] -= teams[game["away"]+key[-4:]]["pre_adj_temp"] / preseason_length
            else:
                team["pre_adj_ortg"] -= (teams[game["home"]+key[-4:]]["pre_adj_drtg"] + teams[game["away"]+key[-4:]]["away_o_adv"]) / preseason_length
                team["pre_adj_drtg"] -= (teams[game["home"]+key[-4:]]["pre_adj_ortg"] + teams[game["away"]+key[-4:]]["away_d_adv"]) / preseason_length # Positive drtg good, amount of points fewer they gave up than expected
                team["pre_adj_temp"] -= teams[game["home"]+key[-4:]]["pre_adj_temp"] / preseason_length
        team["pre_adj_ortg"] += year_averages["ortg"+key[-4:]]
        team["pre_adj_drtg"] += year_averages["drtg"+key[-4:]]
        team["pre_adj_temp"] += year_averages["temp"+key[-4:]]
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
    return (Decimal('.7362'),Decimal('.7968'))

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
                        home_o.append(Decimal(str(game["home_ORtg"]))-Decimal(str(teams[game["away"]+str(2014+i)]["kp_d"]))) # How many more points per 100 possessions scored than an average team
                        home_d.append(Decimal(str(game["home_DRtg"]))-Decimal(str(teams[game["away"]+str(2014+i)]["kp_o"]))) # How many more points given up per...
                    else:
                        away = True
                        away_o.append(Decimal(str(game["away_ORtg"]))-Decimal(str(teams[game["home"]+str(2014+i)]["kp_d"])))
                        away_d.append(Decimal(str(game["away_DRtg"]))-Decimal(str(teams[game["home"]+str(2014+i)]["kp_o"])))
        if home:
            home_o_avg = Decimal(str(np.median(home_o)))
            home_d_avg = Decimal(str(np.median(home_d)))
        else:
            print("NO HOME GAMES",name)
        if away:
            away_o_avg = Decimal(str(np.median(away_o)))
            away_d_avg = Decimal(str(np.median(away_d)))
        else:
            print("NO ROAD GAMES",name)
        for i in range(4):
            team = teams[name+str(2014+i)]
            normalo = Decimal(str(team["kp_o"])) - kp_averages["kp_o"+str(2014+i)]
            normald = Decimal(str(team["kp_d"])) - kp_averages["kp_d"+str(2014+i)]
            team["home_o_adv"] = home_o_avg - normalo
            team["home_d_adv"] = home_d_avg - normald
            team["away_o_adv"] = away_o_avg - normalo
            team["away_d_adv"] = away_d_avg - normald
    print(x,y)

def calc_kp_averages():
    for key,team in teams.items():
        year = key[-4:]
        kp_averages["kp_o"+year] = kp_averages.get("kp_o"+year,0) + Decimal(str(team["kp_o"])) / 351
        kp_averages["kp_d"+year] = kp_averages.get("kp_d"+year,0) + Decimal(str(team["kp_o"])) / 351
        kp_averages["kp_t"+year] = kp_averages.get("kp_t"+year,0) + Decimal(str(team["kp_t"])) / 351
        kp_averages["kp_o"] = kp_averages.get("kp_o",0) + Decimal(str(team["kp_o"])) / 1404
        kp_averages["kp_d"] = kp_averages.get("kp_d",0) + Decimal(str(team["kp_d"])) / 1404
        kp_averages["kp_t"] = kp_averages.get("kp_t",0) + Decimal(str(team["kp_t"])) / 1404

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
                profit -= Decimal('1.1')
                total += 1
        except:
            pass
    print(profit,wins,total)

kp_averages = {}
calc_kp_averages()
home_tempo_factor, away_tempo_factor = calc_home_tempo_factor()
calc_home_advantage()
betsy()
test_betsy()

# with open('new_teams.json','w') as outfile:
#     json.dump(teams,outfile)
# with open('new_game_dict.json','w') as outfile:
#     json.dump(game_dict,outfile)
# with open('spread_dict.json','w') as outfile:
#     json.dump(spread_dict,outfile)
