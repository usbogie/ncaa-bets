import pandas as pd
import numpy as np
from datetime import date,timedelta
from pprint import pprint
import json
from sklearn import tree, svm, preprocessing
from sklearn.decomposition import PCA
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt

import sendText


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

def pick_features(initial_training_games,features):
	y = np.array(initial_training_games['home_cover'].tolist())
	X = initial_training_games.as_matrix(features)
	return X,y

def track_today(results_df):
	right = 0
	wrong = 0
	for idx, row in results_df.iterrows():
		if row['results'] < 0 and row['home_cover'] < 0:
			right += 1
		elif row['results'] < 0 and row['home_cover'] > 0:
			wrong += 1
		elif row['results'] > 0 and row['home_cover'] < 0:
			wrong += 1
		elif row['results'] > 0 and row['home_cover'] > 0:
			right += 1
		elif row['results'] == 0 and row['home_cover'] == 0:
			right+=1
	return right,wrong


def main():
	pd.set_option('display.width', 400)
	pd.set_option('display.max_rows', 100)
	np.set_printoptions(edgeitems=10,linewidth=325,precision=3)

	all_games = pd.read_csv('incremental_data.csv')
	all_dates = all_games.date.unique().tolist()
	initial_training_games = get_initial_years_train_data(all_games,all_dates)

	test_days = []
	for day in make_season(2017):
		test_days.append(all_games.ix[all_games['date']==day])
	test_data = pd.concat(test_days,ignore_index=True)
	features = ['spread','true_home_game','home_public_percentage']
	X_train,y = pick_features(initial_training_games,features)
	X_test, y_test = pick_features(test_data,features)

	polyclf = svm.SVR(degree=1, kernel='poly')
	polyclf.fit(X_train, y)

	rbfclf = svm.SVR(C=6, gamma=.01)
	rbfclf.fit(X_train, y)

	resultspoly = polyclf.predict(X_test)
	resultsrbf = rbfclf.predict(X_test)

	results_df = test_data[['team_away','team_home','margin_home','spread','home_cover']]
	results_df.insert(5, 'results', resultspoly)
	polyright,polywrong = track_today(results_df)
	results_df = test_data[['team_away','team_home','margin_home','spread','home_cover']]
	results_df.insert(5, 'results', resultsrbf)
	rbfright,rbfwrong = track_today(results_df)

	# scores = ['r2']
	# tuned_parameters = [{'kernel': ['rbf'], 'gamma': [.1,.001,.00001], 'C':[1,10,100]},
	# 					{'kernel': ['poly'], 'degree': [1]}]
	# for score in scores:
	# 	print("# Tuning hyper-parameters for %s" % score)
	# 	print()
	#
	# 	clf = GridSearchCV(svm.SVR(), tuned_parameters, verbose=100, cv=5, scoring='%s' % score, n_jobs=4)
	# 	clf.fit(X_train, y)
	# 	print("Best parameters set found on development set:")
	# 	print(clf.best_params_)
	# 	print()
	# 	print("Grid scores on development set:")
	# 	print()
	# 	means = clf.cv_results_['mean_test_score']
	# 	stds = clf.cv_results_['std_test_score']
	# 	for mean, std, params in zip(means, stds, clf.cv_results_['params']):
	# 		print("%0.3f (+/-%0.03f) for %r" % (mean, std * 2, params))
	# 	print()
	#
	# 	print("Detailed classification report:")
	# 	print()
	# 	print("The model is trained on the full development set.")
	# 	print("The scores are computed on the full evaluation set.")
	# 	print()
	# 	y_true, y_pred = y_test, clf.predict(X_test)
	# 	print(r2_score(y_true, y_pred))
	# 	print()
	#
	# right = 0
	# wrong = 0
	# days = []
	# percentages = []
	# sizes = []
	#
	# for i, day in enumerate(make_season(2017)):
	# 	test_games = all_games.ix[all_games['date']==day]
	# 	if len(test_games.index) == 0:
	# 		continue
	# 	days.append(i)
	# 	print (day, len(test_games.index))
	#
	# 	clf = svm.SVR()
	# 	clf = clf.fit(X_train, y)
	#
	# 	test_matrix = test_games.as_matrix(features)
	#
	# 	# try:
	# 	# 	scoresSVM = cross_val_score(clfSVM,test_matrix,y=np.array(test_games['home_cover'].tolist()),cv=5)
	# 	# except:
	# 	# 	try:
	# 	# 		scoresSVM = cross_val_score(clfSVM,test_matrix,y=np.array(test_games['home_cover'].tolist()))
	# 	# 	except:
	# 	# 		continue
	#
	# 	results = clf.predict(test_matrix)
	#
	# 	results_df = test_games[['team_away','team_home','margin_home','spread','home_cover']]
	# 	results_df.insert(5, 'results', results)
	# 	print(results_df)
	# 	day_right,day_wrong = track_today(results_df)
	# 	right += day_right
	# 	wrong += day_wrong
	# 	# print("SVM Accuracy: {}f (+/- {})".format(round(scoresSVM.mean(),3),round(scoresSVM.std() * 2,3)))
	# 	percentages.append(round(float(day_right)/(day_right + day_wrong),3))
	# 	sizes.append(len(test_games.index))
	# 	print("SVM Daily Percentage: {}".format(round(float(day_right)/(day_right + day_wrong),3)))
	#
	#
	# 	X_train = np.concatenate((X_train,test_matrix), axis=0)
	# 	y = np.concatenate((y, np.array(test_games['home_cover'].tolist())), axis=0)
	print("Poly final")
	print(float(polyright)/(polyright+polywrong))
	print("RBF final")
	print(float(rbfright)/(rbfright+rbfwrong))
	# sendText.sendText(float(right)/(right+wrong))
	# plt.scatter(days, percentages, s=sizes, alpha=0.5)
	# plt.show()


if __name__ == '__main__':
	main()
