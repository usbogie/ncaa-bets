# NCAA Basketball Betting Tool
This project has the aim of utilizing a wide variety of data about NCAA Basketball to help inform bets.

The project breaks down into to main categories: 
1. Information retrieval, storage, and access
2. Data analysis

## Information Retrieval
We will retrieve the following information:

```
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
                Game: {
                  General_Game_info: {
                    Game_ID
                    Away_Abbrv
                    Home_Abbrv
                    Away_Score
                    Home_Score
                    Away_record (after game)
                    Home_record (after game)
                    Away_1st (points in 1st)
                    Home_1st (points in 1st)
                    Away_2nd (points in 2nd)
                    Home_2nd (points in 2nd)
                    Away_OT (points in OT)
                    Home_OT (points in OT)
                    Game_Dear
                    Game_Date
                    Game_Tipoff
                    Game_Away (Away Team: full name)
                    Game_Home (Home Team: full name)
                    ....Some Tourney Info
                  }
                  Players: {
                    Player Name
                    Min
                    OREB
                    DREB
                    REB
                    AST
                    STL
                    BLK
                    TO
                    PF
                    Position
                    FGM
                    FGA
                    3PM
                    3PA
                    FTM
                    FTA
                    GAME_ID
                    Home_Away (was player home or away)
                    Team (what team they are on, abbreviation)
                  }
                  Team Stats: {
                    OREB
                    DREB
                    REB
                    AST
                    STL
                    BLK
                    TO
                    PF
                    FGM
                    FGA
                    3PM
                    3PA
                    FTM
                    FTA
                    GAME_ID
                    Home_Away
                    Team (Full name: Like Arizona State)
                  }
                }
        }
        
```


## Information Storage and Access Plan
*define language/schema for how we will store and access info*

## Data Analysis
*lay out algorithm(s) to be used for analysis*
