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
variables = ["spread","true_home_game","home_ats","away_ats","home_rec","away_rec","home_off_adv","away_off_adv","away_three_adv","home_three_d_adv"]
spread = ["home_tempo_z","away_tempo_z"]
true = ["conf"]
def regress_spreads():
    gamesdf = pd.DataFrame.from_dict(regress_spread)
    form = ""
    for var in variables:
        if var == "spread":
            form = var
        else:
            form += " + " + var
    for var in spread:
            form += " + {}:spread".format(var)
    for var in true:
            form += " + {}:true_home_game".format(var)
    result = sm.ols(formula = "home_cover ~ {} -1".format(form),data=gamesdf,missing='raise').fit()
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
    return parameters
def predict_new_games(data=new_games):
    gamesdf = pd.DataFrame.from_dict(data)
    for game in data:
        prob = 0
        i = 0
        for var in variables:
            prob += parameters[i] * game[var]
            i += 1
        for var in spread:
            prob += parameters[i] * game[var] * game["spread"]
            i += 1
        for var in true:
            prob += parameters[i] * game[var] * game["true_home_game"]
            i += 1
        game["prob"] = prob + .5
        if game["prob"] < .5:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - game["prob"]
        else:
            game["pick"] = game["home"][:-4]

def test_strategy(lb = .5,ub = 2,data=regress_spread):
    number_of_games = 0
    wins = 0
    profit = 0
    lb = int(1000*lb)/1000
    spreads = {}
    correct = {}
    for game in data:
        if game["cover"] != "Tie":
            if game["spread"] < 0 and game["spread"] > -5:
                spreads[-.1] = spreads.get(-.1,0) + 1
            else:
                spreads[int(game["spread"]/5)] = spreads.get(int(game["spread"]/5),0) + 1
        if game["pick"] == game["cover"]:
            if game["spread"] < 0 and game["spread"] > -5:
                correct[-.1] = correct.get(-.1,0) + 1
            else:
                correct[int(game["spread"]/5)] = correct.get(int(game["spread"]/5),0) + 1
        if game["prob"] >= lb and game["prob"] <= ub:
            number_of_games += 1
            if game["pick"] == game["cover"]:
                wins += 1
                profit += 10
            elif game["cover"] == "Tie":
                number_of_games -= 1
            else:
                profit -= 11
    for key in spreads.keys():
        correct[key] = correct.get(key,0) / spreads[key]
    for key in sorted(correct.keys()):
        print(key*5,correct[key],spreads[key])
    try:
        percent = int(wins / number_of_games * 10000)/100
    except:
        percent = 0
    s1 = "Testing with lower-bound {} won {} percent of {} games.".format(str(lb), str(percent), str(number_of_games))
    s2 = "This would lead to a profit of {} units.".format(str(profit/10))
    o = s1
    f.write("\n"+o)
    print(o)
    o = s2
    f.write("\n"+o)
    print(o)

def print_picks(prob = .5,top = 175):
    gamesleft = len(new_games)
    o = "Prob".ljust(6)
    o += "Pick".ljust(24)
    o += "Spread".ljust(7)
    o += "Opponent".ljust(27)
    o += "Tip"
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
        prob_str = str(int(nextgame["prob"]*10000)/100).ljust(6)
        tip_str = str(nextgame["tipstring"]).ljust(4)
        if nextgame["pick"] == nextgame["home"][:-4]:
            pick_str = nextgame["home_espn"].ljust(24)
            spread_str = str(nextgame["spread"]).ljust(7)
            opp_str = "vs " + nextgame["away"][:-4].ljust(24)
        else:
            pick_str = nextgame["away_espn"].ljust(24)
            spread_str = str(-1 * nextgame["spread"]).ljust(7)
            opp_str = "@  " + nextgame["home"][:-4].ljust(24)
        o = "{}{}{}{}{}".format(prob_str,pick_str,spread_str,opp_str,tip_str)
        f.write("\n"+o)
        print(o)
        top -= 1
        gamesleft -= 1
        new_games.remove(nextgame)
parameters = regress_spreads()
test_strategy()
# for i in range(5):
#     test_strategy(lb=.5+.05*i)
predict_new_games()
print_picks()
