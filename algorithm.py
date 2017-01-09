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
f = open('output.txt','w')
variables = ["spread","home_off_adv","away_off_adv","true_home_game","home_three_adv","away_three_adv","home_three_d_adv","away_three_d_adv","home_reb_adv","to","tof"]
timespread = ["home_tempo_z","away_tempo_z"]
true = ["conf"]
def regress_spreads():
    gamesdf = pd.DataFrame.from_dict(regress_spread)
    form = ""
    for var in variables:
        if var == "spread":
            form = var
        else:
            form += " + " + var
    for var in timespread:
            form += " + " + var + ":spread"
    for var in true:
            form += " + " + var + ":true_home_game"
    result = sm.ols(formula = "home_cover ~ "+form+" -1",data=gamesdf,missing='drop').fit()
    o = str(result.summary())
    f.write("\n"+o)
    print(o)
    parameters = list(result.params)
    i = 0
    for game in regress_spread:
        game["prob"] = result.predict()[i] + .5
        if game["prob"] < .5:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - game["prob"]
        else:
            game["pick"] = game["home"][:-4]
        i += 1
    # games = []
    # margins = {}
    # for i in range(len(gamesdf.spread)):
    #     if abs(gamesdf.margin[i]) <= 8:
    #         try:
    #             margins[abs(gamesdf.margin[i])] += 1
    #         except:
    #             margins[abs(gamesdf.margin[i])] = 1
    # for key in sorted(margins.keys()):
    #     print(key,margins[key]/len(gamesdf.spread))
    return parameters

def predict_new_games(data=new_games):
    gamesdf = pd.DataFrame.from_dict(data)
    for game in new_games:
        prob = 0
        i = 0
        for var in variables:
            prob += parameters[i] * game[var]
            i += 1
        for var in timespread:
            prob += parameters[i] * game[var] * game["spread"]
            i += 1
        for var in true:
            prob += parameters[i] * game[var] * game["true_home_game"]
            i += 1
        game["prob"] = prob + .5
        if prob < 0:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - game["prob"]
        else:
            game["pick"] = game["home"][:-4]

def test_strategy(lb = .5,ub = 2,data=regress_spread):
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
    o = s1
    f.write("\n"+o)
    print(o)
    o = s2
    f.write("\n"+o)
    print(o)

def print_picks(prob = .5,top = 175):
    gamesleft = len(new_games)
    o = "Pick".ljust(20)+"Spread".ljust(6)+"Prob".ljust(6)+"Tip".ljust(4)+"Opponent"
    f.write("\n"+o)
    print(o)
    while gamesleft > 0 and top != 0:
        maxprob = 0
        nextgame = {}
        for game in new_games:
            if game["prob"] > maxprob:
                nextgame = game
                maxprob = game["prob"]
        if maxprob < prob:
            break
        if nextgame["pick"] == nextgame["home"][:-4]:
            o = nextgame["home_espn"].ljust(20)+str(nextgame["spread"]).ljust(6)+str(int(nextgame["prob"]*10000)/100).ljust(6)+str(nextgame["tipstring"]).ljust(4)+"vs " + nextgame["away"][:-4]
            f.write("\n"+o)
            print(o)
        else:
            o = nextgame["away_espn"].ljust(20)+str(-1*nextgame["spread"]).ljust(6)+str(int(nextgame["prob"]*10000)/100).ljust(6)+str(nextgame["tipstring"]).ljust(4)+"@  " + nextgame["home"][:-4]
            f.write("\n"+o)
            print(o)
        top -= 1
        gamesleft -= 1
        new_games.remove(nextgame)
parameters = regress_spreads()
for i in range(10):
   test_strategy(lb=i/20+.5)
predict_new_games()
print_picks()
