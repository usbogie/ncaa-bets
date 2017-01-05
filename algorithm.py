import numpy as np
import pandas as pd
import statsmodels.formula.api as sm

def regress_winners():
    gamesdf = pd.read_csv('games.csv')
    regress_games = gamesdf.to_dict("index")
    result = sm.ols(formula = "home_cover ~ spread + o + d + h_tempo + a_tempo + fto + ftd + three_o + three_d + rebo + rebd + to + tof + total + true -1",data=gamesdf,missing='drop').fit()
    #result = sm.ols(formula = "home_cover ~ spread + o + d + h_tempo + a_tempo + hfto_z + afto_z + hftd_z + aftd_z + hthree_o_z + athree_o_z + hthree_d_z + athree_d_z + hrebo_z + arebo_z + hrebd_z + arebd_z + hto_poss_z + ato_poss_z + htof_poss_z + atof_poss_z + total + true -1",data=gamesdf,missing='drop').fit()
    print(result.summary())
    parameters = list(result.params)
    for i in range(len(regress_games)):
        game = regress_games[i]
        prob = result.predict()[i]
        if prob < .5:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - prob
        else:
            game["pick"] = game["home"][:-4]
            game["prob"] = prob
    return regress_games,parameters

def predict_new_games():
    variables = ["spread","o","d","h_tempo","a_tempo","fto","ftd","three_o","three_d","rebo","rebd","to","tof","total","true"]
    gamesdf = pd.read_csv('new_games.csv')
    new_games = gamesdf.to_dict("index")
    for i in range(len(new_games)):
        game = new_games[i]
        prob = parameters[0]
        for i in range(1,len(parameters)):
            for var in variables:
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
    for i in range(len(regress_games)):
        game = regress_games[i]
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

def print_picks(prob = .52):
    prob_list_b = []
    for i in range(len(new_games)):
        game = new_games[i]
        if game["prob"] > prob:
            prob_list_b.append(game["prob"])
    np.sort(prob_list_b)
    prob_list = []
    for i in range(len(prob_list_b)):
        prob_list.append(prob_list_b[len(prob_list_b)-i-1])
    for p in prob_list:
        for i in range(len(new_games)):
            game = new_games[i]
            if p == game["prob"]:
                print(game["pick1"]["name"],game["prob"])

# Strategy 3
regress_games, parameters = regress_winners()
#new_games = predict_new_games()
#print_picks()
for i in range(50):
    test_strategy(i/100+.5)
