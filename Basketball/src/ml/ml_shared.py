import numpy as np
import pandas as pd
import helpers as h
import os

my_path = h.path
this_season = h.this_season

def get_game_list():
	h_games = h.gamesdf.ix[h.gamesdf['true_home_game'] == 1]
	n_games = h.gamesdf.ix[h.gamesdf['true_home_game'] == 0]
	return [h_games, n_games]


def pick_features(initial_training_games,features):
    y = np.asarray(initial_training_games['home_cover'], dtype="|S6")
    X = initial_training_games.as_matrix(features)
    return X,y


def get_train_data(games,test_year=0):
    training_games_list = []
    for year in range(2012,this_season+1):
        if year == test_year:
            continue
        training_games_list.append(games.ix[games['season']==year])
    return pd.concat(training_games_list, ignore_index=True)