"""
Objective:
    Report the favorable spreads

Variables:
    Regression:
        Adjusted Offense KP
        Adjusted Defense KP
        Adjusted Tempo KP
        FTO: points as a percentage of points scored
        FTD: FTA per possession
        3O: points as a percentage of points scored
        3O%
        3D%
        REBO: offensive rebound percentage
        REBD: defensive rebound percentage
        Turnovers per offensive play
        Turnovers forced per offensive play
        Total
        Home
        Weekday

    Scrape:
        Team: {
            KenPom:
                KP Adjusted O
                KP Adjusted D
                KP Adjusted T
            TeamRankings:
                FTperc (percent of points from ft)
                OFTAPP
                3perc (percent of points from 3)
                3%
                Opponent 3FG%
                O Rebound percentage
                D Rebound percentage
                Turnovers per play
                Turnovers forced per play
        }

        Old Game: {
            OddShark:
                Spread
                Total
            ESPN:
                Day of week
                True Home Game
                Home Team
                Away Team
                Home Score
                Away Score
        }

        New Game: {
            Sportsbook:
                Spread
                Total
            ESPN:
                Day of week
                True Home Game
                Home Team
                Away Team
        }
"""

"""
Get Database

Dictionaries
    teams: {
        name
        espn
        year
        home (May have issues if early in the year)
        homes
        kp_o
        kp_d
        kp_t
        three_o
        perc3
        three_d
        rebo
        rebd
        to
        tof

        kp_o_z
        kp_d_z
        fto_z
        ftd_z
        three_o_z
        perc3_z
        three_d_z
        rebo_z
        rebd_z
        to_poss_z
        tof_poss_z
    }

    old_games: {
        game_type ("old")
        home
        away
        h_espn
        a_espn
        date

        spread
        total
        weekday (1 weekday and true, 0 false)
        true (1 true, 0 false)
        o
        d
        h_tempo
        a_tempo
        fto
        ftd
        three_o
        three_d
        rebo
        rebd
        to
        tof

        pick1
        pick2
        p_margin
        p_spread_margin
        prob1
        prob2
        prob3

        h_score
        a_score
        margin
        winner
        home_winner (1 if home team won, else 0)
        cover
        home_cover
        correct (1 if pick and winner are equal, else 0)
    }

    new_games: {
        game_type ("new")
        home
        away
        h_espn
        a_espn
        date
        spread
        total
        weekday (1 weekday and true, 0 false)
        true (1 true, 0 false)
        o
        d
        h_tempo
        a_tempo
        fto
        ftd
        three_o
        three_d
        rebo
        rebd
        to
        tof

        pick1
        pick2
        p_margin
        p_spread_margin
        prob1
        prob2
        prob3
    }
"""

import numpy as np
import pandas as pd
from scipy.stats.mstats import zscore
import statsmodels.formula.api as sm
from scipy.stats import norm
from datetime import date, timedelta
from fuzzywuzzy import fuzz

def get_team_stats():
    ncaa_2014 = pd.read_csv('NCAAM_2014.csv')
    ncaa_2015 = pd.read_csv('NCAAM_2015.csv')
    ncaa_2016 = pd.read_csv('NCAAM_2016.csv')
    ncaa_2017 = pd.read_csv('NCAAM_2017.csv')
    years = [ncaa_2014,ncaa_2015,ncaa_2016,ncaa_2017]
    for i in range(len(years)):
        teams_count = len(years[i])
        for j in range(teams_count):
            team = years[i].Name[j] + str(2014 + i)
            teams[team] = {}
            teams[team]["name"] = years[i].Name[j]
            teams[team]["year"] = str(i + 2014)
            teams[team]["homes"] = {}
            teams[team]["fto"] = years[i].FTO[j]
            teams[team]["ftd"] = years[i].FTD[j]
            teams[team]["three_o"] = years[i].Three_O[j]
            teams[team]["perc3"] = years[i].perc3[j]
            teams[team]["three_d"] = years[i].Three_D[j]
            teams[team]["rebo"] = years[i].REBO[j]
            teams[team]["rebd"] = years[i].REBD[j]
            teams[team]["to_poss"] = years[i].TOP[j]
            teams[team]["tof_poss"] = years[i].TOFP[j]
            all_teams.append(teams[team])
            if i == len(years) - 1:
                new_teams.append(teams[team])
    get_espn_names(ncaa_2014.Name)
    get_kp_names(ncaa_2014.Name)
    get_kp_stats()

