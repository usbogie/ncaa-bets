# NCAA Basketball Betting Tool
This project has the aim of utilizing a wide variety of data about NCAA Basketball to help inform bets.

The project breaks down into to main categories:
1. Information retrieval, storage, and access
2. Data analysis

## Information Retrieval

### Objective
Report the favorable spreads

### Variables
- Game Type: Neutral Site or True Home Game.
- Spread: The Vegas spread according to Vegas Insider.
- Predicted Margin: Calculated using adjusted efficiency statistics and other factors.
- Home/Away: Only relevant for True Home Games.
- Line Movement: The difference between the opening spread and the closing/current spread.
- Public Percentage: The percent of the public picking a team.
- ATS Record: A team's record against the spread according to Vegas Insider.
- Three Point Rate: Percent of Field Goal Attempts from Three.
- Rebound Rate: Percent of available Rebounds grabbed.
- Turnover Rate: Turnovers per 100 plays.
- Free Throw Rate: Free Throw Attempts per Field Goal Attempt.


## Information Storage and Access Plan
All data from past games is stored in an SQLite database.

## Data Analysis
There are two different datasets, one for True Home Games and one for Neutral Site games. Both datasets will be analyzed using the variables described above in the Decision Tree Classifier from the scikit-learn library.
