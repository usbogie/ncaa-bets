"""
Objective:
    Report the favorable spreads

Variables:
    Regression:
        Adjusted Offense KP
        Adjusted Defense KP
        KP Tempo
        FTO: points as a percentage of points scored
        FTD: FTA per possession
        3O: points as a percentage of points scored
        3D: %
        Rebound Differential
        Turnovers per possession
        Turnovers forced per possession
        Tipoff
        Total
        Home

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
        kp_t
        ppg
        ftm
        fouls
        3fg
        opp_3fg
        reb
        to
        tof

        fto (FTM / PPG)
        fto_z
        ftd (Fouls / KP Tempo)
        ftd_z
        3o (3FGM * 3 / PPG)
        3o_z
        3d_z
        to_poss (TO per game / KP Tempo)
        tof_poss (TO forced per game/ KP Tempo)
    }

    old_games: {
        spread
        total
        tipoff (1 early, 0 not)
        weekend (1 true, 0 false)
        true (1 true, 0 false)
        home
        away
        off
        def
        h_tempo
        a_tempo
        fto
        ftd
        3o
        3d
        reb
        to
        tof
        h_score
        a_score
        margin
        winner
        pick
        p_margin
        p_spread_margin
        correct (1 if pick and winner are equal, else 0)
        prob
        prob1
        prob2
    }

    new_games: {
        spread
        total
        tipoff (1 early, 0 not)
        weekend (1 true, 0 false)
        true (1 true, 0 false)
        home
        away
        off
        def
        h_tempo
        a_tempo
        fto
        ftd
        3o
        3d
        reb
        to
        tof
        pick
        p_margin
        p_spread_margin
        prob
        prob1
        prob2
    }
"""

old_teams = []
old_games = []
new_teams = []
new_games = []
all_teams = []

import numpy as np
import pandas as pd

def get_database():
    # Get team info (old_teams, new_teams)
    # Get old game info
    # Get new game info
    # old

def get_old_teams():
    ncaa_2014 = pd.read_csv('NCAAM_2014.csv')
    ncaa_2015 = pd.read_csv('NCAAM_2015.csv')
    ncaa_2016 = pd.read_csv('NCAAM_2016.csv')
    old_years = []
    old_years.append([ncaa_2014,ncaa_2015,ncaa_2016])
    for i in range(len(old_years)):
        teams = len(old_years[i])
        for j in range(teams):
            old_teams[j+teams*i]["name"] = old_years[i].Name[j]
            old_teams[j+teams*i]["year"] = i + 2014
            old_teams[j+teams*i]["ppg"] = old_years[i].PPG[j]
            old_teams[j+teams*i]["ftm"] = old_years[i].3PG[j]
            old_teams[j+teams*i]["fouls"] = old_years[i].opp3[j]
            old_teams[j+teams*i]["3fg"] = old_years[i].FPG[j]
            old_teams[j+teams*i]["opp_3fg"] = old_years[i].TOF[j]
            old_teams[j+teams*i]["reb"] = old_years[i].TO[j]
            old_teams[j+teams*i]["to"] = old_years[i].REB[j]
            old_teams[j+teams*i]["tof"] = old_years[i].FTPG[j]

def set_team_attributes(team_type):
    team_list = all_teams
    if team_type == "old":
        team_list = old_teams
    elif team_type == "new":
        team_list = new_teams
    for team in team_list:
        team["fto"] = team["ftm"]/team["ppg"]
        team["ftd"] = team["fouls"]/team["kp_t"]
        team["3o"] = team["3fg"]*3/team["ppg"]
        team["to_poss"] = team["to"]/team["kp_t"]
        team["tof_poss"] = team["tof"]/team["kp_t"]

from scipy.stats.mstats import zscore
def set_zscores():
    fto_list = []
    ftd_list = []
    3o_list = []
    3d_list = []
    for team in all_teams:
        fto_list.append(team["fto"])
        ftd_list.append(team["ftd"])
        3o_list.append(team["3o"])
        3d_list.append(team["3d"])
    fto_z = npzscore(fto_list)
    ftd_z = zscore(ftd_list)
    3o_z = zscore(3o_list)
    3d_z = zscore(3d_list)
    i=0
    for team in all_teams:
        team["fto_z"] = fto_z[i]
        team["ftd_z"] = -1 * ftd_z[i]
        team["3o_z"] = 3o_z[i]
        team["3d_z"] = -1 * 3d_z[i]
        i += 1

