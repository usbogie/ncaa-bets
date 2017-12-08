import helpers as h
import pandas as pd
import numpy as np
from organizers import add_features as af
import json
import csv
import os

this_season = h.this_season
path = h.path

def get(season=str(this_season)):
    print("Getting new games")
    data_path = os.path.join(path,'..','data','espn','upcoming_games.csv')
    gamesdf = pd.read_csv(data_path)
    upcoming_games = {}
    new_games = []
    new_over_games = []
    for i, row in gamesdf.iterrows():
        try:
            game = {}
            game["home"] = row.Game_Home.strip()
            game["away"] = row.Game_Away.strip()
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
            print("In ESPN, {} vs. {} failed".format(row.Game_Away,row.Game_Home))
            continue
    data_path = os.path.join(path,'..','data','vi','vegas_today.json')
    with open(data_path,'r') as infile:
        vegas_info = json.load(infile)
    for game in vegas_info:
        try:
            home = game['home']
            away = game['away']
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
            continue

    for game in new_games:
        home = h.teams[game["home"]+season]
        away = h.teams[game["away"]+season]

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

        FT_std,tPAr_std,TRBP_std,TOVP_std,opp_TOVP_std,FT_avg,tPAr_avg,TRBP_avg,TOVP_avg,opp_TOVP_avg = af.get_standard_deviations_averages(int(season))
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

        #print("Found:",game["home"],game["away"])
    if new_games:
        data_path = os.path.join(path,'..','data','composite','todays_games.csv')
        with open(data_path,'w') as outfile:
            keys = list(new_games[0].keys())
            writer = csv.DictWriter(outfile,fieldnames = keys)
            writer.writeheader()
            for game in new_games:
                writer.writerow(game)
    if new_over_games:
        data_path = os.path.join(path,'..','data','composite','todays_over_games.csv')
        with open(data_path,'w') as outfile:
            keys = list(new_over_games[0].keys())
            writer = csv.DictWriter(outfile,fieldnames = keys)
            writer.writeheader()
            for game in new_over_games:
                writer.writerow(game)
    print()
    