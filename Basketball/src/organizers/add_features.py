import csv
import numpy as np
from datetime import date,timedelta
import os
import math
import helpers as h
import pandas as pd
from scrapers.shared import make_season

path = h.path
this_season = h.this_season
num_teams = 351
preseason_length = 4
over_games = []

def run(year_list):
    print("Adding features")
    gamesdf = pd.DataFrame()
    saved_years = sorted(list(set(range(h.first_season, this_season + 1)) - set(year_list)))
    if saved_years:
        gamesdf = pd.concat([h.gamesdf.ix[h.gamesdf['season']==year] for year in saved_years])
    game_list = []
    home_ortg_std_list = []
    away_ortg_std_list = []
    home_score_std_list = []
    away_score_std_list = []
    spread_std_list = []
    pmargin_std_list = []
    diff_std_list = []
    home_count = []
    pred_margin_count = []
    game_date_dict = get_game_date_dict()
    sort_games()
    eliminate_games_missing_data()
    correct = 0
    for key,team in h.teams.items():
        team["prev_games"] = []
    run_preseason()
    for key,team in h.teams.items():
        game_count = min(preseason_length, len(team["games"]))
        for i in range(game_count):
            del team["games"][0]
    margins = {}
    diffs = {}
    data_list = []
    # Trying to iterate through all of the games chronologically
    averages = {}
    for year in year_list:
        print(year)
        dates = make_season(year)
        for d in dates:
            d_list = list(map(int,d.split('-')))
            gamedate = date(d_list[0],d_list[1],d_list[2])
            if gamedate >= date.today():
                break
            try:
                game_keys = game_date_dict[str(gamedate)]
            except:
                if gamedate == date.fromordinal(date.today().toordinal()-1):
                    print("No games from yesterday.")
                continue
            FT_std,tPAr_std,TRBP_std,TOVP_std,opp_TOVP_std,FT_avg,tPAr_avg,TRBP_avg,TOVP_avg,opp_TOVP_avg = get_standard_deviations_averages(year)
            for key in game_keys:
                game = h.game_dict[key]
                try:
                    game["home_ORtg"]
                    game["away_ORtg"]
                    game["Pace"]
                except:
                    continue
                try:
                    home = h.teams[game["home"]+str(game["season"])]
                    away = h.teams[game["away"]+str(game["season"])]
                except:
                    continue
                team_list = [home,away]
                if not game["key"] in home["games"] + away["games"]:
                    continue
                elif game["key"] in home["games"] and game["key"] != home["games"][0]:
                    raise()
                elif game["key"] in away["games"] and game["key"] != away["games"][0]:
                    raise()
                home_dict = {}
                away_dict = {}
                dicts = [home_dict,away_dict]
                # Update stats
                for index,d in enumerate(dicts):
                    d["adj_ortg"] = team_list[index]["pre_adj_ortg"]
                    d["adj_drtg"] = team_list[index]["pre_adj_drtg"]
                    d["adj_temp"] = team_list[index]["pre_adj_temp"]
                    i = 0
                    weights = 1
                    weight = 1
                    for result in team_list[index]["prev_games"]:
                        i += 1
                        weight *= 1.15
                        d["adj_ortg"] += result["adj_ortg"] * weight
                        d["adj_drtg"] += result["adj_drtg"] * weight
                        d["adj_temp"] += result["adj_temp"] * weight
                        weights += weight
                    if len(team_list[index]["prev_games"]) > 0:
                        d["adj_ortg"] /= weights
                        d["adj_drtg"] /= weights
                        d["adj_temp"] /= weights
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
                game["away_o"] = -2 if game["true_home_game"] == 1 else 0
                game["home_em"] = home["adj_ortg"][-1] - home["adj_drtg"][-1]
                game["away_em"] = away["adj_ortg"][-1] - away["adj_drtg"][-1]
                game["tempo"] = (home["adj_temp"][-1] + away["adj_temp"][-1]) / 2
                game["em_diff"] = (4 * game["home_o"] + game["home_em"] - game["away_em"]) / 100
                game["pmargin"] = game["em_diff"] * game["tempo"] * .5
                game["home_portg"] = game["home_o"] + .5 * (home["adj_ortg"][-1] + away["adj_drtg"][-1])
                game["away_portg"] = game["away_o"] + .5 * (away["adj_ortg"][-1] + home["adj_drtg"][-1])
                game["ptotal"] = round((game["home_portg"] + game["away_portg"]) / 100 * game["tempo"])
                if game["pmargin"] > 0 and game["pmargin"] <= 6:
                    game["pmargin"] += 1
                if game["pmargin"] < 0 and game["pmargin"] >= -6:
                    game["pmargin"] -= 1
                game["pmargin"] *= .8
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
                a_proj_o = (away["adj_ortg"][-1] + home["adj_drtg"][-1]) / 2 + game["away_o"]
                try:
                    home_ortg_std_list.append(h_proj_o - game["home_ORtg"])
                    away_ortg_std_list.append(a_proj_o - game["away_ORtg"])
                    home_score_std_list.append(h_proj_o * game["tempo"] / 100 - game["home_score"])
                    away_score_std_list.append(a_proj_o * game["tempo"] / 100 - game["away_score"])
                    spread_std_list.append(game["spread"] + game["margin"])
                    pmargin_std_list.append(game["pmargin"] - game["margin"])
                    diff_std_list.append(abs(game["pmargin"] + game["spread"]))
                    home_count.append(game["pmargin"] / game["margin"] > 0)
                    if game["spread"] != 0 and game["pmargin"] + game["spread"] != 0 and game["spread"] + game["margin"] != 0:
                        pred_margin_count.append((game["pmargin"] + game["spread"]) / (game["margin"] + game["spread"]) > 0)

                except:
                    pass

                data = {}
                data["pmargin"] = game["pmargin"]
                data["home_em"] = game["home_em"]
                data["away_em"] = game["away_em"]
                data["Pace"] = game["Pace"]
                data["home_portg"] = game["home_portg"]
                data["away_portg"] = game["away_portg"]
                data["home_o"] = game["home_ORtg"]
                data["away_o"] = game["away_ORtg"]
                data["home_temp"] = home["adj_temp"][-1]
                data["away_temp"] = away["adj_temp"][-1]
                data["margin"] = game["margin"]
                data["ptemp"] = game["tempo"]
                data["true_home_game"] = game["true_home_game"]
                data["neutral"] = 1 - game["true_home_game"]
                data_list.append(data)
                try:
                    margins[game["pmargin"] // 5].append(game["margin"])
                    diffs[game["pmargin"] // 5].append(game["pmargin"] - game["margin"])
                except:
                    margins[game["pmargin"] // 5] = [game["margin"]]
                    diffs[game["pmargin"] // 5] = [game["pmargin"] - game["margin"]]

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
                home_results["adj_drtg"] = game["home_DRtg"] - away_o_diff - game["away_o"]
                home_results["adj_temp"] = game["Pace"] + temp_diff
                away_results = {}
                away_results["key"] = game["key"]
                away_results["adj_ortg"] = game["away_ORtg"] + away_o_diff - game["away_o"]
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
    '''
    for key in sorted(margins.keys()):
        data = {}
        data["pred"] = key
        data["margmed"] = np.median(margins[key])
        data["diffmed"] = np.median(diffs[key])
        data["count"] = len(margins[key])
        print(str(key * 5).rjust(5),str(data["margmed"]).rjust(5),str(data["diffmed"]).rjust(15),str(len(margins[key])).rjust(6))

    print("Standard deviation of Home Offensive Rating prediction:".ljust(60),np.std(home_ortg_std_list))
    print("Standard deviation of Away Offensive Rating prediction:".ljust(60),np.std(away_ortg_std_list))
    print("Standard deviation of Home Score prediction:".ljust(60),np.std(home_score_std_list))
    print("Standard deviation of Away Score prediction:".ljust(60),np.std(away_score_std_list))
    print("Standard deviation of Scoring Margin prediction:".ljust(60),np.std(pmargin_std_list))
    print("Standard deviation of Scoring Margin and Spread:".ljust(60),np.std(spread_std_list))
    print("Standard deviation of Predicted Scoring Margin and Spread:".ljust(60),np.std(diff_std_list))
    print("Home count:",len(home_count),len([i for i in home_count if i])/len(home_count))
    print("Predicted Margin count:",len(pred_margin_count),len([i for i in pred_margin_count if i])/len(pred_margin_count))
    print("Ties:",correct)
    '''
    print()
    try:
        gamesdf = pd.concat([gamesdf, pd.DataFrame(game_list)],ignore_index=True).set_index('key')
    except:
        gamesdf = pd.DataFrame(game_list)
    save(gamesdf)

def get_standard_deviations_averages(year):
    FT_list = []
    tPAr_list = []
    TRBP_list = []
    TOVP_list = []
    opp_TOVP_list = []
    for key,team in h.teams.items():
        if team["year"] == year:
            FT_list.append(np.mean(team["FT"]))
            tPAr_list.append(np.mean(team["tPAr"]))
            TRBP_list.append(np.mean(team["TRBP"]))
            TOVP_list.append(np.mean(team["TOVP"]))
            opp_TOVP_list.append(np.mean(team["opp_TOVP"]))
    return (np.std(FT_list),np.std(tPAr_list),np.std(TRBP_list),np.std(TOVP_list),np.std(opp_TOVP_list),np.mean(FT_list),np.mean(tPAr_list),np.mean(TRBP_list),np.mean(TOVP_list),np.mean(opp_TOVP_list))

# Get averages for a certain point in the year
# Used in "kenpom" style computations for comparison
def get_averages(year):
    averages = {}
    for key,team in h.teams.items():
        team_year = key[-4:]
        if team_year != str(year):
            continue
        averages["o"+team_year] = averages.get("o"+team_year,0) + team["adj_ortg"][-1] / num_teams
        averages["t"+team_year] = averages.get("t"+team_year,0) + team["adj_temp"][-1] / num_teams
    return averages

# Gets starting stats for a team in the year
# These games will not be predicted
def run_preseason():
    for key,team in h.teams.items():
        team["adj_ortg"] = []
        team["adj_drtg"] = []
        team["adj_temp"] = []
        team["FT"] = []
        team["tPAr"] = []
        team["TRBP"] = []
        team["TOVP"] = []
        team["opp_TOVP"] = []
        team["over_rec"] = [0,0]
        game_count = min(len(team["games"]), preseason_length)
        if not game_count:
            continue
        if len(team["games"]) < preseason_length:
            print("{} doesn't have {} games in ".format(team["name"],preseason_length)+key[-4:])
        # Get average of each stat for each team
        for i in range(game_count):
            game = h.game_dict[team["games"][i]]
            home = h.teams[game["home"]+str(game["season"])]
            away = h.teams[game["away"]+str(game["season"])]
            team["pre_adj_temp"] = team.get("pre_adj_temp",0) + game["Pace"] / game_count
            try:
                team["over_rec"][0] += 1 if game["over"] == .5 else 0
                team["over_rec"][1] += 1 if game["over"] == -.5 else 0
            except:
                pass
            if game["home"] == team["name"]:
                team["pre_adj_ortg"] = team.get("pre_adj_ortg",0) + game["home_ORtg"] / game_count
                team["pre_adj_drtg"] = team.get("pre_adj_drtg",0) + game["home_DRtg"] / game_count
                team["FT"].append(game["home_FT"])
                team["tPAr"].append(game["home_tPAr"])
                team["TRBP"].append(game["home_TRBP"])
                team["TOVP"].append(game["home_TOVP"])
                team["opp_TOVP"].append(game["away_TOVP"])
            else:
                team["pre_adj_ortg"] = team.get("pre_adj_ortg",0) + game["away_ORtg"] / game_count
                team["pre_adj_drtg"] = team.get("pre_adj_drtg",0) + game["away_DRtg"] / game_count
                team["FT"].append(game["away_FT"])
                team["tPAr"].append(game["away_tPAr"])
                team["TRBP"].append(game["away_TRBP"])
                team["TOVP"].append(game["away_TOVP"])
                team["opp_TOVP"].append(game["home_TOVP"])
        # Averages will be initial stats before we level them off
        team["adj_ortg"].append(team["pre_adj_ortg"])
        team["adj_drtg"].append(team["pre_adj_drtg"])
        team["adj_temp"].append(team["pre_adj_temp"])

    # Run five times to try to level off each h.teams's stats to correct values
    for j in range(5):
        for key,team in h.teams.items():
            p_game_list = team["games"]
            game_count = min(preseason_length, len(team["games"]))
            if not game_count:
                continue
            pre_adj_off = 0
            pre_adj_def = 0
            pre_adj_tempo = 0
            for i in range(game_count):
                game = h.game_dict[p_game_list[i]]
                home = h.teams[game["home"]+str(game["season"])]
                away = h.teams[game["away"]+str(game["season"])]
                # Home court advantage values taken into account only if true home game
                home_o = 3 if game["true_home_game"] == 1 else 0
                away_o = 2 if game["true_home_game"] == 1 else 0
                home_o_diff = (home["pre_adj_ortg"] - away["pre_adj_drtg"]) / 2
                away_o_diff = (away["pre_adj_ortg"] - home["pre_adj_drtg"]) / 2
                temp_diff = (home["pre_adj_temp"] - away["pre_adj_temp"]) / 2
                # Best predictor of Ratings and Pace is an average of the two, so must reverse calculate a team's adjusted rating for the game
                if game["home"] == team["name"]:
                    pre_adj_off += (game["home_ORtg"] + home_o_diff - home_o) / game_count
                    pre_adj_def += (game["home_DRtg"] - away_o_diff + away_o) / game_count # Positive drtg good, amount of points fewer they gave up than expected
                    pre_adj_tempo += (game["Pace"] + temp_diff) / game_count
                else:
                    pre_adj_off += (game["away_ORtg"] + away_o_diff + away_o) / game_count
                    pre_adj_def += (game["away_DRtg"] - home_o_diff - home_o) / game_count # Positive drtg good, amount of points fewer they gave up than expected
                    pre_adj_tempo += (game["Pace"] - temp_diff) / game_count
            team["adj_ortg"].append(pre_adj_off)
            team["adj_drtg"].append(pre_adj_def)
            team["adj_temp"].append(pre_adj_tempo)
        for key,team in h.teams.items():
            try:
                team["pre_adj_ortg"] = team["adj_ortg"][-1]
                team["pre_adj_drtg"] = team["adj_drtg"][-1]
                team["pre_adj_temp"] = team["adj_temp"][-1]
            except:
                continue

def sort_games():
    for key in h.teams.keys():
        h.teams[key]["games"] = sorted(h.teams[key]["games"],key=lambda g:g.split(", ")[-1])

# Eliminates games that don't have Offensive Rating stats for both h.teams, or Pace
def eliminate_games_missing_data():
    keys_to_remove = set()
    for key,team in h.teams.items():
        for key in team["games"]:
            game = h.game_dict[key]
            try:
                dummy1 = game["home_ORtg"]
                dummy2 = game["away_ORtg"]
                dummy3 = game["Pace"]
            except:
                keys_to_remove.add(key)
    for key in keys_to_remove:
        game = h.game_dict[key]
        h.teams[game["home"]+str(game["season"])]["games"].remove(key)
        h.teams[game["away"]+str(game["season"])]["games"].remove(key)

# Creates game dictionary that facilitates getting games played on the same date
def get_game_date_dict():
    game_date_dict = {}
    for key,game in h.game_dict.items():
        try:
            if game["key"] not in game_date_dict[game["date"]]:
                game_date_dict[game["date"]].append(game["key"])
        except:
            game_date_dict[game["date"]] = [game["key"]]
    return game_date_dict

def save(games):
    h.gamesdf = games
    games.to_csv(h.games_path)
