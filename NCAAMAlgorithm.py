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
        opp_to

        fto (FTM / PPG)
        fto_rank
        ftd (Fouls / KP Tempo)
        ftd_rank
        3o (3FGM * 3 / PPG)
        3o_rank
        3d_rank
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
        tempo
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
        confidence_level
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
        tempo
        fto
        ftd
        3o
        3d
        reb
        to
        tof
        confidence_level
        pick
    }
"""

import numpy as np
import pandas as pd

def get_database():
    # Get team info (old_teams, new_teams)
    # Get old game info
    # Get new game info
    # old

def set_ranks():
    for team in all_teams:
        team["fto_rank"] = find_rank("fto",team)
        team["ftd_rank"] = find_rank("ftd",team)
        team["3o_rank"] = find_rank("3o",team)
        team["3d_rank"] = find_rank("opp_3fg",team)

def find_rank(stat,team):
    value = team["stat"]
    rank = 0
    for other in all_teams:
        if other["stat"] <= value:
            rank += 1
    return rank

import statsmodels.formula.api as sm
def first_regression():
    gamesdf = pd.DataFrame.from_dict(old_games)
    result = sm.ols(formula = "margin ~ off + def + tempo + fto + ftd + 3o + 3d + reb + to + tof + tipoff + total + true + weekend",data=gamesdf,missing='drop').fit()
    return (result,gamesdf)

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
    result2 = sm.ols(formula = "margin ~ game_off + game_def + game_tempo + game_fto + game_ftd + game_3o + game_3d + game_reb + game_to + game_tof + game_tipoff + game_total + game_true + game_weekend",data=gamesdf,missing='drop').fit()
    residuals = gamesdf["margin"] - result.predict()
    SER = np.sqrt(sum(residuals*residuals)/len(game_list))
    se = np.sqrt(SER**2 + result2.bse[0]**2)
    if result2.params[0] - game["spread"] < 0:
        game["pick"] = game["away"]
    else:
        game["pick"] = game["home"]
    if se * .12 > abs(result2.params[0]):
        game["confidence_level"] = 0
    elif se * .26 > abs(result2.params[0]):
        game["confidence_level"] = 1
    elif se * .52 > abs(result2.params[0]):
        game["confidence_level"] = 2
    else:
        game["confidence_level"] = 3

def set_retroactive_picks():
    for game in old_games:
        regress_spread(game)

def set_picks():
    for game in new_games:
        regress_spread(game)

def test_strategy(level):
    number_of_games = 0
    wins = 0
    for game in old_games:
        if game["confidence_level"] >= level:
            number_of_games += 1
            if game["pick"] == game["winner"]:
                wins += 1
    percent = wins / number_of_games * 100
    s1 = "Strategy with confidence level " + level + ", won " + percent + " percent of games."
    profit = wins - 1.1 * (number_of_games - wins)
    s2 = "This would lead to a profit of " + profit + " units."
    print(s1)
    print(s2)

"""
main:
get_database()
old_teams
old_games
new_teams
new_games
all_teams
result,gamesdf = first_regression()
set_ranks()
set_picks()
set_retroactive_picks()
for i in range(4):
    test_strategy(i)
"""
