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

for key,team in teams.items():
    team["variance"] = []

regress_games = []

def betsy():
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
                    d["adj_ortg"] += result["adj_ortg"] * (1 + Decimal(str(.1)) * i)
                    d["adj_drtg"] += result["adj_drtg"] * (1 + Decimal(str(.1)) * i)
                    d["adj_temp"] += result["adj_temp"] * (1 + Decimal(str(.1)) * i)
                if len(team_list[index]["prev_games"]) > 0:
                    d["adj_ortg"] /= 1 + i + Decimal(str((i * (i + 1)) / 20))
                    d["adj_drtg"] /= 1 + i + Decimal(str((i * (i + 1)) / 20))
                    d["adj_temp"] /= 1 + i + Decimal(str((i * (i + 1)) / 20))
            for index,d in enumerate(dicts):
                for key,value in d.items():
                    team_list[index][key].append(value)
            if len(home["prev_games"]) > 0 and len(away["prev_games"]) > 0:
                game["home_variance"] = np.std(home["variance"])
                game["away_variance"] = np.std(away["variance"])
                game["std_range"] = game["home_variance"] + game["away_variance"]
            # Prediction
            home_em = home["adj_ortg"][-1] - home["adj_drtg"][-1]
            away_em = away["adj_ortg"][-1] - away["adj_drtg"][-1]
            tempo = (home["adj_temp"][-1] + away["adj_temp"][-1]) * Decimal(str(.75)) - averages["t"+game["season"]] * Decimal(str(.5))
            em_diff = (home_em - away_em) / 100
            pmargin = em_diff * tempo
            if game["true_home_game"] == 1:
                # Try without advantage
                home_em += Decimal(str(home["home_o_adv"]))
                away_em += Decimal(str(away["away_o_adv"]))
                em_diff = (home_em - away_em) / 100
                pmargin = em_diff * tempo
            pmargin *= Decimal(str(.75))
            game["em_diff"] = em_diff
            game["tempo"] = tempo
            data = {}
            data["pmargin"] = float(pmargin)
            data["margin"] = game["margin"]
            data["true_home_game"] = game["true_home_game"]
            data["neutral"] = abs(game["true_home_game"] - 1)
            try:
                data["spread"] = game["spread"]
            except:
                pass
            if game["true_home_game"] == 1:
                data_list.append(data)
                try:
                    margins[int(pmargin)].append(Decimal(str(game["margin"])))
                    diffs[int(pmargin)].append(pmargin - Decimal(str(game["margin"])))
                except:
                    margins[int(pmargin)] = [Decimal(str(game["margin"]))]
                    diffs[int(pmargin)] = [pmargin - Decimal(str(game["margin"]))]
            try:
                if len(home["prev_games"]) > 2 and len(away["prev_games"]) > 2:
                    if pmargin + Decimal(str(game["spread"])) >= 0:
                        game["vprob"] = (pmargin + Decimal(str(game["spread"]))) / (game["std_range"] * 2) + Decimal(str(.5))
                    else:
                        game["vprob"] = -1 * (pmargin + Decimal(str(game["spread"]))) / (game["std_range"] * 2) + Decimal(str(.5))
                game["fem_diff"] = float(game["em_diff"])
                game["ftempo"] = float(game["tempo"])
                game["home_ats"]
                game["away_ats"]
                game["line_movement"]
                regress_games.append(game)
            except:
                pass

            # Store results
            tempo_factor = (Decimal(str(game["Pace"])) + Decimal(str(.5)) * averages["t"+game["season"]]) / (Decimal(str(.75)) * (home["adj_temp"][-1] + away["adj_temp"][-1]))
            home_o = Decimal(str(home["home_o_adv"])) if game["true_home_game"] == 1 else 0
            away_o = Decimal(str(away["away_o_adv"])) if game["true_home_game"] == 1 else 0
            home_offense = (Decimal(str(game["home_ORtg"])) - home_o + averages["o"+game["season"]]) / (home["adj_ortg"][-1] + away["adj_drtg"][-1])
            away_offense = (Decimal(str(game["away_ORtg"])) - away_o + averages["o"+game["season"]]) / (away["adj_ortg"][-1] + home["adj_drtg"][-1])
            home_results = {}
            home_results["key"] = game["key"]
            home_results["adj_ortg"] = home_offense * home["adj_ortg"][-1]
            home_results["adj_drtg"] = away_offense * home["adj_drtg"][-1]
            home_results["adj_temp"] = tempo_factor * home["adj_temp"][-1]
            away_results = {}
            away_results["key"] = game["key"]
            away_results["adj_ortg"] = away_offense * away["adj_ortg"][-1]
            away_results["adj_drtg"] = home_offense * away["adj_drtg"][-1]
            away_results["adj_temp"] = tempo_factor * away["adj_temp"][-1]
            if game["key"] in home["games"]:
                home["prev_games"].append(home_results)
                if home["games"][0] == game["key"]:
                    home["variance"].append(Decimal(str(game["margin"])) - pmargin)
                    del home["games"][0]
            else:
                # Game in this teams preseason
                del home["adj_ortg"][-1]
                del home["adj_drtg"][-1]
                del home["adj_temp"][-1]
            if game["key"] in away["games"]:
                away["prev_games"].append(away_results)
                if away["games"][0] == game["key"]:
                    away["variance"].append(pmargin - Decimal(str(game["margin"])))
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
    # gamesdf = pd.DataFrame.from_dict(data_list)
    # reg = sm.ols(formula = "margin ~ pmargin",data=gamesdf,missing='drop').fit()
    # print(reg.summary())

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
            team["pre_adj_temp"] = team.get("pre_adj_temp",0) + Decimal(str(game["Pace"])) / preseason_length
            if game["home"] == team["name"]:
                team["pre_adj_ortg"] = team.get("pre_adj_ortg",0) + Decimal(str(game["home_ORtg"])) / preseason_length
                team["pre_adj_drtg"] = team.get("pre_adj_drtg",0) + Decimal(str(game["home_DRtg"])) / preseason_length
            else:
                team["pre_adj_ortg"] = team.get("pre_adj_ortg",0) + Decimal(str(game["away_ORtg"])) / preseason_length
                team["pre_adj_drtg"] = team.get("pre_adj_drtg",0) + Decimal(str(game["away_DRtg"])) / preseason_length
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
                home_o = Decimal(str(home["home_o_adv"])) if game["true_home_game"] == 1 else 0
                away_o = Decimal(str(away["away_o_adv"])) if game["true_home_game"] == 1 else 0
                home_off_factor = (Decimal(str(game["home_ORtg"])) - home_o + year_averages["ortg"+game["season"]]) / (home["adj_ortg"][-1] + away["adj_drtg"][-1])
                away_off_factor = (Decimal(str(game["away_ORtg"])) - away_o + year_averages["ortg"+game["season"]]) / (away["adj_ortg"][-1] + home["adj_drtg"][-1])
                tempo_factor = (Decimal(str(game["Pace"])) + Decimal(str(.5)) * year_averages["temp"+game["season"]]) / (Decimal(str(.75)) * (home["adj_temp"][-1] + away["adj_temp"][-1]))
                if game["home"] == team["name"]:
                    pre_adj_off += home_off_factor * home["adj_ortg"][-1] / preseason_length
                    pre_adj_def += away_off_factor * home["adj_drtg"][-1] / preseason_length # Positive drtg good, amount of points fewer they gave up than expected
                else:
                    pre_adj_off += away_off_factor * away["adj_ortg"][-1] / preseason_length
                    pre_adj_def += home_off_factor * away["adj_drtg"][-1] / preseason_length # Positive drtg good, amount of points fewer they gave up than expected
                pre_adj_tempo += tempo_factor * team["adj_temp"][-1] / preseason_length
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
        kp_averages["kp_o"+year] = kp_averages.get("kp_o"+year,0) + Decimal(str(team["kp_o"])) / 351
        kp_averages["kp_t"+year] = kp_averages.get("kp_t"+year,0) + Decimal(str(team["kp_t"])) / 351
        kp_averages["kp_o"] = kp_averages.get("kp_o",0) + Decimal(str(team["kp_o"])) / 1404
        kp_averages["kp_t"] = kp_averages.get("kp_t",0) + Decimal(str(team["kp_t"])) / 1404

def test_betsy():
    print("Testing")
    gamesdf = pd.DataFrame.from_dict(regress_games)
    print(len(gamesdf.spread))
    reg = sm.ols(formula = "home_cover ~ spread + fem_diff + home_ats + away_ats + line_movement + ftempo:spread -1",data=gamesdf,missing='drop').fit()
    print(reg.summary())
    for index,game in enumerate(regress_games):
        game["prob"] = reg.predict()[index]
        game["prob"] += .5
        if game["prob"] >= .5:
            game["pick"] = game["home"]
        else:
            game["pick"] = game["away"]
            game["prob"] = 1 - game["prob"]
    wins = 0
    total = 0
    profit = 0
    for game in regress_games:
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

def eliminate_stupid_games():
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
eliminate_stupid_games()
calc_kp_averages()
betsy()
test_betsy()

# with open('new_teams.json','w') as outfile:
#     json.dump(teams,outfile)
# with open('new_game_dict.json','w') as outfile:
#     json.dump(game_dict,outfile)
