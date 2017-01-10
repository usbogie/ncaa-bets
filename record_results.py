from datetime import datetime
import pandas as pd
import json

def add_yesterday(last_night_info, lines):
    games = []
    for idx, row in last_night_info.iterrows():
        for game in lines:
            game_results = {}
            if game['away'] == row['Game_Away'] and game['home']==row['Game_Home'] and game['date'] == row['Game_Date']:
                game_results['home'] = game['home']
                game_results['away'] = game['away']
                game_results['date'] = game['date']
                game_results['spread'] = game['spread']
                if row['Away_Score']-row['Home_Score'] > game['spread']:
                    game_results['correct'] = False
                else:
                    game_results['correct'] = True
                games.append(game_results)
    return games
