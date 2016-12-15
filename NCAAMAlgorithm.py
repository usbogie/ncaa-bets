"""
Objective:
    Report the favorable spreads

Variables:
    Regression:
        Adjusted Offense KP
        Adjusted Defense KP
        Adjusted Tempo KP
        FTO: points as a percentage of points scored
        FTD: FTA per possession
        3O: points as a percentage of points scored
        3O%
        3D%
        REBO: offensive rebound percentage
        REBD: defensive rebound percentage
        Turnovers per offensive play
        Turnovers forced per offensive play
        Tipoff
        Total
        Home
        Weekend

    Scrape:
        Team: {
            KenPom:
                KP Adjusted O
                KP Adjusted D
                KP Adjusted T
            TeamRankings:
                FTperc (percent of points from ft)
                OFTAPP
                3perc (percent of points from 3)
                3%
                Opponent 3FG%
                O Rebound percentage
                D Rebound percentage
                Turnovers per play
                Turnovers forced per play
        }

        Old Game: {
            OddShark:
                Spread
                Total
            ESPN:
                Tipoff
                Day of week
                True Home Game
                Home Team
                Away Team
                Home Score
                Away Score
        }

        New Game: {
            Sportsbook:
                Spread
                Total
            ESPN:
                Tipoff
                Day of week
                True Home Game
                Home Team
                Away Team
        }
"""

"""
Get Database

Dictionaries
    teams: {
        name
        year
        kp_o
        kp_d
        kp_t
        three_o
        perc3
        three_d
        rebo
        rebd
        to
        tof

        kp_o_z
        kp_d_z
        fto_z
        ftd_z
        three_o_z
        perc3_z
        three_d_z
        rebo_z
        rebd_z
        to_poss_z
        tof_poss_z
    }

    old_games: {
        game_type ("new" or "old")
        home
        away

        spread
        total
        tipoff (1 early and true, 0 not)
        weekend (1 weekend and true, 0 false)
        true (1 true, 0 false)
        o
        d
        h_tempo
        a_tempo
        fto
        ftd
        three_o
        three_d
        rebo
        rebd
        to
        tof

        pick1
        pick2
        p_margin
        p_spread_margin
        prob1
        prob2
        prob3

        h_score
        a_score
        margin
        winner
        home_winner (1 if home team won, else 0)
        correct (1 if pick and winner are equal, else 0)
    }

    new_games: {
        game_type ("new" or "old")
        home
        away
        spread
        total
        tipoff (1 early and true, 0 not)
        weekend (1 weekend and true, 0 false)
        true (1 true, 0 false)
        o
        d
        h_tempo
        a_tempo
        fto
        ftd
        three_o
        three_d
        rebo
        rebd
        to
        tof

        pick1
        pick2
        p_margin
        p_spread_margin
        prob1
        prob2
        prob3
    }
"""

teams = []
all_teams = []
old_teams = []
new_teams = []
all_games = []
old_games = []
new_games = []
parameters1 = []
parameters2 = []

import numpy as np
import pandas as pd

def get_team_stats():
    ncaa_2014 = pd.read_csv('NCAAM_2014.csv')
    ncaa_2015 = pd.read_csv('NCAAM_2015.csv')
    ncaa_2016 = pd.read_csv('NCAAM_2016.csv')
    ncaa_2017 = pd.read_csv('NCAAM_2017.csv')
    years = [ncaa_2014,ncaa_2015,ncaa_2016,ncaa_2017]
    teams = []
    for i in range(len(years)):
        teams_count = len(years[i])
        teams.append([])
        for j in range(teams_count):
            teams[i].append({})
            all_teams.append(teams[i][j])
            if i < (len(years) - 1):
                old_teams.append(teams[i][j])
                teams[i][j]["game_type"] = "old"
            else:
                new_teams.append(teams[i][j])
                teams[i][j]["game_type"] = "new"
            teams[i][j]["name"] = years[i].Name[j]
            teams[i][j]["year"] = i + 2014
            teams[i][j]["fto"] = years[i].FTO[j]
            teams[i][j]["ftd"] = years[i].FTD[j]
            teams[i][j]["three_o"] = years[i].Three_O[j]
            teams[i][j]["perc3"] = years[i].perc3[j]
            teams[i][j]["three_d"] = years[i].Three_D[j]
            teams[i][j]["rebo"] = years[i].REBO[j]
            teams[i][j]["rebd"] = years[i].REBD[j]
            teams[i][j]["to_poss"] = years[i].TOP[j]
            teams[i][j]["tof_poss"] = years[i].TOFP[j]

