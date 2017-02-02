import numpy as np
import pandas as pd
import statsmodels.formula.api as sm
from datetime import date,timedelta
import json
from decimal import *

getcontext().prec = 10
getcontext().traps[FloatOperation] = True

# Teams dictionary: all teams since 2014, contains list of games, HCA values, etc
# Keyed by name+season
with open('new_teams.json','r') as infile:
    teams = json.load(infile)
# Game dictionary: all games between two D1 teams on ESPN since 2014, may contain advanced stats, may contain spread
# Keyed by str((home,away,date))
with open('new_game_dict.json','r') as infile:
    game_dict = json.load(infile)
with open('espn_data/names_dict.json','r') as infile:
    espn_names = json.load(infile)

# Number of games used to create starting stats for teams
preseason_length = 5

regress_games = []
new_games = []

def betsy():
    home_ortg_std_list = []
    away_ortg_std_list = []
    home_score_std_list = []
    away_score_std_list = []
    spread_std_list = []
    pmargin_std_list = []
    diff_std_list = []
    for key,team in teams.items():
        team["prev_games"] = []
    run_preseason()
    for key,team in teams.items():
        for i in range(preseason_length):
            del team["games"][0]
    for key,team in teams.items():
        team["variance"] = []
    gamedate = date(2011,11,1)
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


            # # Data collection for testing
            # h_proj_o = (home["adj_ortg"][-1] + away["adj_drtg"][-1]) / 2 + game["home_o"]
            # a_proj_o = (away["adj_ortg"][-1] + home["adj_drtg"][-1]) / 2 + game["home_o"]
            # try:
            #     home_ortg_std_list.append(h_proj_o - game["home_ORtg"])
            #     away_ortg_std_list.append(a_proj_o - game["away_ORtg"])
            #     home_score_std_list.append(h_proj_o * game["tempo"] / 100 - game["home_score"])
            #     away_score_std_list.append(a_proj_o * game["tempo"] / 100 - game["away_score"])
            #     spread_std_list.append(game["spread"] + game["margin"])
            #     pmargin_std_list.append(game["pmargin"] - game["margin"])
            #     diff_std_list.append(game["spread"] + game["pmargin"])
            # except:
            #     pass

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

    compare_strategies(data_list)

    print("Standard deviation of Home Offensive Rating prediction:".ljust(60),np.std(home_ortg_std_list))
    print("Standard deviation of Away Offensive Rating prediction:".ljust(60),np.std(away_ortg_std_list))
    print("Standard deviation of Home Score prediction:".ljust(60),np.std(home_score_std_list))
    print("Standard deviation of Away Score prediction:".ljust(60),np.std(away_score_std_list))
    print("Standard deviation of Scoring Margin prediction:".ljust(60),np.std(pmargin_std_list))
    print("Standard deviation of Scoring Margin and Spread:".ljust(60),np.std(spread_std_list))
    print("Standard deviation of Predicted Scoring Margin and Spread:".ljust(60),np.std(diff_std_list))

    # print(teams["The Citadel2017"])

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
    print(np.std(gamesdf.margin))
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
        if len(team["games"]) < preseason_length:
            print("{} doesn't have {} games in ".format(team,preseason_length)+key[-4:])

        # Get average of each stat for each team
        for i in range(preseason_length):
            game = game_dict[team["games"][i]]
            home = teams[game["home"]+game["season"]]
            away = teams[game["away"]+game["season"]]
            team["pre_adj_temp"] = team.get("pre_adj_temp",0) + game["Pace"] / preseason_length
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

