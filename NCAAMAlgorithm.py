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
                Opponent FTA
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
    Categorize games (Home lock, Home slight edge, Home slight dog, Home long shot, Neutral Big, Neutral normal)
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
        kp_o
        kp_d
        good_fto (FTM / PPG)
        good_ftd (Opp FTA / KP Tempo)
        bad_ftd
        good_3o (3FGM * 3 / PPG)
        good_3d (3%)
        bad_3d
        good_reb (Rebound margin)
        bad_reb
        low_to (TO per game)
        high_to
        agressive (TO forced per game)
        high_temp
        low_temp
    }

    old_games: {
        spread
        total
        tipoff
        home
        away
        true
        h_score
        a_score
        spread_difference
        h_attributes*
        a_attributes*
    }

    game_slate: {
        spread
        total
        tipoff
        home
        away
        true
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
def get_database():
    # Get team info
    # Get old game info
    # Get new game info

# Categorize games
# home_locks
# home_favorites
# home_dogs
# home_long_shots
# neutral_locks
# neutral_favorites
def categorize_old_games():
    for game in old_games:
        spread = game["spread"]
        home = game["true"]
        if home:
            if spread <= -10:
                home_locks.add(game)
            else if spread < 0:
                home_favorites.add(game)
            else if spread < 10:
                home_dogs.add(game)
            else:
                home_long_shots.add(game)
        else:
            if spread >= 10:
                neutral_locks.add(game)
            else:
                neutral_favorites.add(game)

        attributes = game["attributes"]
        # Add to a set of games
