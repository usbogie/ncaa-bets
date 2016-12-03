"""
Objective:
    Report the favorable spreads and over/unders

Variables:
    Regression:
        Adjusted Offense KP
        Adjusted Defense KP
        Tipoff?
        Total?

    Matchup:
        FTO: points as a percentage of points scored
        FTD: FTA per possession
            Good FTO, Bad FTD
            Good FTO, Good FTD
        3O: points as a percentage of points scored
        3D: FG%
            Good 3O, Bad 3D
            Good 3O, Good 3D
        Rebound Differential
            Good Rebound, Good Rebound
            Good Rebound, Bad Rebound
            Bad Rebound, Bad Rebound
        Turnovers per possession
        Turnovers forced per possession
            Protect Ball, Force turnovers
            Sloppy, Force turnovers
        KP Tempo
            High Temp, Low Temp
            High Temp, High Temp
            Low Temp, Low Temp

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
    Categorize matchups
    Get database of games with same matchup types, games
    Regress data with offense defense differences, tipoff, total
    Predict difference in spread
    Use probablity test to determine how likely a cover is
    Use this data on historical games and check performance
"""

"""
Get Database

Dictionaries
    teams: {
        name
        year
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
        ftd (Fouls / KP Tempo)
        3o (3FGM * 3 / PPG)
        to_poss (TO per game / KP Tempo)
        tof_poss (TO forced per game/ KP Tempo)

        kp_o
        kp_d
        good_fto (FTM / PPG)
        good_ftd (Fouls / KP Tempo)
        bad_ftd
        good_3o (3FGM * 3 / PPG)
        good_3d (3%)
        bad_3d
        good_reb (Rebound margin)
        bad_reb
        low_to (TO per game / KP Tempo)
        high_to
        agressive (TO forced per game/ KP Tempo)
        high_temp
        low_temp
    }

    old_games: {
        spread
        total
        tipoff (-1 early, 0 not)
        home
        h_adv (adj o - opp adj d)
        away
        a_adv
        true (1 if true home game, 0 not)
        h_score
        a_score
        spread_difference
        winner
        pick
        confidence_level
        match_type
        h_attributes*
        a_attributes*
    }

    game_slate: {
        spread
        total
        tipoff (-1 early, 0 not)
        home
        h_adv
        away
        a_adv
        true
        confidence_level
        pick
        match_type
        h_attributes*
        a_attributes*
    }

    *Attribute arrays format:
        index 0:
            No advantage = 0
            Good FTO, Bad FTD = 1
            Good FTO, Good FTD = 2
        index 1:
            No advantage = 0
            Good 3O, Bad 3D = 1
            Good 3O, Good 3D = 2
        index 2:
            No advantage = 0
            Good Rebound, Good Rebound = 1
            Good Rebound, Bad Rebound = 2
            Bad Rebound, Bad Rebound = 3
        index 3:
            No advantage = 0
            Protect Ball, Force turnovers = 1
            Sloppy, Force turnovers = 2
        index 4:
            No advantage = 0
            High Temp, Low Temp = 1
            High Temp, High Temp = 2
            Low Temp, Low Temp = 3
"""

import numpy as np
import pandas as pd

def get_database():
    # Get team info (old_teams, new_teams, all_teams)
    # Get old game info
    # Get new game info
    # old

good_fto = outlier("fto", 1)
good_ftd = outlier("ftd", -1)
bad_ftd = outlier("ftd", 1)
good_3o = outlier("3o", 1)
good_3d = outlier("opp_3fg", -1)
bad_3d = outlier("opp_3fg", 1)
good_reb = outlier("reb", 1)
bad_reb = outlier("reb", -1)
low_to = outlier("to_poss", -1)
high_to = outlier("to_poss", 1)
agressive = outlier("tof_poss", 1)
high_temp = outlier("kp_t", 1)
low_temp = outlier("kp_t", -1)

def set_team_attributes_old():
    for team in old_teams:
        team["good_fto"] = team["fto"] > good_fto
        team["good_ftd"] = team["ftd"] < good_ftd
        team["bad_ftd"] = team["ftd"] > bad_ftd
        team["good_3o"] = team["3o"] > good_3o
        team["good_3d"] = team["opp_3fg"] < good_3d
        team["bad_3d"] = team["opp_3fg"] > bad_3d
        team["good_reb"] = team["reb"] > good_reb
        team["bad_reb"] = team["reb"] < bad_reb
        team["low_to"] = team["to_poss"] < low_to
        team["high_to"] = team["to_poss"] > high_to
        team["aggressive"] = team["tof_poss"] > aggressive
        team["high_temp"] = team["kp_t"] > high_temp
        team["low_temp"] = team["kp_t"] < low_temp

def set_team_attributes_new():
    for team in new_teams:
        team["good_fto"] = team["fto"] > good_fto
        team["good_ftd"] = team["ftd"] < good_ftd
        team["bad_ftd"] = team["ftd"] > bad_ftd
        team["good_3o"] = team["3o"] > good_3o
        team["good_3d"] = team["opp_3fg"] < good_3d
        team["bad_3d"] = team["opp_3fg"] > bad_3d
        team["good_reb"] = team["reb"] > good_reb
        team["bad_reb"] = team["reb"] < bad_reb
        team["low_to"] = team["to_poss"] < low_to
        team["high_to"] = team["to_poss"] > high_to
        team["aggressive"] = team["tof_poss"] > aggressive
        team["high_temp"] = team["kp_t"] > high_temp
        team["low_temp"] = team["kp_t"] < low_temp

