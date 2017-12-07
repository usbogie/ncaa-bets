from pprint import pprint
import numpy as np
import pandas as pd
from sklearn import tree
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import RFECV, RFE
from time import time
from datetime import date
from operator import itemgetter
import matplotlib.pyplot as plt
import helpers as h
import os

games = pd.read_csv("Data/Composite/over_games.csv")
features = ["true_home_game","DT_pover","DT_home_over","DT_away_over",
                "DT_home_tPAr","DT_away_tPAr"]

def track_today(results_df,prob = .5):
    right = 0
    wrong = 0
    for idx, row in results_df.iterrows():
        if float(row['results']) < 0 and row['over'] < 0 and float(row['prob']) >= prob and row['ptotal'] - row['total'] < -1:
            right += 1
        elif float(row['results']) < 0 and row['over'] > 0 and float(row['prob']) >= prob and row['ptotal'] - row['total'] < -1:
            wrong += 1
        elif float(row['results']) > 0 and row['over'] < 0 and float(row['prob']) >= prob and row['ptotal'] - row['total'] > 1:
            wrong += 1
        elif float(row['results']) > 0 and row['over'] > 0 and float(row['prob']) >= prob and row['ptotal'] - row['total'] > 1:
            right += 1
    return right,wrong


def test():
    min_samp_dict = {}
    feature_dict = {}
    for i in range(7):
        test_year = 2011 + i
        initial_training_games = get_initial_years_train_data(games,all_dates,test_year)

        test_days = []
        for day in make_season(test_year):
            test_days.append(games.ix[games['date']==day])
        test_data = pd.concat(test_days,ignore_index=True)
        X_train,y = pick_features(initial_training_games,features)
        X_test, y_test = pick_features(test_data,features)

        print(test_year)
        for j in range(30):
            min_samples = j * 25
            if j == 0:
                min_samples = 1
            clf = tree.DecisionTreeClassifier(min_samples_leaf=min_samples,max_depth=4)
            clf = clf.fit(X_train,y)

            resultstree = clf.predict(X_test)
            probs = []
            for j in range(len(X_test)):
                probs.append(max(max(clf.predict_proba(X_test[j].reshape(1,-1)))))

            results_df = test_data[['away','home','ptotal','total','over']]
            results_df.insert(5, 'results', resultstree)
            results_df.insert(6, 'prob', probs)
            right,wrong = track_today(results_df,prob=.523)
            profit = right - 1.05 * wrong
            if i == 0:
                min_samp_dict[min_samples] = [profit]
            else:
                min_samp_dict[min_samples].append(profit)
            if right + wrong == 0:
                break
            for idx,feat in enumerate(clf.feature_importances_):
                if feat == 0:
                    print(features[idx])
                    feature_dict[features[idx]] = feature_dict.get(features[idx],0) + 1
            print("min_samples_leaf: ",min_samples,"\nProfit: ", profit, "\nTotal Games: ", right + wrong, "\nPercentage: ", right / (right + wrong),"\n")
    for key in sorted(list(min_samp_dict.keys())):
        print(key,sum(min_samp_dict[key]))
    for key in sorted(list(feature_dict.keys())):
        print(key,feature_dict[key])


def predict_today():
    X_train,y = pick_features(games,features)

    min_samples = 100
    clf = tree.DecisionTreeClassifier(min_samples_leaf=min_samples,max_depth=7)
    clf = clf.fit(X_train,y)

    over_path = os.path.join(my_path,'..','data','composite','todays_over_games.csv')
    todays_games = pd.read_csv(over_path)
    game_matrix = todays_games.as_matrix(features)
    run_gridsearch(X_train,y,game_matrix)
    print("\n\n~~~~~~~~~~Regular Desicion Tree Results~~~~~~~~~~~~~~~~\n\n")
    today_results = clf.predict(game_matrix)
    probs = []
    for j in range(len(game_matrix)):
        probs.append(max(max(clf.predict_proba(game_matrix[j].reshape(1,-1)))))

    today_resultsdf = todays_games[['away','home','ptotal','total','tipstring']]
    today_resultsdf.insert(5, 'results', today_results)
    today_resultsdf.insert(6, 'prob', probs)
    print_picks(today_resultsdf,prob=.5)