def get_kp_stats():
    kp14 = pd.read_json('kenpom14.json')
    kp15 = pd.read_json('kenpom15.json')
    kp16 = pd.read_json('kenpom16.json')
    kp17 = pd.read_json('kenpom17.json')
    years = [kp14,kp15,kp16,kp17]
    for i in range(len(years)):
        teams_count = len(years[i])
        for j in range(teams_count):
            name = kp_names[years[i].name[j]] + str(2014 + i)
            teams[name]["kp_o"] = years[i].adjO[j]
            teams[name]["kp_d"] = years[i].adjD[j]
            teams[name]["kp_t"] = years[i].adjT[j]

def get_old_games():
    gamesdf14 = pd.read_csv("game_info2014.csv")
    gamesdf15 = pd.read_csv("game_info2015.csv")
    gamesdf16 = pd.read_csv("game_info2016.csv")
    gamesdf17 = pd.read_csv("game_info2017.csv")
    years = [gamesdf14,gamesdf15,gamesdf16,gamesdf17]
    for year in len(years):
        for i in range(len(gamesdf14.Game_Away)):
            try:
                home = espn_names[years[year].Game_Home[i]]
                away = espn_names[years[year].Game_Away[i]]
                game = {}
                all_games.append(game)
                old_games.append(game)
                game["game_type"] = "old"
                game["home"] = teams[home+str(2014+year)]
                game["away"] = teams[away+str(2014+year)]
                game["h_score"] = years[year].Home_Score[i]
                game["a_score"] = years[year].Away_Score[i]
                game["margin"] = game["h_score"] - game["a_score"]
                game["home_winner"] = (game["margin"]/abs(game["margin"])) * .5 + .5
                if game["home_winner"] == 1:
                    game["winner"] = game["home"]
                else:
                    game["winner"] = game["away"]

                # Get Game Date
                d = years[year].Game_Date[i].split("-")
                d.append(year+2014)
                months = ["Jan","Feb","Mar","Apr","Nov","Dec"]
                j = 0
                for m in months:
                    j += 1
                    if m == d[1]:
                        if j > 4:
                            d[2] -= 1
                            d[1] = j + 6
                        else:
                            d[1] = j
                        break
                gameday = date(d[2],d[1],int(d[0]))
                game["tipoff_e"] = years[year].Game_Tipoff[i]
                hour = int(game["tipoff_e"].split(":")[0])
                if (hour < 6 or hour == 12) and game["tipoff_e"].split(" ")[1] == "AM":
                    gameday -= timedelta(days=1)
                game["date"] = gameday

                game["location"] = years[year].Game_Location[i]
                try:
                    game["home"]["homes"][game["location"]] += 1
                except:
                    game["home"]["homes"][game["location"]] = 1
            except:
                continue

    for team in all_teams:
        team["home"] = max(team["homes"],key=team["homes"].get)
    for game in all_games:
        game["true"] = 0
        if game["home"]["home"] == game["location"]:
            game["true"] = 1
        game["weekday"] = 0
        if game["date"].weekday() > 1 and game["date"].weekday() < 7 and game["true"] == 1:
            game["weekday"] = 1