def set_game_attributes():
    for game in all_games:
        game["off"] = game["home"]["kp_o"] - game["away"]["kp_d"]
        game["def"] = game["home"]["kp_d"] - game["away"]["kp_o"]
        game["h_tempo"] = game["home"]["kp_t"]
        game["a_tempo"] = game["away"]["kp_t"]
        game["fto"] = game["home"]["fto_z"] - game["away"]["ftd_z"]
        game["ftd"] = game["home"]["ftd_z"] - game["away"]["fto_z"]
        game["3o"] = game["home"]["3o_z"] - game["away"]["3d_z"]
        game["3d"] = game["home"]["3d_z"] - game["away"]["3o_z"]
        game["reb"] = game["home"]["reb"] - game["away"]["reb"]
        game["to"] = game["home"]["to_poss"] - game["away"]["tof_poss"]
        game["tof"] = game["home"]["tof_poss"] - game["away"]["to_poss"]

import statsmodels.formula.api as sm
def first_regression():
    gamesdf = pd.DataFrame.from_dict(old_games)
    result = sm.ols(formula = "margin ~ off + def + h_tempo + a_tempo + fto + ftd + 3o + 3d + reb + to + tof + total + tipoff + true + weekend -1",data=gamesdf,missing='drop').fit()
    for i in range(len(result.params)):
        parameters[i] = result.params[i]
    return (result,gamesdf)

from scipy.stats.norm import cdf
def regress_spread(game,gamesdf,result):
    gamesdf["game_off"] = gamesdf.off - game["off"]
    gamesdf["game_def"] = gamesdf.def - game["def"]
    gamesdf["game_tempo"] = gamesdf.tempo - game["tempo"]
    gamesdf["game_fto"] = gamesdf.fto - game["fto"]
    gamesdf["game_ftd"] = gamesdf.ftd - game["ftd"]
    gamesdf["game_3o"] = gamesdf.3o - game["3o"]
    gamesdf["game_3d"] = gamesdf.3d - game["3d"]
    gamesdf["game_reb"] = gamesdf.reb - game["reb"]
    gamesdf["game_to"] = gamesdf.to - game["to"]
    gamesdf["game_tof"] = gamesdf.tof - game["tof"]
    gamesdf["game_tipoff"] = gamesdf.tipoff - game["tipoff"]
    gamesdf["game_total"] = gamesdf.total - game["total"]
    gamesdf["game_true"] = gamesdf.true - game["true"]
    gamesdf["game_weekend"] = gamesdf.weekend - game["weekend"]
    result2 = sm.ols(formula = "margin ~ game_off + game_def + game_h_tempo + game_a_tempo + game_fto + game_ftd + game_3o + game_3d + game_reb + game_to + game_tof + game_total + game_tipoff + game_true + game_weekend",data=gamesdf,missing='drop').fit()
    game["p_margin"] = result2.params[0]
    game["p_spread_margin"] = abs(result2.params[0] + game["spread"])
    if result2.params[0] + game["spread"] < 0:
        game["pick"] = game["away"]
    else:
        game["pick"] = game["home"]
    # Option 1 for probability
    residuals = gamesdf["margin"] - result.predict()
    SER = np.sqrt(sum(residuals*residuals)/len(game_list))
    se = np.sqrt(SER**2 + result2.bse[0]**2)
    game["prob1"] = game["p_spread_margin"]/se

    # Option 2 for probability
    gamesdf["game_advantage"] = gamesdf.p_spread_margin - game["p_spread_margin"]
    test2 = sm.ols(formular = "correct ~ game_advantage + game_advantage^2",data=gamesdf,missing='drop').fit()
    game["prob2"] = test2.params[0]

def set_retroactive_picks():
    for game in old_games:
        regress_spread(game)

def set_picks():
    for game in new_games:
        regress_spread(game)

def test_strategy(level,strat):
    number_of_games = 0
    wins = 0
    prob = game["prob1"]
    if strat == 2:
        prob = game["prob2"]
    for game in old_games:
        if prob >= level:
            number_of_games += 1
            if game["pick"] == game["winner"]:
                wins += 1

    percent = wins / number_of_games * 100
    s1 = "Strategy " + strat + " with probability level " + level + ", won " + percent + " percent of " + number_of_games + " games."
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
    for i in range(len(prob_list_b)):
        prob_list[i] = prob_list_b[len(prob_list_b)-i-1]
    for p in prob_list:
        for game in new_games:
            if p == game["prob"]:
                print(game["pick"]["name"],game["prob"])
"""
main:
get_database()
old_teams
old_games
new_teams
new_games
all_teams

#First:
set_team_attributes("all")
set_zscores()
set_game_attributes()
parameters
result,gamesdf = first_regression()
set_picks()
set_retroactive_picks()
test_strategy(.55,1)
test_strategy(.55,2)
print_picks()

#After:
set_team_attributes("new")
set_zscores()
set_game_attributes()
result,gamesdf = first_regression()
set_picks()
print_picks()
"""