def update_team_stats():
    ncaa_2017 = pd.read_csv('NCAAM_2017.csv')
    i = len(teams)-1
    for j in range(len(teams[i])):
        teams[i][j]["fto"] = ncaa_2017[i].FTO[j]
        teams[i][j]["ftd"] = ncaa_2017[i].FTD[j]
        teams[i][j]["three_o"] = ncaa_2017[i].Three_O[j]
        teams[i][j]["perc3"] = ncaa_2017[i].perc3[j]
        teams[i][j]["three_d"] = ncaa_2017[i].Three_D[j]
        teams[i][j]["rebo"] = ncaa_2017[i].REBO[j]
        teams[i][j]["rebd"] = ncaa_2017[i].REBD[j]
        teams[i][j]["to_poss"] = ncaa_2017[i].TOP[j]
        teams[i][j]["tof_poss"] = ncaa_2017[i].TOFP[j]
    set_team_attributes()

def set_team_attributes():
    stat_list = ["kp_o","kp_d","fto","ftd","three_o","perc3","three_d","rebo","rebd","to_poss","tof_poss"]
    for stat in stat_list:
        set_zscores(stat)

from scipy.stats.mstats import zscore
def set_zscores(stat):
    l = []
    for team in all_teams:
        l.append(team[stat])
    z = zscore(l)
    i=0
    stat_z = stat + "_z"
    for team in all_teams:
        team[stat_z] = z[i]
        i += 1

def set_game_attributes():
    for game in all_games:
        home = game["home"]
        away = game["away"]
        game["o"] = home["kp_o_z"] + away["kp_d_z"]
        game["d"] = -1 * (home["kp_d_z"] + away["kp_o_z"])
        game["h_tempo"] = home["kp_t"]
        game["a_tempo"] = away["kp_t"]
        game["fto"] = 0
        if home["fto_z"] > 0:
            game["fto"] = home["fto_z"] + away["ftd_z"]
        game["ftd"] = 0
        if away["fto_z"] > 0:
            game["ftd"] = -1 * (home["ftd_z"] + away["fto_z"])
        game["three_o"] = 0
        if home["three_o_z"] > 0:
            game["three_o"] = home["three_o_z"] * (home["perc3_z"] + away["three_d_z"])
        game["three_d"] = 0
        if away["three_o_z"] > 0:
            game["three_d"] = -1 * away["three_o_z"] * (away["perc3_z"] + home["three_d_z"])
        game["rebo"] = home["rebo_z"] - away["rebd_z"]
        game["rebd"] = home["rebd_z"] - away["rebo_z"]
        game["to"] = -1 * (home["to_poss_z"] + away["tof_poss_z"])
        game["tof"] = home["tof_poss_z"] + away["to_poss_z"]


import statsmodels.formula.api as sm
def regress_margin():
    gamesdf = pd.DataFrame.from_dict(old_games)
    result = sm.ols(formula = "margin ~ o + d + h_tempo + a_tempo + fto + ftd + three_o + three_d + rebo + rebd + to + tof + total + tipoff + true + weekend -1",data=gamesdf,missing='drop').fit()
    for i in range(len(result.params)):
        parameters1[i] = result.params[i]
    i = 0
    for old_game in old_games:
        old_game["p_spread_margin"] = abs(result.predict()[i] + old_game["spread"])
    predictions1 = result.predict()
    return gamesdf