def update_team_stats():
    ncaa_2017 = pd.read_csv('NCAAM_2017.csv')
    j = 0
    for team in new_teams:
        team["fto"] = ncaa_2017.FTO[j]
        team["ftd"] = ncaa_2017.FTD[j]
        team["three_o"] = ncaa_2017.Three_O[j]
        team["perc3"] = ncaa_2017.perc3[j]
        team["three_d"] = ncaa_2017.Three_D[j]
        team["rebo"] = ncaa_2017.REBO[j]
        team["rebd"] = ncaa_2017.REBD[j]
        team["to_poss"] = ncaa_2017.TOP[j]
        team["tof_poss"] = ncaa_2017.TOFP[j]
        j += 1
    set_team_attributes()

def set_team_attributes():
    stat_list = ["kp_o","kp_d","fto","ftd","three_o","perc3","three_d","rebo","rebd","to_poss","tof_poss"]
    for stat in stat_list:
        set_zscores(stat)

def set_zscores(stat):
    l = []
    for team in all_teams:
        l.append(team[stat])
    z = zscore(l)
    i=0
    stat_z = stat + "_z"
    for team in all_teams:
        team[stat_z] = z[i]
        i += 1

def set_game_attributes():
    for game in all_games:
        home = game["home"]
        away = game["away"]
        game["o"] = home["kp_o_z"] + away["kp_d_z"]
        game["d"] = -1 * (home["kp_d_z"] + away["kp_o_z"])
        game["h_tempo"] = home["kp_t"]
        game["a_tempo"] = away["kp_t"]
        game["fto"] = 0
        if home["fto_z"] > 0:
            game["fto"] = home["fto_z"] + away["ftd_z"]
        game["ftd"] = 0
        if away["fto_z"] > 0:
            game["ftd"] = -1 * (home["ftd_z"] + away["fto_z"])
        game["three_o"] = 0
        if home["three_o_z"] > 0:
            game["three_o"] = home["three_o_z"] * (home["perc3_z"] + away["three_d_z"])
        game["three_d"] = 0
        if away["three_o_z"] > 0:
            game["three_d"] = -1 * away["three_o_z"] * (away["perc3_z"] + home["three_d_z"])
        game["rebo"] = home["rebo_z"] - away["rebd_z"]
        game["rebd"] = home["rebd_z"] - away["rebo_z"]
        game["to"] = -1 * (home["to_poss_z"] + away["tof_poss_z"])
        game["tof"] = home["tof_poss_z"] + away["to_poss_z"]


def regress_margin():
    gamesdf = pd.DataFrame.from_dict(old_games)
    result = sm.ols(formula = "margin ~ o + d + h_tempo + a_tempo + fto + ftd + three_o + three_d + rebo + rebd + to + tof + total + true + weekday -1",data=gamesdf,missing='drop').fit()
    parameters = list(result.params)
    i = 0
    for old_game in old_games:
        old_game["p_spread_margin"] = abs(result.predict()[i] + old_game["spread"])
    predictions = result.predict()
    return (gamesdf,predictions,parameters)

def predict_spread(game,gamesdf,predictions):
    gamesdf["game_o"] = gamesdf.o - game["o"]
    gamesdf["game_d"] = gamesdf.d - game["d"]
    gamesdf["game_h_tempo"] = gamesdf.h_tempo - game["h_tempo"]
    gamesdf["game_a_tempo"] = gamesdf.a_tempo - game["a_tempo"]
    gamesdf["game_fto"] = gamesdf.fto - game["fto"]
    gamesdf["game_ftd"] = gamesdf.ftd - game["ftd"]
    gamesdf["game_3o"] = gamesdf.three_o - game["three_o"]
    gamesdf["game_3d"] = gamesdf.three_d - game["three_d"]
    gamesdf["game_rebo"] = gamesdf.rebo - game["rebo"]
    gamesdf["game_rebd"] = gamesdf.rebd - game["rebd"]
    gamesdf["game_to"] = gamesdf.to - game["to"]
    gamesdf["game_tof"] = gamesdf.tof - game["tof"]
    gamesdf["game_total"] = gamesdf.total - game["total"]
    gamesdf["game_true"] = gamesdf.true - game["true"]
    gamesdf["game_weekday"] = gamesdf.weekday - game["weekday"]
    result2 = sm.ols(formula = "margin ~ game_o + game_d + game_h_tempo + game_a_tempo + game_fto + game_ftd + game_3o + game_3d + game_rebo + game_rebd + game_to + game_tof + game_total + game_true + game_weekday",data=gamesdf,missing='drop').fit()
    game["p_margin"] = result2.params[0]
    game["p_spread_margin"] = abs(result2.params[0] + game["spread"])
    if result2.params[0] + game["spread"] < 0:
        game["pick1"] = game["away"]
    else:
        game["pick1"] = game["home"]
    # Get Prob 1
    residuals = gamesdf["margin"] - predictions
    SER = np.sqrt(sum(residuals*residuals)/len(old_games))
    se = np.sqrt(SER**2 + result2.bse[0]**2)
    game["prob1"] = norm.cdf(game["p_spread_margin"]/se)

