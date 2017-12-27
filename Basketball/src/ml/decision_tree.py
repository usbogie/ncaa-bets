import numpy as np
import pandas as pd
from sklearn import tree
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import RFE
from time import time
from datetime import date
import itertools
import helpers as h
from ml import ml_shared as mls
from scrapers.shared import make_season
import os

my_path = h.path
this_season = h.this_season

game_type = ['home','neutral']

features = ["away_movement","home_ats","away_ats","away_reb",
"home_tPAr","home_winner"]

n_features = ["home_public","home_ats","home_TOVP","home_reb",
"away_tPAr","home_FT","away_FT","home_winner"]

samples = [650,75]
depths = [4,7]
min_probs = [.51,.515]
max_probs = [.534,None]
min_pdiffs = [3.5,3.5]
max_pdiffs = [8.5,None]
feat_list = [features,n_features]

def run_gridsearch(games, home_away):
    X_train,y = mls.pick_features(games[home_away],feat_list[home_away])
    param_grid = {"criterion": ["gini","entropy"],
              "max_depth": [None,1,2,3,4,5,6,7,8,9],
              "min_samples_leaf": [50,75,100,125,150,175,200,250,300,325,350,375,400,450,500,550,600,650]}

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

    top = top_scores[0]
    est = tree.DecisionTreeClassifier(criterion=top.parameters['criterion'], max_depth=top.parameters['max_depth'], min_samples_leaf=top.parameters['min_samples_leaf'])
    rfe = RFE(est, 1, verbose=10)
    rfe = rfe.fit(X_train, y)
    # summarize the selection of the attributes
    rankings = []
    for idx,i in enumerate(rfe.ranking_):
        rankings.append((i,feat_list[home_away][idx]))
    for i in sorted(rankings):
        print(i)

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
            bet_string = 'Bet' #if (float(diff) >= pdiff[10] and row['prob']>=min_prob) else 'Caution'
            if float(diff) < 0:
                diff = '---'
            elif float(diff) == 0:
                diff = str(abs(float(diff)))
            if print_game:
                suggestion_str = "{}{}{}{}{}{}{}{}{}\n".format(bet_string.ljust(10),winner.ljust(20),spread.ljust(7),pmargin.ljust(5),diff.ljust(5),loc,loser.ljust(20),str(round(row['prob'],4)).ljust(8),row['tipstring'].ljust(12))
                games.append(suggestion_str)
                print(suggestion_str[:-1])
    return games

def track_today(results_df, min_prob, min_diff, max_prob, max_diff):
    right = 0
    wrong = 0
    for idx, row in results_df.iterrows():
        if row['prob'] < min_prob or (max_prob is not None and row['prob'] >= max_prob):
            continue

        if float(row['results']) > 0 and row['pmargin'] + row['spread'] >= min_diff and (max_diff is None or row['pmargin'] + row['spread'] < max_diff):
            if row['home_cover'] > 0:
                #print("right",row)
                right += 1
            elif row['home_cover'] < 0:
                #print("wrong",row)
                wrong += 1
        if float(row['results']) < 0 and -1*(row['pmargin'] + row['spread']) >= min_diff and (max_diff is None or -1*(row['pmargin'] + row['spread']) < max_diff):
            if row['home_cover'] < 0:
                #print("right",row)
                right += 1
            elif row['home_cover'] > 0:
                #print("wrong",row)
                wrong += 1
    return right,wrong