def test_betsy():
    print("Testing")
    gamesdf = pd.DataFrame.from_dict(regress_games)
    print(len(gamesdf.spread))

    # Variables used in regression
    variables = ["spread","home_ats","away_ats"]
    temp_variables = ["home_em","away_em"]

    # Create formula string
    form = ""
    for var in variables:
        form += "{} + ".format(var)
    for var in temp_variables:
        form += "{}:tempo + ".format(var)
    form = form[:-2] + "-1"

    # Fit teams that covered the spread with the variables
    reg = sm.ols(formula = "home_cover ~ " + form,data=gamesdf,missing='drop').fit()
    print(reg.summary())
    for index,game in enumerate(regress_games):
        game["prob"] = reg.predict()[index]
        game["prob"] += .5
        if game["prob"] >= .5:
           game["pick"] = game["home"]
        else:
            game["pick"] = game["away"]
            game["prob"] = 1 - game["prob"]

    # Predict games that were not used in the regression
    for game in new_games:
        game["prob"] = 0
        for index,var in enumerate(variables):
            game["prob"] += reg.params[index] * game[var]
        for index,var in enumerate(temp_variables):
            game["prob"] += reg.params[index + len(variables)] * game[var] * game["tempo"]
        game["prob"] += .5
        if game["prob"] >= .5:
            game["pick"] = game["home"]
        else:
            game["pick"] = game["away"]
            game["prob"] = 1 - game["prob"]

    # Get the results
    wins = 0
    total = 0
    profit = 0
    for game in regress_games:
        if game["prob"] > .5:
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
        if game["prob"] > .5:
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

# Eliminates games that don't have Offensive Rating stats for both teams, or Pace
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

def get_overall_hca():
    home_o_adv = 0
    home_d_adv = 0
    away_o_adv = 0
    away_d_adv = 0
    for name in espn_names.keys():
        home_o_adv += teams[name+'2014']["home_o_adv"] / 351
        home_d_adv += teams[name+'2014']["home_d_adv"] / 351
        away_o_adv += teams[name+'2014']["away_o_adv"] / 351
        away_d_adv += teams[name+'2014']["away_d_adv"] / 351
    return [home_o_adv,home_d_adv,away_o_adv,away_d_adv]

eliminate_games_missing_data()
game_date_dict = get_game_date_dict()
betsy()
all_games = pd.read_csv('incremental_data.csv')
new_stats = []
new_game_dict = {}
for key, game in game_dict.items():
    try:
        game['home_adj_o']
        game['line_movement']
        game['home_public_percentage']
        csv_game = all_games.ix[all_games['team_home'] = game['home'] & all_games['date']=games['date']]
        new_game_dict[key] = game
        new_game_dict[key]['home_FTO'] = csv_game['home_FTO']
        new_game_dict[key]['away_FTO'] = csv_game['away_FTO']
        new_game_dict[key]['home_FTD'] = csv_game['home_FTD']
        new_game_dict[key]['away_FTD'] = csv_game['away_FTD']
        new_game_dict[key]['home_Three_O'] = csv_game['home_Three_O']
        new_game_dict[key]['away_Three_O'] = csv_game['away_Three_O']
        new_game_dict[key]['home_Three_D'] = csv_game['home_Three_D']
        new_game_dict[key]['away_Three_D'] = csv_game['away_Three_D']
        new_game_dict[key]['home_REBO'] = csv_game['home_REBO']
        new_game_dict[key]['away_REBO'] = csv_game['away_REBO']
        new_game_dict[key]['home_REBD'] = csv_game['home_REBD']
        new_game_dict[key]['away_REBD'] = csv_game['away_REBD']
        new_game_dict[key]['home_REB'] = csv_game['home_REB']
        new_game_dict[key]['away_REB'] = csv_game['away_REB']
        new_game_dict[key]['home_TOP'] = csv_game['home_TOP']
        new_game_dict[key]['away_TOP'] = csv_game['away_TOP']
        new_game_dict[key]['home_TOFP'] = csv_game['home_TOFP']
        new_game_dict[key]['away_TOFP'] = csv_game['away_TOFP']

#test_betsy()

#with open('new_teams.json','w') as outfile:
#    json.dump(teams,outfile)
with open('new_game_dict.json','w') as outfile:
   json.dump(new_game_dict,outfile)