def set_prob2(game,gamesdf):
    gamesdf["game_advantage"] = gamesdf.p_spread_margin - game["p_spread_margin"]
    test2 = sm.ols(formula = "correct ~ game_advantage + game_advantage^2",data=gamesdf,missing='drop').fit()
    game["prob2"] = test2.params[0]

def set_picks():
    gamesdf,predictions,parameters = regress_margin()
    for game in all_games:
        predict_spread(game,gamesdf,predictions)
        if game["game_type"] == "old":
            if game["pick1"] == game["cover"]:
                game["correct"] = 1
            else:
                game["correct"] = 0
    for game in all_games:
        set_prob2(game,gamesdf)
    return parameters

def regress_winners():
    gamesdf = pd.DataFrame.from_dict(old_games)
    result = sm.ols(formula = "home_cover ~ spread + o + d + h_tempo + a_tempo + fto + ftd + three_o + three_d + rebo + rebd + to + tof + total + true + weekday -1",data=gamesdf,missing='drop').fit()
    parameters = list(result.params)
    i = 0
    for game in old_games:
        prob = result.predict()[i]
        i += 1
        if prob < .5:
            game["pick2"] = game["away"]
            game["prob3"] = 1 - prob
        else:
            game["pick2"] = game["home"]
            game["prob3"] = prob
    predict_new_games(parameters)
    return parameters

def predict_new_games(parameters):
    variables = ["spread","o","d","h_tempo","a_tempo","fto","ftd","three_o","three_d","rebo","rebd","to","tof","total","true","weekday"]
    for game in new_games:
        prob = parameters[0]
        for i in range(1,len(parameters)):
            for var in variables:
                prob += parameters[i] * game[var]
        if prob < .5:
            game["pick2"] = game["away"]
            game["prob3"] = 1 - prob
        else:
            game["pick2"] = game["home"]
            game["prob3"] = prob

def test_strategy(strat,level = .55,ub = 2):
    number_of_games = 0
    wins = 0
    prob = "prob" + str(strat)
    pick = "pick" + str(int((strat + 1) / 2))
    for game in old_games:
        if game[prob] >= level and game[prob] <= ub:
            number_of_games += 1
            if game[pick] == game["winner"]:
                wins += 1

    percent = wins / number_of_games * 100
    s1 = "Strategy " + str(strat) + " with probability level " + str(level) + ", won " + str(percent) + " percent of " + str(number_of_games) + " games."
    profit = wins - 1.1 * (number_of_games - wins)
    s2 = "This would lead to a profit of " + str(profit) + " units."
    print(s1)
    print(s2)

def print_picks(prob = .6):
    prob_list_b = []
    for game in new_games:
        if game["prob"] > prob:
            prob_list_b.append(game["prob"])
    np.sort(prob_list_b)
    prob_list = []
    for i in range(len(prob_list_b)):
        prob_list.append(prob_list_b[len(prob_list_b)-i-1])
    for p in prob_list:
        for game in new_games:
            if p == game["prob"]:
                print(game["pick1"]["name"],game["prob"])

