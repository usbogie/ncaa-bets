from pprint import pprint
import numpy as np
import pandas as pd
from sklearn import svm
from time import time
from operator import itemgetter
import matplotlib.pyplot as plt
import os
import statsmodels.formula.api as sm

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

    for year in range(2011,2018):
        if year == test_year:
            continue
        season_dates = make_season(year)
        for day in season_dates:
            training_games_list.append(all_games.ix[all_games['date']==day])
    return pd.concat(training_games_list, ignore_index=True)

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
                loc = "@ " if row['true_home_game'] else "v "
            bet_string = 'Bet' if (float(diff) >= 0 and row['prob']>=.53) or (float(diff) >= 1 and row['prob'] >= .51) or float(diff) >= 1.5 else 'Caution'
            if float(diff) < 0:
                diff = '---'
            elif float(diff) == 0:
                diff = str(abs(float(diff)))
            if print_game:
                games.append("{}{}{}{}{}{}{}{}{}\n".format(bet_string.ljust(10),winner.ljust(20),spread.ljust(7),pmargin.ljust(5),diff.ljust(5),loc,loser.ljust(20),str(round(row['prob'],4)).ljust(8),row['tipstring'].ljust(12)))
                print(bet_string.ljust(7),winner.ljust(20),spread.ljust(5),pmargin.ljust(5),diff.ljust(5),loc,loser.ljust(20),str(round(row['prob'],4)).ljust(5),row['tipstring'].ljust(12))
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
    total_profit = 0
    for test_year in range(2011,2018):
        print(test_year)
        initial_training_games = get_initial_years_train_data(all_games,all_dates,test_year)

        test_days = []
        for day in make_season(test_year):
            test_days.append(all_games.ix[all_games['date']==day])
        test_data = pd.concat(test_days,ignore_index=True)

        X_train,y = pick_features(initial_training_games,features)
        X_test, y_test = pick_features(test_data,features)

        form = features[0]
        for idx,feat in enumerate(features):
            if idx == 0:
                continue
            form += " + " + feat
        result = sm.ols(formula = "home_cover ~ {} -1".format(form),data=initial_training_games,missing='raise').fit()
        #print(result.summary())
        probs = []
        picks = []
        for i,row in test_data.iterrows():
            prob = 0
            for idx,feat in enumerate(features):
                prob += result.params[idx] * row[feat]
            if prob < 0:
                picks.append(-1)
            else:
                picks.append(1)
            probs.append(abs(prob) / 2 + .5)

#        X_train,y = pick_features(initial_training_games,features)
#        X_test, y_test = pick_features(test_data,features)
#
#        mlp = neural_network.MLPClassifier(solver='lbfgs',activation='logistic')
#        mlp = mlp.fit(X_train,y)
#
#        resultstree = mlp.predict(X_test)
#        probs = []
#        for j in range(len(X_test)):
#            probs.append(max(max(mlp.predict_proba(X_test[j].reshape(1,-1)))))
#
        results_df = test_data[['away','home','pmargin','spread','home_cover']]
        results_df.insert(5, 'results', picks)
        results_df.insert(6, 'prob', probs)
        right,wrong = track_today(results_df,prob=.524,pdiff=-2)
        
        profit = right - 1.1 * wrong
        total_profit += profit
        print("profit",round(profit,1),right+wrong,round(right/(right+wrong),4))
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
    model = svm.SVC(probability=True)
    model = model.fit(X_train,y)

    resultstree = model.predict(X_test)
    probs = []
    for j in range(len(X_test)):
        probs.append(max(max(model.predict_proba(X_test[j].reshape(1,-1)))))
            
    todays_games = pd.read_csv('todays_games.csv')
    todays_n_games = todays_games.ix[todays_games['true_home_game']==0]
    todays_h_games = todays_games.ix[todays_games['true_home_game']==1]
    t_game_list = [todays_h_games,todays_n_games]
    game_types = ["Regular","Neutral"]
    for i in range(2):
        if len(t_game_list[i]) == 0:
            continue
        games = get_initial_years_train_data(game_list[i],all_dates,2010)
        game_matrix = t_game_list[i].as_matrix(feat_list[i])
        X_train,y = pick_features(games,feat_list[i])

        clf = tree.DecisionTreeClassifier(min_samples_leaf=samples[i],max_depth=depths[i])
        clf = clf.fit(X_train,y)
        
        print("\n\n~~~~~~~~~~{} Desicion Tree Results~~~~~~~~~~~~~~~~\n\n".format(game_types[i]))
        today_results = clf.predict(game_matrix)
        probs = []
        for j in range(len(game_matrix)):
            probs.append(max(max(clf.predict_proba(game_matrix[j].reshape(1,-1)))))

        today_resultsdf = t_game_list[i][['away','home','pmargin','spread','tipstring','true_home_game']]
        today_resultsdf.insert(6, 'results', today_results)
        today_resultsdf.insert(7, 'prob', probs)
        print_picks(today_resultsdf,prob=.5)

if __name__ == '__main__':
    all_games = pd.read_csv('games.csv')
    all_dates = all_games.date.unique().tolist()
    features = ["true_home_game","home_ats","away_ats",
                "NN_reb","NN_home_winner","DT_home_public"]


    #X_train,y = pick_features(h_games,features)
    #run_gridsearch(X_train,y)
    #find_min_samples()
    #predict_today_spreads()
    test_spread()
