from pprint import pprint
import numpy as np
import pandas as pd
from sklearn import tree

def partition(a):
    return {c: (a==c).nonzero()[0] for c in np.unique(a)}

def entropy(s):
    res = 0
    val, counts = np.unique(s, return_counts=True)
    freqs = counts.astype('float')/len(s)
    for p in freqs:
        if p != 0.0:
            res -= p * np.log2(p)
    return res

def mutual_information(y, x):
    res = entropy(y)
    # We partition x, according to attribute values x_i
    val, counts = np.unique(x, return_counts=True)
    freqs = counts.astype('float')/len(x)
    # We calculate a weighted average of the entropy
    for p, v in zip(freqs, val):
        res -= p * entropy(y[x == v])
    return res

def is_pure(s):
    return len(set(s)) == 1

def recursive_split(x, y, feature_dict):
    # If there could be no split, just return the original set
    if is_pure(y) or len(y) == 0:
        return y
    # We get attribute that gives the highest mutual information
    gain = np.array([mutual_information(y, x_attr) for x_attr in x.T])
    selected_attr = np.argmax(gain)

    # If there's no gain at all, nothing has to be done, just return the original set
    if np.all(gain < 1e-6):
        return y
    sets = partition(x[:, selected_attr])
    res = {}
    for k, v in sets.items():
        y_subset = y.take(v, axis=0)
        x_subset = x.take(v, axis=0)

        res["{} = {}".format(feature_dict[selected_attr], k)] = recursive_split(x_subset, y_subset, feature_dict)
    return res

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

def get_initial_years_train_data(all_games, all_dates):
    training_games_list = []
    for year in range(2012,2016):
        season_dates = make_season(year)
        for day in season_dates:
            training_games_list.append(all_games.ix[all_games['date']==day])

    return pd.concat(training_games_list, ignore_index=True)

def track_today(results_df,prob = .5):
    right = 0
    wrong = 0
    for idx, row in results_df.iterrows():
        if float(row['results']) < 0 and row['home_cover'] < 0 and float(row['prob']) >= prob:
            right += 1
        elif float(row['results']) < 0 and row['home_cover'] > 0 and float(row['prob']) >= prob:
            wrong += 1
        elif float(row['results']) > 0 and row['home_cover'] < 0 and float(row['prob']) >= prob:
            wrong += 1
        elif float(row['results']) > 0 and row['home_cover'] > 0 and float(row['prob']) >= prob:
            right += 1
    return right,wrong

if __name__ == '__main__':
    all_games = pd.read_csv('games.csv')
    all_dates = all_games.date.unique().tolist()
    initial_training_games = get_initial_years_train_data(all_games,all_dates)

    test_days = []
    for day in make_season(2016):
        test_days.append(all_games.ix[all_games['date']==day])
    test_data = pd.concat(test_days,ignore_index=True)
    features = ["true_home_game","DT_home_winner","DT_spread","DT_spread_diff","DT_line_movement",
                "DT_home_public_percentage","DT_home_ats","DT_away_ats","DT_home_FT",
                "DT_away_FT","DT_home_tPAr","DT_away_tPAr","DT_TRBP","DT_home_TOVP",
                "DT_away_TOVP"]
    X_train,y = pick_features(initial_training_games,features)
    X_test, y_test = pick_features(test_data,features)

    score = 1
    i = 1
    positive = False
    for i in range(40):
        min_samples = i * 25
        if i == 0:
            min_samples = 1
        clf = tree.DecisionTreeClassifier(min_samples_leaf=min_samples)
        clf = clf.fit(X_train,y)
        score = clf.score(X_train,y)

        resultstree = clf.predict(X_test)
        probs = []
        for j in range(len(X_test)):
            probs.append(max(max(clf.predict_proba(X_test[j].reshape(1,-1)))))

        results_df = test_data[['away','home','margin','spread','home_cover']]
        results_df.insert(5, 'results', resultstree)
        results_df.insert(6, 'prob', probs)
        right,wrong = track_today(results_df,prob = .6)
        profit = right - 1.1 * wrong
        if profit > 0:
            positive = True
            print("min_samples_leaf: ",min_samples,"\nProfit: ", profit, "\nTotal Games: ", right + wrong, "\nGames won - lost: ", right - wrong,"\n")
    if not positive:
        print("No samples minimum leads to a profit")