def get_espn_names(name_list):
    team_pairs = set()
    team_set = set()
    for team in name_list:
        team_set.add(team)

    games_df = pd.read_csv('game_info2014.csv')
    i = 0
    team_set2 = set()
    team_set3 = set()
    for team in games_df["Game_Home"]:
        if team in team_set:
            team_set2.add(team)
            team_pairs.add((team,team))
        elif games_df["Home_Abbrv"][i] in team_set:
            team_set2.add(games_df["Home_Abbrv"][i])
            team_pairs.add((games_df["Home_Abbrv"][i],team))
        else:
            team_set3.add(team)
        i += 1
    for team in team_set2:
        team_set.remove(team)
    team_set4 = set()
    for team in team_set3:
        state = team.replace("State","St")
        if state in team_set:
            team_set.remove(state)
            team_set4.add(team)
            team_pairs.add((state,team))
        state2 = team.replace("St","State")
        sac = state2.replace("Sacramento","Sac")
        nw = sac.replace("Northwestern", "NW")
        app = nw.replace("Appalachian","App")
        tenn = app.replace("Tennessee","TN")
        miss = tenn.replace("Mississippi","Miss")
        if miss in team_set:
            team_set.remove(miss)
            team_set4.add(team)
            team_pairs.add((miss,team))
        fran = team.replace("Francis","Fran")
        if fran in team_set:
            team_set.remove(fran)
            team_set4.add(team)
            team_pairs.add((fran,team))
        s = team.replace("'s","s")
        saint = s.replace("Saint","St")
        st = saint.replace("St.","St")
        if st in team_set:
            team_set.remove(st)
            team_set4.add(team)
            team_pairs.add((st,team))
        cent = team.replace("Cent","Central")
        car = cent.replace(" Carolina","C")
        if car in team_set:
            team_set.remove(car)
            team_set4.add(team)
            team_pairs.add((car,team))
        north = team.replace("North","N")
        south = north.replace("South","S")
        if south in team_set:
            team_set.remove(south)
            team_set4.add(team)
            team_pairs.add((south,team))
        tech = team.replace("Tenn","TN")
        fla = tech.replace("Florida Atl","Fla Atlantic")
        if fla in team_set:
            team_set.remove(fla)
            team_set4.add(team)
            team_pairs.add((fla,team))
        sm = team.replace("Southern Miss", "S Mississippi")
        mass = sm.replace("Massachusetts", "U Mass")
        um = mass.replace("UMass", "Massachusetts")
        mar = um.replace("UM","Maryland ")
        om = mar.replace("Ole Miss","Mississippi")
        if om in team_set:
            team_set.remove(om)
            team_set4.add(team)
            team_pairs.add((om,team))
        a = team.replace("UCF","Central FL")
        b = a.replace("FIU","Florida Intl")
        c = b.replace("UIC","IL-Chicago")
        d = c.replace("MD-E Shore","Maryland ES")
        e = d.replace("New Mexico St", "N Mex State")
        f = e.replace("PV A&M", "Prairie View")
        g = f.replace("SMU", "S Methodist")
        i = g.replace("VMI", "VA Military")
        h = i.replace("TCU", "TX Christian")
        if h in team_set:
            team_set.remove(h)
            team_set4.add(team)
            team_pairs.add((h,team))
    for team in team_set4:
        team_set3.remove(team)
    from fuzzywuzzy import fuzz
    team_set4.clear()
    for team1 in sorted(team_set):
        ratio = 0
        team = ""
        for team2 in team_set3:
            if fuzz.ratio(team1,team2) > ratio:
                ratio = fuzz.ratio(team1,team2)
                team = team2
        invalid = ["Metro State", "Tenn Tech", "Massachusetts", "Florida Atl"]
        if team in invalid:
            continue
        if ratio > 60:
            team_set4.add(team1)
            team_set3.remove(team)
            team_pairs.add((team1,team))
    for team in team_set4:
        team_set.remove(team)
    team_set4.clear()
    for team1 in sorted(team_set):
        ratio = 0
        team = ""
        for team2 in team_set3:
            if fuzz.ratio(team1,team2) > ratio:
                ratio = fuzz.ratio(team1,team2)
                team = team2
                valid = [38,57,58]
        if ratio in valid:
            team_set4.add(team1)
            team_set3.remove(team)
            team_pairs.add((team1,team))
    for team in team_set4:
        team_set.remove(team)
    team_set4.clear()
    for team1 in sorted(team_set):
        ratio = 0
        team = ""
        for team2 in team_set3:
            if fuzz.ratio(team1,team2) > ratio:
                ratio = fuzz.ratio(team1,team2)
                team = team2
        if ratio > 40:
            team_set4.add(team1)
            team_set3.remove(team)
            team_pairs.add((team1,team))
    for tr,espn in team_pairs:
        espn_names[espn] = tr

