from datetime import datetime
import pandas as pd
import json

def get_yesterday_lines(last_night_info, last_night_lines):
    games = []
    for idx, row in last_night_info.iterrows():
        for game in last_night_lines:
            game_results = {}
            if game['away'] == row['Game_Away'] and game['home']==row['Game_Home']:
                game_results['home'] = game['home']
                game_results['away'] = game['away']
                game_results['date'] = game['date']
                if row['Away_Score']-row['Home_Score'] > game['spread']:
                    game_results['prediction_correct'] = False
                else:
                    game_results['prediction_correct'] = True
                games.append(game_results)
    return games
