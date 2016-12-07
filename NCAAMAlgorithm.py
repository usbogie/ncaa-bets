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
        3D: %
        Rebound Margin
        Turnovers per possession
        Turnovers forced per possession
        Tipoff
        Total
        Home
        Weekend

    Scrape:
        Team: {
            kenpom.com:
                School
                Year
                KP Adjusted O
                KP Adjusted D
                KP Adjusted T
            ncaa.com:
                PPG
                FTM
                Fouls
                3FG per game
                3%
                Opponent 3FG%
                Rebound Differential
                Turnovers per game
                Turnovers forced per game
        }

        Old Game: {
            OddShark.com:
                Spread
                Total
            ESPN:
                Tipoff
                Day of week
                Home Team
                Away Team
                Home Score
                Away Score
                True Home Game?
        }

        New Game: {
            Sportsbook.ag:
                Spread
                Total
            ESPN:
                Tipoff
                Home Team
                Away Team
                True Home Game
        }

Strategy:
    Get database of games
    Regress data
    Predict spread
    Use probablity test to determine how likely a cover is
    Use this data on historical games and check performance
"""

"""
Get Database

Dictionaries
    teams: {
        name
        year
        kp_o
        kp_d
        kp_o_z
        kp_d_z
        kp_t
        ppg
        ftm
        fouls
        three_fg
        opp_3fg
        reb
        to
        tof

        fto (FTM / PPG)
        fto_z
        ftd (Fouls / KP Tempo)
        ftd_z
        three_o (3FGM * 3 / PPG)
        three_o_z
        three_d_z
        to_poss (TO per game / KP Tempo)
        tof_poss (TO forced per game/ KP Tempo)
        to_poss_z
        tof_poss_z
    }

    old_games: {
        spread
        total
        tipoff (1 early, 0 not)
        weekend (1 true, 0 false)
        true (1 true, 0 false)
        home
        away
        o
        d
        h_tempo
        a_tempo
        fto
        ftd
        three_o
        three_d
        reb
        to
        tof
        h_score
        a_score
        margin
        winner
        pick1
        pick2
        p_margin
        p_spread_margin
        correct (1 if pick and winner are equal, else 0)
        home_winner (1 if home team won, else 0)
        prob
        prob1
        prob2
        prob3
    }

    new_games: {
        spread
        total
        tipoff (1 early and true, 0 not)
        weekend (1 weekend and true, 0 false)
        true (1 true, 0 false)
        home
        away
        o
        d
        h_tempo
        a_tempo
        fto
        ftd
        three_o
        three_d
        reb
        to
        tof
        pick1
        pick2
        p_margin
        p_spread_margin
        prob
        prob1
        prob2
        prob3
    }
