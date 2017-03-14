import numpy as np
import pandas as pd
from sklearn import tree
from sklearn import neural_network
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import RFE
from time import time
from operator import itemgetter
import statsmodels.formula.api as sm

def run_gridsearch(X_train, y):
    param_grid = {"criterion": ["gini"],
              "max_depth": [None,2,3,4,5,6,7,8,9],
              "min_samples_leaf": [450,500,550,600,625,650,675,700,725,750]}
    est = tree.DecisionTreeClassifier(criterion="entropy", max_depth=6, min_samples_leaf=675)
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

def new_track_today(results_df,prob = .5,pdiff=0,prob_L=.5,pdiff_L=0):
    right = 0
    wrong = 0
    for idx, row in results_df.iterrows():
        rights = 0
        DT_pick = None
        LR_pick = None
        winner = 'home' if row['home_cover'] > 0 else 'away'
        if float(row['results']) < 0 and float(row['prob']) >= prob and row['pmargin'] + row['spread'] <= -1 * pdiff:
            DT_pick = 'away'
        elif float(row['results']) > 0 and float(row['prob']) >= prob and row['pmargin'] + row['spread'] >= 1 * pdiff:
            DT_pick = 'home'
        if float(row['results_L']) < 0 and float(row['prob_L']) >= prob_L and row['pmargin'] + row['spread'] <= -1 * pdiff_L:
            LR_pick = 'away'
        elif float(row['results_L']) > 0 and float(row['prob_L']) >= prob_L and row['pmargin'] + row['spread'] >= 1 * pdiff_L:
            LR_pick = 'home'
        if DT_pick:
            rights += 1 if DT_pick == winner else -1
        if LR_pick:
            rights += 1 if LR_pick == winner else -1
        if rights < 0:
            wrong += 1
        elif rights > 0:
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
        bet = False
        fade = False
        if float(row['results']) != row['results_L']:
            row['prob_L'] = 1 - row['prob_L']
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
                if row['results_L'] > 0 or row['prob_L'] > .476 or float(diff) > 2:
                    bet = True
                else:
                    fade = True
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
                if row['results_L'] < 0 or row['prob_L'] > .476 or float(diff) > 2:
                    bet = True
                else:
                    fade = True
            bet_string = 'Bet' if bet and ((float(diff) >= .5 and row['prob']>=.53) or (row['results_L'] == float(row['results']) and float(diff) >= -2 and row['prob_L'] >= .524)) else 'Caution'
            bet_string = 'Fade' if fade and not (float(diff) >= .5 and row['prob'] >= .53) else bet_string
            if float(diff) < -2:
                diff = '---'
            elif float(diff) == 0:
                diff = str(abs(float(diff)))
            if print_game:
                games.append("{}{}{}{}{}{}{}{}{}{}\n".format(bet_string.ljust(10),winner.ljust(20),spread.ljust(7),pmargin.ljust(5),diff.ljust(5),loc,loser.ljust(20),str(round(row['prob'],4)).ljust(8),str(round(row['prob_L'],4)).ljust(8),row['tipstring'].ljust(12)))
                print(bet_string.ljust(7),winner.ljust(20),spread.ljust(5),pmargin.ljust(5),diff.ljust(5),loc,loser.ljust(20),str(round(row['prob'],4)).ljust(8),str(round(row['prob_L'],4)).ljust(8),row['tipstring'].ljust(12))
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

def find_min_samples():
    min_samp_dict = {}
    feature_dict = {}
    for test_year in range(2011,2018):
        games = game_list[1]
        these_features = n_features
        depth = 6
        initial_training_games = get_initial_years_train_data(games,all_dates,test_year)

        test_days = []
        for day in make_season(test_year):
            test_days.append(games.ix[games['date']==day])
        test_data = pd.concat(test_days,ignore_index=True)
        X_train,y = pick_features(initial_training_games,these_features)
        X_test, y_test = pick_features(test_data,these_features)

        print('\n' + str(test_year) + '\n')
        for j in range(40):
            min_samples = j * 25
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
            profit = right - 1.1 * wrong
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
        print(key,round(sum(min_samp_dict[key]),2))
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
            right,wrong = track_today(results_df,prob=.53,pdiff = .5)
            total_right += right
            total_wrong += wrong
        profit = total_right - 1.1 * total_wrong
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
    
