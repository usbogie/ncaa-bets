import numpy as np
import pandas as pd
import helpers as h
import sqlite3
import os

my_path = h.path
this_season = h.this_season

def get_dt_data():
	with sqlite3.connect(h.database) as db:
		gamesdf = pd.read_sql_query('''SELECT home, away, season, date, neutral,
			spread, home_cover, tipstring, pmargin, home_winner, home_big,
            away_big, spread_diff, home_fav, away_fav, home_movement,
            away_movement, home_public, away_public, home_ats, away_ats,
            home_tPAr, away_tPAr, home_reb, away_reb, home_TOVP, away_TOVP
            FROM decision_tree''', db)
	h_games = gamesdf.ix[gamesdf['neutral'] == 0]
	n_games = gamesdf.ix[gamesdf['neutral'] == 1]
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
		training_games_list.append(games.ix[games['season']==str(year)])
	return pd.concat(training_games_list, ignore_index=True)