"""

teams = []
all_teams = []
new_teams = []
old_teams = []
old_games = []
new_games = []
all_games = []
parameters1 = []
parameters2 = []

import numpy as np
import pandas as pd

def get_old_teams():
    ncaa_2014 = pd.read_csv('NCAAM_2014.csv')
    ncaa_2015 = pd.read_csv('NCAAM_2015.csv')
    ncaa_2016 = pd.read_csv('NCAAM_2016.csv')
    old_years = [ncaa_2014,ncaa_2015,ncaa_2016]
    teams = []
    old_teams = []
    all_teams = []
    for i in range(len(old_years)):
        teams_count = len(old_years[i])
        teams.append([])
        for j in range(teams_count):
            teams[i].append({})
            all_teams.append(teams[i][j])
            old_teams.append(teams[i][j])
            teams[i][j]["name"] = old_years[i].Name[j]
            teams[i][j]["ppg"] = old_years[i].PPG[j]
            teams[i][j]["ftm"] = old_years[i].TPG[j]
            teams[i][j]["fouls"] = old_years[i].opp3[j]
            teams[i][j]["three_fg"] = old_years[i].FPG[j]
            teams[i][j]["opp_3fg"] = old_years[i].TOF[j]
            teams[i][j]["reb"] = old_years[i].TO[j]
            teams[i][j]["to"] = old_years[i].REB[j]
            teams[i][j]["tof"] = old_years[i].FTPG[j]
            teams[i][j]["perc3"] = old_years[i].perc3[j]

def set_team_attributes(team_type):
    team_list = all_teams
    if team_type == "old":
        team_list = teams
    elif team_type == "new":
        team_list = new_teams
    for team in team_list:
        team["fto"] = team["ftm"]/team["ppg"]
        team["ftd"] = team["fouls"]/team["kp_t"]
        team["three_o"] = team["three_fg"]*3/team["ppg"]
        team["to_poss"] = team["to"]/team["kp_t"]
        team["tof_poss"] = team["tof"]/team["kp_t"]

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
        game["d"] = home["kp_d_z"] + away["kp_o_z"]
        game["h_tempo"] = home["kp_t"]
        game["a_tempo"] = away["kp_t"]
        game["fto"] = 0
        if home["fto_z"] > 0:
            game["fto"] = home["fto_z"] + away["ftd_z"]
        game["ftd"] = 0
        if away["fto_z"] > 0:
            game["ftd"] = -1 * home["ftd_z"] + away["fto_z"]
        game["three_o"] = 0
        if home["three_o_z"] > 0:
            game["three_o"] = home["three_o_z"] * (home["perc3"] + away["three_d_z"])
        game["three_d"] = 0
        if away["three_o_z"] > 0:
            game["three_d"] = -1 * away["three_o_z"] * (away["perc3"] + home["three_d_z"])
        game["reb"] = home["reb"] - away["reb"]
        game["to"] = home["to_poss_z"] + away["tof_poss_z"]
        game["tof"] = -1 * home["tof_poss_z"] + away["to_poss_z"]


import statsmodels.formula.api as sm
def first_regression1():
    gamesdf = pd.DataFrame.from_dict(old_games)
    result = sm.ols(formula = "margin ~ o + d + h_tempo + a_tempo + fto + ftd + three_o + three_d + reb + to + tof + total + tipoff + true + weekend -1",data=gamesdf,missing='drop').fit()
    for i in range(len(result.params)):
        parameters1[i] = result.params[i]
    return (result,gamesdf)

from scipy.stats import norm
def regress_spread1(game,gamesdf,result):
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
    result2 = sm.ols(formula = "margin ~ game_o + game_d + game_h_tempo + game_a_tempo + game_fto + game_ftd + game_3o + game_3d + game_reb + game_to + game_tof + game_total + game_tipoff + game_true + game_weekend",data=gamesdf,missing='drop').fit()
    game["p_margin"] = result2.params[0]
    game["p_spread_margin"] = abs(result2.params[0] + game["spread"])
    if result2.params[0] + game["spread"] < 0:
        game["pick"] = game["away"]
    else:
        game["pick"] = game["home"]
    # Option 1 for probability
    residuals = gamesdf["margin"] - result.predict()
    SER = np.sqrt(sum(residuals*residuals)/len(old_games))
    se = np.sqrt(SER**2 + result2.bse[0]**2)
    game["prob1"] = norm.cdf(game["p_spread_margin"]/se)

    # Option 2 for probability, should be better
    gamesdf["game_advantage"] = gamesdf.p_spread_margin - game["p_spread_margin"]
    test2 = sm.ols(formula = "correct ~ game_advantage + game_advantage^2",data=gamesdf,missing='drop').fit()
    game["prob2"] = test2.params[0]

def set_retroactive_picks1(gamesdf,result):
    for game in old_games:
        regress_spread1(game,gamesdf,result)

def set_picks1(gamesdf,result):
    for game in new_games:
        regress_spread1(game,gamesdf,result)

def first_regression2():
    gamesdf = pd.DataFrame.from_dict(old_games)
    result = sm.ols(formula = "home_winner ~ spread + o + d + h_tempo + a_tempo + fto + ftd + three_o + three_d + reb + to + tof + total + tipoff + true + weekend -1",data=gamesdf,missing='drop').fit()
    for i in range(len(result.params)):
        parameters2[i] = result.params[i]
    return (result,gamesdf)

def regress_spread2(game,gamesdf,result):
    gamesdf["game_spread"] = gamesdf.spread - game["spread"]
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
    result2 = sm.ols(formula = "home_winner ~ game_spread + game_o + game_d + game_h_tempo + game_a_tempo + game_fto + game_ftd + game_3o + game_3d + game_reb + game_to + game_tof + game_total + game_tipoff + game_true + game_weekend",data=gamesdf,missing='drop').fit()
    prob = result2.params[0]
    if prob < .5:
        game["pick2"] = game["away"]
        game["prob3"] = 1 - prob
    else:
        game["pick2"] = game["home"]
        game["prob3"] = prob

def set_retroactive_picks2(gamesdf,result):
    for game in old_games:
        regress_spread2(game,gamesdf,result)

def set_picks2(gamesdf,result):
    for game in new_games:
        regress_spread2(game,gamesdf,result)

def test_strategy(level,regression, strat = 1):
    number_of_games = 0
    wins = 0
    prob = "prob1"
    pick = "pick" + regression
    if strat == 2:
        prob = "prob2"
    if regression == 2:
        prob = "prob3"
    for game in old_games:
        if game[prob] >= level:
            number_of_games += 1
            if game[pick] == game["winner"]:
                wins += 1

    percent = wins / number_of_games * 100
    s1 = "Regression, strategy " + regression + "/" + strat + " with probability level " + level + ", won " + percent + " percent of " + number_of_games + " games."
    profit = wins - 1.1 * (number_of_games - wins)
    s2 = "This would lead to a profit of " + profit + " units."
    print(s1)
    print(s2)

def print_picks(prob = .524):
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
                print(game["pick"]["name"],game["prob"])
"""
main:
teams
all_teams
old_teams
new_teams
old_games
new_games
all_games

get_old_teams()
set_team_attributes("all")
stat_list = ["kp_o","kp_d","fto","ftd","three_o","three_d","to_poss","tof_poss"]
for stat in stat_list:
    set_zscores(stat)
set_game_attributes()
parameters
result,gamesdf = first_regression1()
result2,gamesdf2 = first_regression2()
set_picks1(gamesdf,result)
set_retroactive_picks1(gamesdf,result)
set_picks2(gamesdf2,result2)
set_retroactive_picks2(gamesdf2,result2)
test_strategy(.55,1)
test_strategy(.55,1,2)
test_strategy(.55,2)
print_picks()
"""