def test_combinations(game_list):
    percentages = [ float('%.3f' % elem) for elem in list(np.arange(.50,.56,.005)) ] + [None]
    pdiffs = [-100] + [ float('%.1f' % elem) for elem in list(np.arange(-10.5,15.5,.5)) ] + [None]
    print(percentages)
    print(pdiffs)

    home_games = game_list[0]
    neutral_games = game_list[1]

    results_dfs = []
    for test_year in range(2011,this_season + 1):
        test_days = []
        for day in make_season(test_year):
            test_days.append(neutral_games.ix[neutral_games['date']==day])
        test_data = pd.concat(test_days,ignore_index=True)
        initial_training_games = mls.get_train_data(neutral_games,test_year)
        X_train,y = mls.pick_features(initial_training_games,feat_list[1])
        X_test, y_test = mls.pick_features(test_data,feat_list[1])

        clf = tree.DecisionTreeClassifier(min_samples_leaf=samples[1],max_depth=depths[1])
        clf = clf.fit(X_train,y)

        resultstree = clf.predict(X_test)
        probs = []
        for j in range(len(X_test)):
            probs.append(max(max(clf.predict_proba(X_test[j].reshape(1,-1)))))

        results_df = test_data[['away','home','pmargin','spread','home_cover']]
        results_df.insert(5, 'results', resultstree)
        results_df.insert(6, 'prob', probs)
        results_dfs.append(results_df)

    results = pd.concat(results_dfs, ignore_index=True)

    for percentage, upper_percentage in zip(percentages, percentages[2:]):
        for margin, upper_margin in zip(pdiffs, pdiffs[2:]):
            right, wrong = track_today(results,percentage,margin,upper_percentage,upper_margin)
            profit = (float(right)/1.07) - wrong
            total_games = right + wrong
            if total_games == 0:
                print("No games")
                continue
            roi = round((100 * float(profit)/total_games),2)
            print('prob: {}-{}; diff: {}-{}; games: {} ({}-{}); ROI: {}'.format(percentage,upper_percentage,margin,upper_margin,total_games,right,wrong,roi))
            # print('right: {}, wrong {}'.format(right,wrong))

def test(game_list):
    min_samp_dict = {}
    feature_dict = {}
    total_profit = 0
    total_games = 0
    # print("Grid search Home")
    # run_gridsearch(game_list,0)
    # print("Grid search Neutral")
    # run_gridsearch(game_list,1)
    for test_year in range(2011,this_season + 1):
        print(test_year)
        total_right = 0
        total_wrong = 0
        year_profit = 0
        for k,games in enumerate(game_list):
            initial_training_games = mls.get_train_data(games,test_year)
            test_days = []
            for day in make_season(test_year):
                test_days.append(games.ix[games['date']==day])
            test_data = pd.concat(test_days,ignore_index=True)
            X_train,y = mls.pick_features(initial_training_games,feat_list[k])
            X_test, y_test = mls.pick_features(test_data,feat_list[k])

            clf = tree.DecisionTreeClassifier(min_samples_leaf=samples[k],max_depth=depths[k])
            clf = clf.fit(X_train,y)

            # filename = os.path.join(my_path,'..','data','trees','tree{}{}'.format(str(test_year),game_type[k]))
            # tree.export_graphviz(clf, out_file='{}.dot'.format(filename),
            #                     feature_names=feat_list[k],
            #                     class_names=True,
            #                     filled=True,
            #                     rounded=True,
            #                     special_characters=True)
            # os.system('dot -Tpng {}.dot -o {}.png'.format(filename,filename))
            # ./dot -Tpng C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.dot -o C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.png

            resultstree = clf.predict(X_test)
            probs = []
            for j in range(len(X_test)):
                probs.append(max(max(clf.predict_proba(X_test[j].reshape(1,-1)))))

            results_df = test_data[['away','home','pmargin','spread','home_cover']]
            results_df.insert(5, 'results', resultstree)
            results_df.insert(6, 'prob', probs)

            right,wrong = track_today(results_df,min_probs[k],min_pdiffs[k],max_probs[k],max_pdiffs[k])
            total_right += right
            total_wrong += wrong
            year_profit += ((float(total_right)/1.07) - total_wrong)
            break
        total_profit += year_profit
        total_games += (total_right+total_wrong)
        print("profit",round(year_profit,1),total_right+total_wrong)
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
    print("total games", total_games, "ROI", round(100*(total_profit/total_games),1))
    # for key in sorted(list(min_samp_dict.keys())):
    #     print(key,sum(min_samp_dict[key]))
    # for key in sorted(list(feature_dict.keys())):
    #     print(key,feature_dict[key])

def predict_today(game_list):
    today_path = os.path.join(my_path,'..','data','todays_predict_data.csv')
    todays_games = pd.read_csv(today_path)
    todays_n_games = todays_games.ix[todays_games['neutral']==1]
    todays_h_games = todays_games.ix[todays_games['neutral']==0]
    t_game_list = [todays_h_games,todays_n_games]
    game_types = ["Regular","Neutral"]
    output_path = os.path.join(my_path,'..','data','output',str(this_season),h.months[date.today().month])
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    write_path = os.path.join(output_path,'{}.txt'.format(date.today()))
    write_file = open(write_path, 'w')
    for i in range(len(t_game_list)):
        if len(t_game_list[i]) == 0:
            continue
        games = mls.get_train_data(game_list[i])
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
        write_file.writelines(print_picks(today_resultsdf,game_types[i],prob=.5))
