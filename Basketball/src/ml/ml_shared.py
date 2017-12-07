import numpy as np
import pandas as pd
import helpers as h
import os

my_path = h.path
this_season = h.this_season
today_path = os.path.join(my_path,'..','data','composite','todays_games.csv')
todays_games = pd.read_csv(today_path)
games_path = os.path.join(my_path,'..','data','composite','games.csv')
all_games = pd.read_csv(games_path)
n_games = all_games.ix[all_games['true_home_game'] == 0]
h_games = all_games.ix[all_games['true_home_game'] == 1]

def pick_features(initial_training_games,features):
    y = np.asarray(initial_training_games['home_cover'], dtype="|S6")
    X = initial_training_games.as_matrix(features)
    return X,y


def get_train_data(games,test_year=0):
    training_games_list = []
    for year in range(2012,this_season + 1):
        if year == test_year:
            continue
        training_games_list.append(games.ix[games['season']==year])
    return pd.concat(training_games_list, ignore_index=True)