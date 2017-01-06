import numpy as np
import pandas as pd
import statsmodels.formula.api as sm
import json

with open('new_games.json') as infile:
    new_games = json.load(infile)
with open('regress_spread.json') as infile:
    regress_spread = json.load(infile)

def regress_spreads():
    gamesdf = pd.DataFrame.from_dict(regress_spread)
    result = sm.ols(formula = "home_cover ~ spread + o + d + h_tempo + a_tempo + fto + ftd + three_o + three_d + rebo + rebd + to + tof + true -1",data=gamesdf,missing='drop').fit()
    #result = sm.ols(formula = "home_cover ~ spread + o + d + h_tempo + a_tempo + hfto_z + afto_z + hftd_z + aftd_z + hthree_o_z + athree_o_z + hthree_d_z + athree_d_z + hrebo_z + arebo_z + hrebd_z + arebd_z + hto_poss_z + ato_poss_z + htof_poss_z + atof_poss_z + total + true -1",data=gamesdf,missing='drop').fit()
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
    variables = ["spread","o","d","h_tempo","a_tempo","fto","ftd","three_o","three_d","rebo","rebd","to","tof","true"]
    gamesdf = pd.DataFrame.from_dict(new_games)
    for game in new_games:
        prob = 0
        for i,var in enumerate(variables):
            prob += parameters[i] * game[var]
        if prob < .5:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - prob
        else:
            game["pick"] = game["home"][:-4]
            game["prob"] = prob

def test_strategy(lb = .55,ub = 2):
    number_of_games = 0
    wins = 0
    for game in regress_spread:
        if game["prob"] >= lb and game["prob"] <= ub:
            number_of_games += 1
            if game["pick"] == game["cover"]:
                wins += 1
            elif game["cover"] == "Tie":
                number_of_games -= 1
    try:
        percent = wins / number_of_games * 100
    except:
        percent = 0
    s1 = "Testing with lower-bound " + str(lb) + " won " + str(percent) + " percent of " + str(number_of_games) + " games."
    profit = wins - 1.1 * (number_of_games - wins)
    s2 = "This would lead to a profit of " + str(profit) + " units."
    print(s1)
    print(s2)

def print_picks(prob = .5):
    probs = []
    for game in new_games:
        if game["prob"] > prob:
            probs.append(-1 * game["prob"])
    probs = sorted(probs)
    for p in probs:
        for game in new_games:
            if -1 * p == game["prob"]:
                if game["pick"] == game["home"][:-4]:
                    print(game["pick"],game["spread"],game["prob"])
                else:
                    print(game["pick"],-1*game["spread"],game["prob"])

parameters = regress_spreads()
predict_new_games()
for i in range(50):
    test_strategy(lb=i/100+.5)
print_picks()
