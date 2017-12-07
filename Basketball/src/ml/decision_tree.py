import numpy as np
import pandas as pd
from sklearn import tree
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import RFE
from time import time
from datetime import date
from operator import itemgetter
import helpers as h
from ml import ml_shared as mls
from scrapers.shared import make_season
import os

my_path = h.path
this_season = h.this_season

all_games = mls.all_games
todays_games = mls.todays_games
h_games = mls.h_games
n_games = mls.n_games

game_type = ['home','neutral']
features = ["DT_home_winner","DT_away_movement","DT_home_public","DT_away_public",
            "DT_home_ats","DT_away_ats","DT_home_tPAr","DT_home_reb"]

n_features = ["DT_home_winner",
            "DT_home_public","DT_home_ats",
            "DT_home_reb"]

game_list = [h_games,n_games]
samples = [575,1]
depths = [6,4]
feat_list = [features,n_features]

def run_gridsearch():
    X_train,y = mls.pick_features(h_games,features)
    param_grid = {"criterion": ["gini"],
              "max_depth": [None,2,3,4,5,6,7,8,9],
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


def track_today(results_df,prob = .5,pdiff=0):
    right = 0
    wrong = 0
    for idx, row in results_df.iterrows():
        if float(row['results']) < 0 and row['home_cover'] < 0 and float(row['prob']) >= prob and row['pmargin'] + row['spread'] <= -1 * pdiff:
            right += 1
        elif float(row['results']) < 0 and row['home_cover'] > 0 and float(row['prob']) >= prob and row['pmargin'] + row['spread'] <= -1 * pdiff:
            wrong += 1
        elif float(row['results']) > 0 and row['home_cover'] < 0 and float(row['prob']) >= prob and row['pmargin'] + row['spread'] >= 1 * pdiff:
            wrong += 1
        elif float(row['results']) > 0 and row['home_cover'] > 0 and float(row['prob']) >= prob and row['pmargin'] + row['spread'] >= 1 * pdiff:
            right += 1
    return right,wrong


def find_min_samples():
    min_samp_dict = {}
    feature_dict = {}
    for test_year in range(2011,this_season + 1):
        games = game_list[0]
        these_features = features
        depth = 5
        initial_training_games = mls.get_train_data(games,test_year)

        test_days = []
        for day in make_season(test_year):
            test_days.append(games.ix[games['date']==day])
        test_data = pd.concat(test_days,ignore_index=True)
        X_train,y = mls.pick_features(initial_training_games,these_features)
        X_test, y_test = mls.pick_features(test_data,these_features)

        print('\n' + str(test_year) + '\n')
        for j in range(12):
            min_samples = j * 25 + 375
            if min_samples == 0:
                min_samples = 1
            clf = tree.DecisionTreeClassifier(min_samples_leaf=min_samples,max_depth=depth)
            clf = clf.fit(X_train,y)

            resultstree = clf.predict(X_test)
            probs = []
            for j in range(len(X_test)):
                probs.append(max(max(clf.predict_proba(X_test[j].reshape(1,-1)))))

            results_df = test_data[['away','home','pmargin','spread','home_cover']]
            results_df.insert(5, 'results', resultstree)
            results_df.insert(6, 'prob', probs)
            right,wrong = track_today(results_df,prob=.53,pdiff = .5)
            profit = right - 1.05 * wrong
            if min_samp_dict.get(min_samples,0) == 0:
                min_samp_dict[min_samples] = [profit]
            else:
                min_samp_dict[min_samples].append(profit)
            if right + wrong == 0:
                break
            for idx,feat in enumerate(clf.feature_importances_):
                if feat == 0:
                    print(these_features[idx])
                    feature_dict[these_features[idx]] = feature_dict.get(these_features[idx],0) + 1
            print("min_samples_leaf: ",min_samples,"\nProfit: ", profit, "\nTotal Games: ", right + wrong, "\nPercentage: ", right / (right + wrong),"\n")
    for key in sorted(list(min_samp_dict.keys())):
        print(key,sum(min_samp_dict[key]))
    for key in sorted(list(feature_dict.keys())):
        print(key,feature_dict[key])

def test():
    min_samp_dict = {}
    feature_dict = {}
    total_profit = 0
    for test_year in range(2011,this_season + 1):
        print(test_year)
        total_right = 0
        total_wrong = 0
        for k,games in enumerate(game_list):
            initial_training_games = mls.get_train_data(games,test_year)

            test_days = []
            for day in make_season(test_year):
                test_days.append(games.ix[games['date']==day])
            test_data = pd.concat(test_days,ignore_index=True)
            X_train,y = mls.pick_features(initial_training_games,feat_list[k])
            X_test, y_test = mls.pick_features(test_data,feat_list[k])

            min_samples = samples[k]
            clf = tree.DecisionTreeClassifier(min_samples_leaf=min_samples,max_depth=depths[k])
            clf = clf.fit(X_train,y)

            filename = os.path.join(my_path,'..','data','trees','tree{}{}'.format(str(test_year),game_type[k]))
            tree.export_graphviz(clf, out_file='{}.dot'.format(filename),
                                feature_names=feat_list[k],
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
            right,wrong = track_today(results_df,prob=.53,pdiff = .5)
            total_right += right
            total_wrong += wrong
        profit = total_right - 1.05 * total_wrong
        total_profit += profit
        print("profit",round(profit,1),total_right+total_wrong)
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


def print_picks(games,game_type,prob=.5,check_pmargin=False):
    sorted_games = games.sort_values('prob',ascending=False)
    games = []
    game_type_str = "~~~~~~~~~~{} Decision Tree Results~~~~~~~~~~~~~~~~\n".format(game_type)
    print(game_type_str)
    games.append(game_type_str)
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
                diff = str(row['spread'] + row['pmargin'])
                loc = "v "
            else:
                if check_pmargin and row['pmargin'] + row['spread'] >= -1:
                    print_game = False
                    continue
                winner = row['away']
                loser = row['home']
                spread = str(row['spread'] * -1)
                pmargin = str(row['pmargin'] * -1)
                diff = str(-1 * (row['spread'] + row['pmargin']))
                loc = "@ "
            bet_string = 'Bet' if (float(diff) >=.5 and row['prob']>=.53) or (float(diff) >= 1 and row['prob'] >= .51) or float(diff) >= 1.5 else 'Caution'
            if float(diff) < 0:
                diff = '---'
            elif float(diff) == 0:
                diff = str(abs(float(diff)))
            if print_game:
                suggestion_str = "{}{}{}{}{}{}{}{}{}\n".format(bet_string.ljust(10),winner.ljust(20),spread.ljust(7),pmargin.ljust(5),diff.ljust(5),loc,loser.ljust(20),str(round(row['prob'],4)).ljust(8),row['tipstring'].ljust(12))
                games.append(suggestion_str)
                print(suggestion_str[:-1])
    return games


def predict_today():
    todays_n_games = todays_games.ix[todays_games['true_home_game']==0]
    todays_h_games = todays_games.ix[todays_games['true_home_game']==1]
    t_game_list = [todays_h_games,todays_n_games]
    game_types = ["Regular","Neutral"]
    output_path = os.path.join(my_path,'..','data','output',str(this_season),h.months[date.today().month])
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    write_path = os.path.join(output_path,'{}.txt'.format(date.today()))
    write_file = open(write_path, 'w')
    for i in range(len(game_list)):
        if len(t_game_list[i]) == 0:
            continue
        games = mls.get_train_data(game_list[i],2011)
        game_matrix = t_game_list[i].as_matrix(feat_list[i])
        X_train,y = mls.pick_features(games,feat_list[i])

        clf = tree.DecisionTreeClassifier(min_samples_leaf=samples[i],max_depth=depths[i])
        clf = clf.fit(X_train,y)
        filename = os.path.join(my_path,'..','data','trees','tree{}'.format(game_type[i]))
        tree.export_graphviz(clf, out_file='{}.dot'.format(filename),
                            feature_names=feat_list[i],
                            class_names=True,
                            filled=True,
                            rounded=True,
                            special_characters=True)
        # os.system('dot -Tpng {}.dot -o {}.png'.format(filename,filename))
        # ./dot -Tpng C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.dot -o C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.png

        # run_gridsearch(X_train,y,game_matrix)
        today_results = clf.predict(game_matrix)
        probs = []
        for j in range(len(game_matrix)):
            probs.append(max(max(clf.predict_proba(game_matrix[j].reshape(1,-1)))))

        today_resultsdf = t_game_list[i][['away','home','pmargin','spread','tipstring']]
        today_resultsdf.insert(5, 'results', today_results)
        today_resultsdf.insert(6, 'prob', probs)
        write_file.writelines(print_picks(today_resultsdf,game_types[i],prob=.5,))