import numpy as np
import pandas as pd
import helpers as h

this_season = h.this_season

def pick_features(initial_training_games,features):
    y = np.asarray(initial_training_games['home_cover'], dtype="|S6")
    X = initial_training_games.as_matrix(features)
    return X,y


def get_train_data(all_games,test_year=0):
    training_games_list = []
    for year in range(2012,this_season + 1):
        if year == test_year:
            continue
        training_games_list.append(all_games.ix[all_games['season']==year])
    return pd.concat(training_games_list, ignore_index=True)