def get_kp_names(name_list):
    trset = set()
    espnset = set()
    matched = set()
    unmatched = set()
    pairs = set()
    kpdf17 = pd.read_json('kenpom17.json')
    kpdf14 = pd.read_json('kenpom14.json')
    for name in name_list:
        trset.add(name)
    for name in list(espn_names.keys()):
        espnset.add(name)
    for name in kpdf14.name:
        if name in trset or name in espnset:
            matched.add(name)
            pairs.add((name,name))
        else:
            unmatched.add(name)
    for name in kpdf17.name:
        if name not in matched and name not in unmatched:
            if name in trset or name in espnset:
                matched.add(name)
                pairs.add((name,name))
            else:
                unmatched.add(name)
    tmp = set()
    for team in unmatched:
        e = team.replace('Eastern','E')
        e2 = e.replace('East','E')
        tn = e2.replace('Tennessee','TN')
        n = tn.replace('Northern','N')
        n2 = n.replace('North','N')
        w = n2.replace('Western','W')
        s = w.replace('Southern','S')
        se = s.replace('Southeastern','SE')
        s2 = se.replace('South','S')
        il = s2.replace('Illinois ','IL-')
        miss = il.replace('Mississippi','Miss')
        period = miss.replace('.','')
        if period in espnset or period in trset:
            matched.add(period)
            pairs.add((period,team))
            tmp.add(team)
    for team in tmp:
        unmatched.remove(team)
    tmp.clear()
    for team in unmatched:
        george = team.replace('George','G.')
        nc = george.replace('North Carolina','NC')
        st = nc.replace('St.','State')
        if st in espnset or st in trset:
            matched.add(st)
            pairs.add((st,team))
            tmp.add(team)
        la = team.replace('Louisiana','LA')
        fw = la.replace('Fort Wayne','IPFW')
        pa = fw.replace('Rio Grande Valley','Pan American')
        ts = pa.replace('Tennessee St.','Tenn St')
        if ts in espnset or ts in trset:
            matched.add(ts)
            pairs.add((ts,team))
            tmp.add(team)
    for team in tmp:
        unmatched.remove(team)
    tmp.clear()

    for t1 in sorted(unmatched):
        ratio = 0
        t = ""
        for t2 in espnset.union(trset):
            if fuzz.ratio(t1,t2) > ratio:
                ratio = fuzz.ratio(t1,t2)
                t = t2
        matched.add(t)
        pairs.add((t,t1))
        tmp.add(t1)
    for team in tmp:
        unmatched.remove(team)
    tmp.clear()
    for other,kp in pairs:
        try:
            kp_names[kp] = espn_names[other]
        except:
            kp_names[kp] = other

teams = {}
espn_names = {}
kp_names = {}
all_teams = []
new_teams = []
all_games = []
old_games = []
new_games = []

get_team_stats()
get_old_games()
set_team_attributes()
set_game_attributes()

# Strategies 1 and 2
set_picks()

# Strategy 3
regress_winners()

test_strategy(1)
test_strategy(2)
test_strategy(3)