from scipy.stats import norm
def predict_spread(game,gamesdf):
    gamesdf["game_o"] = gamesdf.o - game["o"]
    gamesdf["game_d"] = gamesdf.d - game["d"]
    gamesdf["game_h_tempo"] = gamesdf.h_tempo - game["h_tempo"]
    gamesdf["game_a_tempo"] = gamesdf.a_tempo - game["a_tempo"]
    gamesdf["game_fto"] = gamesdf.fto - game["fto"]
    gamesdf["game_ftd"] = gamesdf.ftd - game["ftd"]
    gamesdf["game_3o"] = gamesdf.three_o - game["three_o"]
    gamesdf["game_3d"] = gamesdf.three_d - game["three_d"]
    gamesdf["game_reb"] = gamesdf.reb - game["reb"]
    gamesdf["game_to"] = gamesdf.to - game["to"]
    gamesdf["game_tof"] = gamesdf.tof - game["tof"]
    gamesdf["game_tipoff"] = gamesdf.tipoff - game["tipoff"]
    gamesdf["game_total"] = gamesdf.total - game["total"]
    gamesdf["game_true"] = gamesdf.true - game["true"]
    gamesdf["game_weekend"] = gamesdf.weekend - game["weekend"]
    result2 = sm.ols(formula = "margin ~ game_o + game_d + game_h_tempo + game_a_tempo + game_fto + game_ftd + game_3o + game_3d + game_rebo + game_rebd + game_to + game_tof + game_total + game_tipoff + game_true + game_weekend",data=gamesdf,missing='drop').fit()
    game["p_margin"] = result2.params[0]
    game["p_spread_margin"] = abs(result2.params[0] + game["spread"])
    if result2.params[0] + game["spread"] < 0:
        game["pick1"] = game["away"]
    else:
        game["pick1"] = game["home"]

    # Get Prob 1
    residuals = gamesdf["margin"] - predictions1
    SER = np.sqrt(sum(residuals*residuals)/len(old_games))
    se = np.sqrt(SER**2 + result2.bse[0]**2)
    game["prob1"] = norm.cdf(game["p_spread_margin"]/se)

def set_prob2(game,gamesdf):
    gamesdf["game_advantage"] = gamesdf.p_spread_margin - game["p_spread_margin"]
    test2 = sm.ols(formula = "correct ~ game_advantage + game_advantage^2",data=gamesdf,missing='drop').fit()
    game["prob2"] = test2.params[0]

def set_picks(gamesdf):
    for game in all_games:
        predict_spread(game,gamesdf)
        if game["game_type"] == "old":
            if game["pick1"] == game["winner"]:
                game["correct"] = 1
            else:
                game["correct"] = 0
    for game in all_games:
        set_prob2(game,gamesdf)

def regress_winners():
    gamesdf = pd.DataFrame.from_dict(old_games)
    result = sm.ols(formula = "home_winner ~ spread + o + d + h_tempo + a_tempo + fto + ftd + three_o + three_d + rebo + rebd + to + tof + total + tipoff + true + weekend -1",data=gamesdf,missing='drop').fit()
    for i in range(len(result.params)):
        parameters2[i] = result.params[i]
    i = 0
    for game in old_games:
        prob = result.predict()[i]
        i += 1
        if prob < .5:
            game["pick2"] = game["away"]
            game["prob3"] = 1 - prob
        else:
            game["pick2"] = game["home"]
            game["prob3"] = prob

def predict_new_games():
    variables = ["spread","o","d","h_tempo","a_tempo","fto","ftd","three_o","three_d","rebo","rebd","to","tof","tipoff","total","true","weekend"]
    for game in new_games:
        prob = parameters2[0]
        for i in range(1,len(parameters2)):
            for var in variables:
                prob += parameters2[i] * game[var]
        if prob < .5:
            game["pick2"] = game["away"]
            game["prob3"] = 1 - prob
        else:
            game["pick2"] = game["home"]
            game["prob3"] = prob

def test_strategy(level = .55,strat):
    number_of_games = 0
    wins = 0
    prob = "prob" + strat
    pick = "pick" + (strat + 1) / 2
    for game in old_games:
        if game[prob] >= level:
            number_of_games += 1
            if game[pick] == game["winner"]:
                wins += 1

    percent = wins / number_of_games * 100
    s1 = "Strategy " + strat + " with probability level " + level + ", won " + percent + " percent of " + number_of_games + " games."
    profit = wins - 1.1 * (number_of_games - wins)
    s2 = "This would lead to a profit of " + profit + " units."
    print(s1)
    print(s2)

def print_picks(prob = .6):
    prob_list_b = []
    for game in new_games:
        if game["prob"] > prob:
            prob_list_b.append(game["prob"])
    np.sort(prob_list_b)
    prob_list = []
    for i in range(len(prob_list_b)):
        prob_list.append(prob_list_b[len(prob_list_b)-i-1])
    for p in prob_list:
        for game in new_games:
            if p == game["prob"]:
                print(game["pick1"]["name"],game["prob"])
"""
main:
teams = []
all_teams = []
old_teams = []
new_teams = []
all_games = []
old_games = []
new_games = []
parameters1 = []
parameters2 = []
predictions1 = []

get_team_stats()
set_team_attributes()
set_game_attributes()

// Strategies 1 and 2
gamesdf = regress_margin()
set_picks(gamesdf)

// Strategy 3
regress_winners()
predict_new_games()

test_strategy(1)
test_strategy(2)
test_strategy(3)
"""
