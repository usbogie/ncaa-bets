# NCAA Basketball Betting Tool
This project has the aim of utilizing a wide variety of data about NCAA Basketball to help inform bets.

The project breaks down into to main categories:
1. Information retrieval, storage, and access
2. Data analysis

## Information Retrieval
We will retrieve the following information:

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
        Total
        Home
        Weekday

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
        espn
        year
        home (May have issues if early in the year)
        homes
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
        game_type ("old")
        home
        away
        date

        spread
        total
        weekday (1 weekday and true, 0 false)
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

        pick
        prob

        h_score
        a_score
        margin
        winner
        home_winner (1 if home team won, else 0)
        cover
        home_cover
        correct (1 if pick and winner are equal, else 0)
    }

    new_games: {
        game_type ("new")
        home
        away
        date
        spread
        total
        weekday (1 weekday and true, 0 false)
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

        pick
        prob
    }
"""

```


## Information Storage and Access Plan
*define language/schema for how we will store and access info*

## Data Analysis
*lay out algorithm(s) to be used for analysis*