def new_test_spread():
    min_samp_dict = {}
    feature_dict = {}
    total_profit = 0
    for test_year in range(2011,2018):
        print(test_year)
        total_right = 0
        total_wrong = 0
        for k,games in enumerate(game_list):
            initial_training_games = get_initial_years_train_data(games,all_dates,test_year)
            all_training_games = get_initial_years_train_data(all_games,all_dates,test_year)
            test_days = []
            for day in make_season(test_year):
                test_days.append(games.ix[games['date']==day])
            test_data = pd.concat(test_days,ignore_index=True)
            X_train,y = pick_features(initial_training_games,feat_list[k])
            X_test, y_test = pick_features(test_data,feat_list[k])

            min_samples = samples[k]
            clf = tree.DecisionTreeClassifier(min_samples_leaf=min_samples,max_depth=depths[k])
            clf = clf.fit(X_train,y)

            # os.system('dot -Tpng {}.dot -o {}.png'.format(filename,filename))
            # ./dot -Tpng C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.dot -o C:\Users\Carl\Documents\ncaa-bets\tree_data\treehome.png

            resultstree = clf.predict(X_test)
            probs = []
            for j in range(len(X_test)):
                probs.append(max(max(clf.predict_proba(X_test[j].reshape(1,-1)))))
            
            form = LR_features[0]
            for idx,feat in enumerate(LR_features):
                if idx == 0:
                    continue
                form += " + " + feat
            result = sm.ols(formula = "home_cover ~ {} -1".format(form),data=all_training_games,missing='raise').fit()
            probs_L = []
            picks = []
            for i,row in test_data.iterrows():
                prob = 0
                for idx,feat in enumerate(LR_features):
                    prob += result.params[idx] * row[feat]
                if prob < 0:
                    picks.append(-1)
                else:
                    picks.append(1)
                probs_L.append(abs(prob) / 2 + .5)
            
            results_df = test_data[['away','home','pmargin','spread','home_cover']]
            results_df.insert(5, 'results', resultstree)
            results_df.insert(6, 'prob', probs)
            results_df.insert(7, 'results_L', picks)
            results_df.insert(8, 'prob_L', probs_L)
            right,wrong = new_track_today(results_df,prob=.53,pdiff=.5,prob_L=.524,pdiff_L=-2)
            total_right += right
            total_wrong += wrong
        profit = total_right - 1.1 * total_wrong
        total_profit += profit
        print("profit",round(profit,1),total_right+total_wrong,round(total_right/(total_right+total_wrong),4))
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
    form = LR_features[0]
    for idx,feat in enumerate(LR_features):
        if idx == 0:
            continue
        form += " + " + feat
    training_games = get_initial_years_train_data(all_games,all_dates,2011)
    result = sm.ols(formula = "home_cover ~ {} -1".format(form),data=training_games,missing='raise').fit()
    #print(result.summary())
    for i in range(2):
        if len(t_game_list[i]) == 0:
            continue
        games = get_initial_years_train_data(game_list[i],all_dates,2011)
        game_matrix = t_game_list[i].as_matrix(feat_list[i])
        X_train,y = pick_features(games,feat_list[i])
        
        clf = tree.DecisionTreeClassifier(min_samples_leaf=samples[i],max_depth=depths[i])
        clf = clf.fit(X_train,y)
 
        today_results = clf.predict(game_matrix)
        probs = []
        for j in range(len(game_matrix)):
            probs.append(max(max(clf.predict_proba(game_matrix[j].reshape(1,-1)))))
        
        probs_L = []
        picks = []
        for j,row in t_game_list[i].iterrows():
            prob = 0
            for idx,feat in enumerate(LR_features):
                prob += result.params[idx] * row[feat]
            if prob < 0:
                picks.append(-1)
            else:
                picks.append(1)
            probs_L.append(abs(prob) / 2 + .5)
        
        print("\n\n~~~~~~~~~~{} Desicion Tree Results~~~~~~~~~~~~~~~~\n\n".format(game_types[i]))

        today_resultsdf = t_game_list[i][['away','home','pmargin','spread','tipstring','true_home_game']]
        today_resultsdf.insert(6, 'results', today_results)
        today_resultsdf.insert(7, 'prob', probs)
        today_resultsdf.insert(8, 'results_L', picks)
        today_resultsdf.insert(9, 'prob_L', probs_L)
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
    features = ["DT_home_winner","DT_away_movement","DT_home_public","DT_away_public",
                "DT_home_ats","DT_away_ats","DT_home_tPAr","DT_home_reb"]
    
    LR_features = ["true_home_game","home_ats","away_ats",
                "NN_reb","NN_home_winner","DT_home_public"]

    n_features = ["DT_home_winner","DT_home_public","DT_home_ats",
                "DT_home_reb"]

    game_list = [h_games,n_games]
    samples = [425,100]
    depths = [6,4]
    feat_list = [features,n_features]

    #X_train,y = pick_features(h_games,features)
    #run_gridsearch(X_train,y)
    #find_min_samples()
    predict_today_spreads()
    #new_test_spread()

    ou_features = ["true_home_game","DT_pover","DT_home_over","DT_away_over",
                "DT_home_tPAr","DT_away_tPAr"]
    over_games = pd.read_csv("over_games.csv")

    # test_over_under(over_games,all_dates)

    # predict_today_ou(over_games)
