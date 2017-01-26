import pandas as pd
import numpy as np
from datetime import date,timedelta
from pprint import pprint
import json
from sklearn import preprocessing

import decision_tree


def make_season(start_year):
	dates = {'11': list(range(31)[1:]), '12': list(range(32)[1:]), '01': list(range(32)[1:]),
			 '02': list(range(29)[1:]), '03': list(range(32)[1:]), '04': list(range(9)[1:])}
	all_season = []
	for month in ['11', '12', '01', '02', '03', '04']:
		if month in ['01', '02', '03', '04']:
			year = start_year
			if year % 4 == 0:
				dates['02'].append(29)
		else:
			year = start_year-1
		for d in dates[month]:
			day = str(d)
			if len(day) == 1:
				day = '0'+day
			all_season.append("{}-{}-{}".format(str(year),month,day))
	return all_season

def get_initial_years_train_data(all_games, all_dates):
	training_games_list = []
	for year in range(2012,2017):
		season_dates = make_season(year)
		for day in season_dates:
			training_games_list.append(all_games.ix[all_games['date']==day])

	return pd.concat(training_games_list, ignore_index=True)

def pick_features(initial_training_games):
	features = ['spread','home_public_percentage']
	feature_dict={idx:feature for idx, feature in enumerate(features)}
	training_games = initial_training_games.ix[(initial_training_games['away_games_played']>5)&(initial_training_games['home_games_played']>5)]
	y = np.array(training_games['home_cover'].tolist())
	# print(y)
	# print(len(y))
	X = training_games.as_matrix(features)
	np.set_printoptions(edgeitems=10,linewidth=325,precision=3)
	# print(X)
	# print(len(X))
	results = decision_tree.recursive_split(X, y, feature_dict)
	pprint(results)


def main():
	all_games = pd.read_csv('incremental_data.csv')
	all_dates = all_games.date.unique().tolist()
	initial_training_games = get_initial_years_train_data(all_games,all_dates)
	pick_features(initial_training_games)


if __name__ == '__main__':
	main()
