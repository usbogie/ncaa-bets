from pprint import pprint
import numpy as np
import pandas as pd
from sklearn import tree
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import RFECV, RFE
from time import time
from operator import itemgetter
import matplotlib.pyplot as plt
import os
import pydot

def run_gridsearch(X_train, y):
    param_grid = {"criterion": ["gini", "entropy"],
              "max_depth": [None,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
              "min_samples_leaf": [50,75,100,125,150,175,200,250,300,325,350,375,400,450,500,550,600,650]}
    est = tree.DecisionTreeClassifier(criterion="entropy", max_depth=6, min_samples_leaf=375)
    rfe = RFE(est, 1, verbose=10)
    rfe = rfe.fit(X_train, y)
    # summarize the selection of the attributes
    rankings = []
    for idx,i in enumerate(rfe.ranking_):
        rankings.append((i,features[idx]))
    for i in sorted(rankings):
        print(i)

    clf = GridSearchCV(tree.DecisionTreeClassifier(), param_grid=param_grid, cv=5, verbose=0)
    start = time()
    clf.fit(X_train, y)
    print(("\nGridSearchCV took {:.2f} "
    	   "seconds for {:d} candidate "
    	   "parameter settings.").format(time() - start, len(clf.grid_scores_)))
    top_scores = sorted(clf.grid_scores_, key=itemgetter(1), reverse=True)[:10]
    for i, score in enumerate(top_scores):
    	print("Model with rank: {0}".format(i + 1))
    	print(("Mean validation score: "
    		   "{0:.3f} (std: {1:.3f})").format(
    		   score.mean_validation_score,
    		   np.std(score.cv_validation_scores)))
    	print("Parameters: {0}".format(score.parameters))
    	print("")

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

def pick_features(initial_training_games,features):
    y = np.asarray(initial_training_games['home_cover'], dtype="|S6")
    X = initial_training_games.as_matrix(features)
    return X,y

def get_initial_years_train_data(all_games, all_dates,test_year):
    training_games_list = []
    for year in range(2012,2018):
        if year == test_year:
            continue
        season_dates = make_season(year)
        for day in season_dates:
            training_games_list.append(all_games.ix[all_games['date']==day])
    return pd.concat(training_games_list, ignore_index=True)


def track_today(results_df,prob = .5,pdiff=0):
    right = 0
    wrong = 0
    x = False
    for idx, row in results_df.iterrows():
        if float(row['results']) < 0 and row['home_cover'] < 0 and float(row['prob']) >= prob and row['ptotal'] - row['total'] < -1*pdiff:
            right += 1
        elif float(row['results']) < 0 and row['home_cover'] > 0 and float(row['prob']) >= prob and row['ptotal'] - row['total'] > pdiff:
            wrong += 1
        elif float(row['results']) > 0 and row['home_cover'] < 0 and float(row['prob']) >= prob and row['ptotal'] - row['total'] < -1*pdiff:
            wrong += 1
        elif float(row['results']) > 0 and row['home_cover'] > 0 and float(row['prob']) >= prob and row['ptotal'] - row['total'] > pdiff:
            right += 1
    return right,wrong

def ou_track_today(results_df,prob = .5):
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

def print_picks(games,prob=.5,check_pmargin=False):
    sorted_games = games.sort_values('prob',ascending=False)
    f2 = open('output.txt', 'w')
    games = []
    for idx, row in sorted_games.iterrows():
        print_game = True
        if row['prob'] >= prob:
            if float(row['results']) > 0:
                if check_pmargin and row['pmargin'] + row['spread'] <= 1:
                    print_game = False
                    continue
                winner = row['home']
                loser = row['away']
                spread = str(row['spread'])
                pmargin = str(row['pmargin'])
                loc = "v "
            else:
                if check_pmargin and row['pmargin'] + row['spread'] >= -1:
                    print_game = False
                    continue
                winner = row['away']
                loser = row['home']
                spread = str(row['spread'] * -1)
                pmargin = str(row['pmargin'] * -1)
                loc = "@ "
            bet_string = 'Bet' if float(spread)+float(pmargin)>=1.0 and row['prob']>.523 else 'Caution'

            if print_game:
                games.append("{}{}{}{}{}{}{}{}\n".format(bet_string.ljust(10),winner.ljust(20),spread.ljust(7),pmargin.ljust(5),loc,loser.ljust(20),str(round(row['prob'],4)).ljust(8),row['tipstring'].ljust(12)))
                print(bet_string.ljust(7),winner.ljust(20),spread.ljust(5),pmargin.ljust(5),loc,loser.ljust(20),str(round(row['prob'],4)).ljust(5),row['tipstring'].ljust(12))
    f2.writelines(games)

def test_over_under(over_games,ou_features):
    X_train,y = pick_features(over_games,ou_features)

    min_samp_dict = {}
    feature_dict = {}
    for i in range(7):
        test_year = 2011 + i
        initial_training_games = get_initial_years_train_data(over_games,all_dates,test_year)

        test_days = []
        for day in make_season(test_year):
            test_days.append(over_games.ix[over_games['date']==day])
        test_data = pd.concat(test_days,ignore_index=True)
        X_train,y = pick_features(initial_training_games,ou_features)
        X_test, y_test = pick_features(test_data,ou_features)

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
            right,wrong = ou_track_today(results_df,prob=.523)
            profit = right - 1.1 * wrong
            if i == 0:
                min_samp_dict[min_samples] = [profit]
            else:
                min_samp_dict[min_samples].append(profit)
            if right + wrong == 0:
                break
            for idx,feat in enumerate(clf.feature_importances_):
                if feat == 0:
                    print(ou_features[idx])
                    feature_dict[ou_features[idx]] = feature_dict.get(ou_features[idx],0) + 1
            print("min_samples_leaf: ",min_samples,"\nProfit: ", profit, "\nTotal Games: ", right + wrong, "\nPercentage: ", right / (right + wrong),"\n")
    for key in sorted(list(min_samp_dict.keys())):
        print(key,sum(min_samp_dict[key]))
    for key in sorted(list(feature_dict.keys())):
        print(key,feature_dict[key])

def test_spread():
    min_samp_dict = {}
    feature_dict = {}
    total_profit = 0
    for test_year in range(2011,2018):
        print(test_year)
        total_right = 0
        total_wrong = 0
        for k,games in enumerate(game_list):
            initial_training_games = get_initial_years_train_data(games,all_dates,test_year)

            test_days = []
            for day in make_season(test_year):
                test_days.append(games.ix[games['date']==day])
            test_data = pd.concat(test_days,ignore_index=True)
            X_train,y = pick_features(initial_training_games,feat_list[k])
            X_test, y_test = pick_features(test_data,feat_list[k])

            min_samples = samples[k]
            clf = tree.DecisionTreeClassifier(min_samples_leaf=min_samples,max_depth=depths[k])
            clf = clf.fit(X_train,y)

            filename = 'tree_data/tree' + str(test_year) + game_type[k]
            tree.export_graphviz(clf, out_file='{}.dot'.format(filename),
                                feature_names=features,
                                class_names=True,
                                filled=True,
                                rounded=True,
                                special_characters=True)
            # os.system('dot -Tpng {}.dot -o {}.png'.format(filename,filename))
            # ./dot -Tpng C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.dot -o C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.png

            resultstree = clf.predict(X_test)
            probs = []
            for j in range(len(X_test)):
                probs.append(max(max(clf.predict_proba(X_test[j].reshape(1,-1)))))

            results_df = test_data[['away','home','pmargin','spread','home_cover']]
            results_df.insert(5, 'results', resultstree)
            results_df.insert(6, 'prob', probs)
            right,wrong = track_today(results_df,prob=.53,pdiff=1)
            total_right += right
            total_wrong += wrong
        profit = total_right - 1.1 * total_wrong
        total_profit += profit
        print("profit",round(profit,1))
        # if i == 0:
        #     min_samp_dict[min_samples] = [profit]
        # else:
        #     min_samp_dict[min_samples].append(profit)
        # if right + wrong == 0:
        #     break
        # for idx,feat in enumerate(clf.feature_importances_):
        #     if feat == 0:
        #         print(features[idx])
        #         feature_dict[features[idx]] = feature_dict.get(features[idx],0) + 1
        # print("min_samples_leaf: ",min_samples,"\nProfit: ", profit, "\nTotal Games: ", right + wrong, "\nPercentage: ", right / (right + wrong),"\n")
    print("total profit",round(total_profit,1))
    # for key in sorted(list(min_samp_dict.keys())):
    #     print(key,sum(min_samp_dict[key]))
    # for key in sorted(list(feature_dict.keys())):
    #     print(key,feature_dict[key])
def predict_today_spreads():
    todays_games = pd.read_csv('todays_games.csv')
    todays_n_games = todays_games.ix[todays_games['true_home_game']==0]
    todays_h_games = todays_games.ix[todays_games['true_home_game']==1]
    t_game_list = [todays_h_games,todays_n_games]
    game_types = ["Regular","Neutral"]
    for i in range(2):
        if len(t_game_list[i]) == 0:
            continue
        games = get_initial_years_train_data(game_list[i],all_dates,2011)
        game_matrix = t_game_list[i].as_matrix(feat_list[i])
        X_train,y = pick_features(games,feat_list[i])

        clf = tree.DecisionTreeClassifier(min_samples_leaf=samples[i],max_depth=depths[i])
        clf = clf.fit(X_train,y)
        filename = 'tree_data/tree{}'.format(game_type[i])
        tree.export_graphviz(clf, out_file='{}.dot'.format(filename),
                            feature_names=features,
                            class_names=True,
                            filled=True,
                            rounded=True,
                            special_characters=True)
        # os.system('dot -Tpng {}.dot -o {}.png'.format(filename,filename))
        # ./dot -Tpng C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.dot -o C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.png

        # run_gridsearch(X_train,y,game_matrix)
        print("\n\n~~~~~~~~~~{} Desicion Tree Results~~~~~~~~~~~~~~~~\n\n".format(game_types[i]))
        today_results = clf.predict(game_matrix)
        probs = []
        for j in range(len(game_matrix)):
            probs.append(max(max(clf.predict_proba(game_matrix[j].reshape(1,-1)))))

        today_resultsdf = t_game_list[i][['away','home','pmargin','spread','tipstring']]
        today_resultsdf.insert(5, 'results', today_results)
        today_resultsdf.insert(6, 'prob', probs)
        print_picks(today_resultsdf,prob=.5)

def predict_today_ou(over_games):
    X_train,y = pick_features(over_games,ou_features)

    min_samples = 100
    clf = tree.DecisionTreeClassifier(min_samples_leaf=min_samples,max_depth=7)
    clf = clf.fit(X_train,y)

    todays_over_games = pd.read_csv('todays_over_games.csv')
    game_matrix = todays_over_games.as_matrix(ou_features)
    run_gridsearch(X_train,y,game_matrix)
    print("\n\n~~~~~~~~~~Regular Desicion Tree Results~~~~~~~~~~~~~~~~\n\n")
    today_results = clf.predict(game_matrix)
    probs = []
    for j in range(len(game_matrix)):
        probs.append(max(max(clf.predict_proba(game_matrix[j].reshape(1,-1)))))

    today_resultsdf = todays_over_games[['away','home','ptotal','total','tipstring']]
    today_resultsdf.insert(5, 'results', today_results)
    today_resultsdf.insert(6, 'prob', probs)
    print_picks(today_resultsdf,prob=.5)

if __name__ == '__main__':
    all_games = pd.read_csv('games.csv')
    n_games = all_games.ix[all_games['true_home_game'] == 0]
    h_games = all_games.ix[all_games['true_home_game'] == 1]
    all_dates = all_games.date.unique().tolist()
    game_type = ['home','neutral']
    features = ["DT_home_winner",
                "DT_away_movement","DT_home_public","DT_away_public","DT_home_ats",
                "DT_away_ats","DT_home_tPAr","DT_home_reb","DT_away_reb"]

    n_features = ["DT_home_winner","DT_spread_diff",
                "DT_home_public","DT_away_public","DT_home_ats",
                "DT_away_ats","DT_home_reb"]

    game_list = [h_games,n_games]
    samples = [375,150]
    depths = [6,4]
    feat_list = [features,n_features]

<<<<<<< HEAD
    # X_train,y = pick_features(h_games,features)
    # run_gridsearch(X_train,y)
=======
    X_train,y = pick_features(h_games,features)
    #run_gridsearch(X_train,y)

    #test_spread()
>>>>>>> changes to decision tree

    predict_today_spreads()
    test_spread()

    ou_features = ["true_home_game","DT_pover","DT_home_over","DT_away_over",
                "DT_home_tPAr","DT_away_tPAr"]
    over_games = pd.read_csv("over_games.csv")

    # test_over_under(over_games,all_dates)

    # predict_today_ou(over_games)
