import numpy as np
import pandas as pd
import statsmodels.formula.api as sm
import json
from scipy.stats.mstats import zscore

with open('new_games.json') as infile:
    new_games = json.load(infile)
with open('regress_spread.json') as infile:
    regress_spread = json.load(infile)
with open('test_games.json') as infile:
    test_games = json.load(infile)
def regress_spreads():
    gamesdf = pd.DataFrame.from_dict(regress_spread)
    #result = sm.ols(formula = "home_cover ~ spread + o + d + htz + atz + fto + ftd + three_o + three_d + rebo + rebd + to + tof + true",data=gamesdf,missing='drop').fit()
    result = sm.ols(formula = "home_cover ~ spread + o + d + htz*spread + atz*spread + ftd + three_d + rebo + tof + true",data=gamesdf,missing='drop').fit()
    print(result.summary())
    parameters = list(result.params)
    i = 0
    for game in regress_spread:
        prob = result.predict()[i]
        if prob < .5:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - prob
        else:
            game["pick"] = game["home"][:-4]
            game["prob"] = prob
        i += 1
    return parameters

def predict_new_games():
    variables = ["spread","o","d","htz","atz","ftd","three_d","rebo","tof","true"]
    gamesdf = pd.DataFrame.from_dict(new_games)
    for game in new_games:
        prob = parameters[0]
        i = 1
        for var in variables:
            prob += parameters[i] * game[var]
            if var in ["htz","atz"]:
                i += 1
                prob += parameters[i] * game[var] * game["spread"]
            i += 1
        if prob < .5:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - prob
        else:
            game["pick"] = game["home"][:-4]
            game["prob"] = prob

def predict_test_games():
    variables = ["spread","o","d","htz","atz","fto","ftd","three_o","three_d","rebo","rebd","to","tof","true"]
    gamesdf = pd.DataFrame.from_dict(test_games)
    for game in test_games:
        prob = parameters[0]
        for i,var in enumerate(variables):
            prob += parameters[i+1] * game[var]
        if prob < .5:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - prob
        else:
            game["pick"] = game["home"][:-4]
            game["prob"] = prob

def test_strategy(lb = .55,ub = 2,data=regress_spread):
    number_of_games = 0
    wins = 0
    profit = 0
    lb = int(1000*lb)/1000
    for game in data:
        if game["prob"] >= lb and game["prob"] <= ub:
            number_of_games += 1
            if game["pick"] == game["cover"]:
                wins += 1
                profit += 10
            elif game["cover"] == "Tie":
                number_of_games -= 1
            else:
                profit -= 11

    try:
        percent = int(wins / number_of_games * 10000)/100
    except:
        percent = 0
    s1 = "Testing with lower-bound " + str(lb) + " won " + str(percent) + " percent of " + str(number_of_games) + " games."
    s2 = "This would lead to a profit of " + str(profit/10) + " units."
    print(s1)
    print(s2)

def print_picks(prob = .5):
    probs = []
    for game in new_games:
        if game["prob"] > prob:
            probs.append(-1 * game["prob"])
    probs = sorted(probs)
    print("Pick".ljust(20),"Spread".ljust(6),"Prob".ljust(6),"Opponent")
    for p in probs:
        for game in new_games:
            if -1 * p == game["prob"]:
                if game["pick"] == game["home"][:-4]:
                    print(game["pick"].ljust(20),str(game["spread"]).ljust(6),str(int(game["prob"]*10000)/100).ljust(6),"vs " + game["away"][:-4])
                else:
                    print(game["pick"].ljust(20),str(-1*game["spread"]).ljust(6),str(int(game["prob"]*10000)/100).ljust(6),"@  " + game["home"][:-4])

parameters = regress_spreads()
predict_new_games()
for i in range(10):
   test_strategy(lb=i/20+.5)
print_picks()