def set_old_game_attributes():
    for game in old_games:
        home = game["home"]
        away = game["away"]
        set_game_attributes_team(game,home,away,"h_attributes")
        set_game_attributes_team(game,away,home,"a_attributes")

def set_new_game_attributes():
    for game in new_games:
        home = game["home"]
        away = game["away"]
        set_game_attributes_team(game,home,away,"h_attributes")
        set_game_attributes_team(game,away,home,"a_attributes")

def set_game_attributes_team(game,team1,team2,side):
    if team1["good_fto"]:
        if team2["bad_ftd"]:
            game[side][0] = 1
        else if team2["good_ftd"]:
            game[side][0] = 2
    if team1["good_3o"]:
        if team2["bad_3d"]:
            game[side][1] = 1
        else if team2["good_3d"]:
            game[side][1] = 2
    if team1["good_reb"]:
        if team2["good_reb"]:
            game[side][2] = 1
        if team2["bad_reb"]:
            game[side][2] = 2
    if team1["bad_reb"] and team2["bad_reb"]:
        game[side][2] = 3
    if team2["aggressive"]:
        if team1["low_to"]:
            game[side][3] = 1
        else if team1["high_to"]:
            game[side][3] = 2
    if team1["high_temp"]:
        if team2["low_temp"]:
            game[side][4] = 1
        else if team2["high_temp"]:
            game[side][4] = 2
    if team1["low_temp"] and team2["low_temp"]:
        game[side][3] = 3

# game_types
    # 0 home_locks
    # 1 home_favorites
    # 2 home_dogs
    # 3 home_long_shots
    # 4 neutral_locks
    # 5 neutral_favorites
# match_types
def categorize_old_games():
    for game in old_games:
        h_attributes = game["h_attributes"]
        a_attributes = game["a_attributes"]
        unique = True
        for i in range(match_types):
            if h_attributes == match_types[i][0]["h_attributes"] and a_attributes == match_types[i][0]["a_attributes"]:
                match_types[i].append(game)
                game["match_type"] = i
                unique = False
        if unique:
            match_types.append([game])

def set_picks():
    for game in new_games:
        regress_spread(find_similar_games(game),game)

import statsmodels.formula.api as sm
def regress_spread(game_list, game):
    similar_games = pd.DataFrame.from_dict(similar_games)
    similar_games['game_h_adv'] = similar_games.h_adv - game["h_adv"]
    similar_games['game_a_adv'] = similar_games.a_adv - game["a_adv"]
    similar_games['game_tipoff'] = similar_games.tipoff - game["tipoff"]
    similar_games['game_total'] = similar_games.total - game["total"]
    similar_games['game_true'] = similar_games.true - game["true"]
    result = sm.ols(formula = "spread_difference ~ game_h_adv + game_a_adv + game_tipoff + game_total + game_true",data=similar_games,missing='drop').fit()
    residuals = similar_games['spread_difference'] - result.predict()
    SER = np.sqrt(sum(residuals*residuals)/len(game_list))
    se = np.sqrt(SER**2 + result.bse[0]**2)
    if result.params[0] < 0:
        game["pick"] = game["away"]
    else:
        game["pick"] = game["home"]
    if se * .12 > abs(result.params[0]):
        game["confidence_level"] = 0
    else if se * .26 > abs(result.params[0]):
        game["confidence_level"] = 1
    else if se * .52 > abs(result.params[0]):
        game["confidence_level"] = 2
    else:
        game["confidence_level"] = 3

def find_similar_games(game):
    h_attributes = game["h_attributes"]
    a_attributes = game["a_attributes"]
    similar_games = []
    for matchup in match_types:
        if h_attributes == matchup[0]["h_attributes"] and a_attributes == matchup[0]["a_attributes"]:
            for i in matchup:
                similar_games.append(i)
    return similar_games

def outlier(stat, sign):
    data = []
    for team in old_teams:
        data.append(team[stat])
    std = np.std(data)
    mean = np.mean(data)
    return mean + std * sign

def set_retroactive_picks():
    for game in old_games:
        regress_spread(match_types[game["match_type"]], game)

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
good_fto = outlier("fto", 1)
good_ftd = outlier("ftd", -1)
bad_ftd = outlier("ftd", 1)
good_3o = outlier("3o", 1)
good_3d = outlier("opp_3fg", -1)
bad_3d = outlier("opp_3fg", 1)
good_reb = outlier("reb", 1)
bad_reb = outlier("reb", -1)
low_to = outlier("to_poss", -1)
high_to = outlier("to_poss", 1)
agressive = outlier("tof_poss", 1)
high_temp = outlier("kp_t", 1)
low_temp = outlier("kp_t", -1)

set_team_attributes_old()
set_old_game_attributes()
set_team_attributes_new()
set_new_game_attributes()
categorize_old_games()
set_picks()
set_retroactive_picks()
test_strategy()
"""
