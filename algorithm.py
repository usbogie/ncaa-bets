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
    result = sm.ols(formula = "home_winner ~ "+form+" -1",data=gamesdf,missing='raise').fit()
    o = str(result.summary())
    f.write("\n"+o)
    print(o)
    parameters = list(result.params)
    i = 0
    for game in regress_spread:
        key = int(abs(game["spread"])+.5)
        spreadprob = 0 if game["spread"] == 0 else no_cover[key] * game["spread"]/abs(game["spread"])
        game["prob"] = result.predict()[i] + .5 + spreadprob
        if game["prob"] < .5:
            game["pick"] = game["away"][:-4]
            game["prob"] = 1 - game["prob"]
        else:
            game["pick"] = game["home"][:-4]
        i += 1
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
        key = int(abs(game["spread"])+.5)
        spreadprob = 0 if game["spread"] == 0 else no_cover[key] * game["spread"]/abs(game["spread"])
        game["prob"] = prob + .5 + spreadprob
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
    o = "Prob".ljust(6)+"Pick".ljust(24)+"Spread".ljust(7)+"Opponent".ljust(27)+"Tip"
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
            o = str(int(nextgame["prob"]*10000)/100).ljust(6)+nextgame["home_espn"].ljust(24)+str(nextgame["spread"]).ljust(7)+"vs " + nextgame["away"][:-4].ljust(24)+str(nextgame["tipstring"]).ljust(4)
            f.write("\n"+o)
            print(o)
        else:
            o = str(int(nextgame["prob"]*10000)/100).ljust(6)+nextgame["away_espn"].ljust(24)+str(-1*nextgame["spread"]).ljust(7)+"@  " + nextgame["home"][:-4].ljust(24)+str(nextgame["tipstring"]).ljust(4)
            f.write("\n"+o)
            print(o)
        top -= 1
        gamesleft -= 1
        new_games.remove(nextgame)
def get_spread_likelihood(gamesdf):
    no_cover = {}
    total = {}
    for i in range(len(gamesdf.spread)):
        spread = gamesdf.spread[i]
        key = int(abs(spread)+.5)
        spreadkey = abs(spread)
        try:
            total[key] += 1
        except:
            total[key] = 1
        if spread < 0 and gamesdf.home_winner[i] == .5 and gamesdf.home_cover[i] < 0:
            try:
                no_cover[key] += 1
            except:
                no_cover[key] = 1
        elif spread > 0 and gamesdf.home_winner[i] == -.5 and gamesdf.home_cover[i] > 0:
            try:
                no_cover[key] += 1
            except:
                no_cover[key] = 1
        elif gamesdf.home_cover[i] == 0:
            total[key] -= 1
    for key in total.keys():
        try:
            no_cover[key] /= total[key]
        except:
            no_cover[key] = 0
    return no_cover
gamesdf = pd.DataFrame.from_dict(regress_spread)
no_cover = get_spread_likelihood(gamesdf)
parameters = regress_spreads()
for i in range(5):
    test_strategy(lb=i/20+.5)
predict_new_games()
print_picks()
