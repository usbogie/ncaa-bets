import pandas as pd
from datetime import date, timedelta
from scipy.stats.mstats import zscore
import math
import json

def get_names():
    sites = ['espn','kp','os','sb']
    espn_names = {}
    kp_names = {}
    os_names = {}
    sb_names = {}
    dicts = [espn_names,kp_names,os_names,sb_names]
    for i in range(len(sites)):
        with open(sites[i] + '_data/names_dict.json', 'r+') as infile:
            dicts[i] = json.load(infile)
    return dicts

def get_team_stats(year_list = [2014,2015,2016,2017]):
    years = []
    csvs = ["team_stats14.csv","team_stats15.csv","team_stats16.csv","team_stats17.csv"]
    for i in range(len(csvs)):
        if i + 2014 in year_list:
            gamesdf = pd.read_csv('tr_data/' + csvs[i])
            years.append(gamesdf)
    for i in range(len(years)):
        teams_count = len(years[i])
        for j in range(teams_count):
            team = years[i].Name[j] + str(year_list[i])
            teams[team] = {}
            teams[team]["name"] = years[i].Name[j]
            teams[team]["year"] = str(year_list[i])
            teams[team]["fto"] = years[i].FTO[j]
            teams[team]["ftd"] = years[i].FTD[j]
            teams[team]["poss"] = years[i].POSS[j]
            teams[team]["three_o"] = years[i].Three_O[j]/teams[team]["poss"]
            teams[team]["three_d"] = years[i].Three_D[j]
            teams[team]["rebo"] = years[i].REBO[j]
            teams[team]["rebd"] = years[i].REBD[j]
            teams[team]["to_poss"] = years[i].TOP[j]
            teams[team]["tof_poss"] = years[i].TOFP[j]

def update_all():
    # get_team_stats()

    # get_kp_stats()

    #get_old_games()

    #get_os_info()

    get_new_games()

    #get_test_games([2016])

    set_team_attributes()
    set_game_attributes()

def get_kp_stats(year_list = [2014,2015,2016,2017]):
    years = []
    jsons = ['kenpom14.json','kenpom15.json','kenpom16.json','kenpom17.json']
    for i in range(len(jsons)):
        if i + 2014 in year_list:
            kpdf = pd.read_json('kp_data/' + jsons[i])
            years.append(kpdf)
    for i in range(len(years)):
        teams_count = len(years[i])
        for j in range(teams_count):
            name = kp_names[years[i].name[j]] + str(year_list[i])
            teams[name]["kp_o"] = years[i].adjO[j]
            teams[name]["kp_d"] = years[i].adjD[j]
            teams[name]["kp_t"] = years[i].adjT[j]

def get_old_games(year_list = [2014,2015,2016,2017]):
    years = []
    csvs = ["game_info2014.csv","game_info2015.csv","game_info2016.csv","game_info2017.csv"]
    for i in range(len(csvs)):
        if i + 2014 in year_list:
            gamesdf = pd.read_csv('espn_data/' + csvs[i])
            years.append(gamesdf)
    for year in range(len(years)):
        for i in range(len(years[year].Game_Away)):
            try:
                game = {}
                game["home"] = espn_names[years[year].Game_Home[i]] + str(year_list[year])
                game["away"] = espn_names[years[year].Game_Away[i]] + str(year_list[year])
                d = years[year].Game_Date[i].split("/")
                d.append(years[year].Game_Year[i])
                gameday = date(int(d[2]),int(d[0]),int(d[1]))
                game["tipoff"] = years[year].Game_Tipoff[i]
                hour = int(game["tipoff"].split(":")[0])
                central = hour-1 if hour != 0 else 23
                game["tipstring"] = (str(central%12) if central != 12 else str(12)) + ("a" if central/12 == 0 else "p")
                if hour < 6:
                    gameday -= timedelta(days=1)
                game["date"] = str(gameday)
                key = str((game["home"][:-4],game["away"][:-4],game["date"]))
                if key not in set(games.keys()):
                    games[key] = game
                else:
                    continue
                home = teams[game["home"]]
                away = teams[game["away"]]
                game["season"] = str(year_list[year])
                game["h_score"] = float(years[year].Home_Score[i])
                game["a_score"] = float(years[year].Away_Score[i])
                game["total_score"] = float(game["h_score"] + game["a_score"])
                game["margin"] = float(game["h_score"] - game["a_score"])
                game["home_winner"] = (game["margin"]/abs(game["margin"])) * .5 + .5
                if game["home_winner"] == 1:
                    game["winner"] = game["home"][:-4]
                else:
                    game["winner"] = game["away"][:-4]
                game["true"] = 1 if not years[year].Neutral_Site[i] else 0
                game["conf"] = 1 if years[year].Conference_Competition[i] else 0
                game["weekday"] = 0 if gameday.weekday() == 1 or gameday.weekday() == 7 else 1
            except:
                continue

def get_os_info(year_list = [2014,2015,2016,2017]):
    years = []
    jsons = ['oddsshark14.json','oddsshark15.json','oddsshark16.json','oddsshark17.json']
    for i in range(len(jsons)):
        if i + 2014 in year_list:
            osdf = pd.read_json('os_data/' + jsons[i])
            years.append(osdf)
    for year in range(len(years)):
        for i in range(len(years[year].home)):
            try:
                h = os_names[years[year].home[i]]
                a = os_names[years[year].away[i]]
                d = str(years[year].date[i])
                d = d.split()[0]
                key = str((h,a,d))
                game = games[key]
                if years[year].spread[i] == "Ev":
                    game["spread"] = 0
                else:
                    game["spread"] = float(years[year].spread[i])
                game["total"] = float(years[year].total[i])
                if years[year].ats[i] == 'L':
                    game["cover"] = game["away"][:-4]
                    game["home_cover"] = 0
                elif years[year].ats[i] == 'W':
                    game["cover"] = game["home"][:-4]
                    game["home_cover"] = 1
                else:
                    game["cover"] = "Tie"
                    game["home_cover"] = .5
                if years[year].o[i] == 'O':
                    game["over"] = 1
                elif years[year].o[i] == 'U':
                    game["over"] = 0
                else:
                    game["over"] = .5
                if math.isnan(game["spread"]) or math.isnan(game["total"]):
                    continue
                if abs(game["spread"] + game["margin"]) <= 3:
                    game["home_cover"] = (game["home_cover"] + .5) / 2
                regress_spread.append(game)
            except:
                continue
def get_test_games(year_list = [2017]):
    test_dict = {}
    for key,game in games.items():
        if int(game["season"]) in year_list:
            test_dict[key] = game
    years = []
    jsons = ['oddsshark14.json','oddsshark15.json','oddsshark16.json','oddsshark17.json']
    for i in range(len(jsons)):
        if i + 2014 in year_list:
            osdf = pd.read_json('os_data/' + jsons[i])
            years.append(osdf)
    for year in range(len(years)):
        for i in range(len(years[year].home)):
            try:
                h = os_names[years[year].home[i]]
                a = os_names[years[year].away[i]]
                d = str(years[year].date[i])
                d = d.split()[0]
                key = str((h,a,d))
                game = test_dict[key]
                if years[year].spread[i] == "Ev":
                    game["spread"] = 0
                else:
                    game["spread"] = float(years[year].spread[i])
                game["total"] = float(years[year].total[i])
                if years[year].ats[i] == 'L':
                    game["cover"] = game["away"][:-4]
                    game["home_cover"] = 0
                elif years[year].ats[i] == 'W':
                    game["cover"] = game["home"][:-4]
                    game["home_cover"] = 1
                else:
                    game["cover"] = "Tie"
                    game["home_cover"] = .5
                if math.isnan(game["spread"]) or math.isnan(game["total"]):
                    continue
                test_games.append(game)
            except:
                continue
def get_new_games():
    gamesdf = pd.read_csv('espn_data/upcoming_games.csv')
    upcoming_games = {}
    for i in range(len(gamesdf.Game_Away)):
        try:
            game = {}
            game["home"] = espn_names[gamesdf.Game_Home[i].strip()] + str(2017)
            game["away"] = espn_names[gamesdf.Game_Away[i].strip()] + str(2017)
            d = gamesdf.Game_Date[i].split("/")
            d.append(gamesdf.Game_Year[i])
            gameday = date(int(d[2]),int(d[0]),int(d[1]))
            game["tipoff"] = gamesdf.Game_Tipoff[i]
            hour = int(game["tipoff"].split(":")[0])
            central = hour-1 if hour != 0 else 23
            game["tipstring"] = (str(central%12) if central != 12 else str(12)) + ("a" if central/12 == 0 else "p")
            if hour < 6:
                gameday -= timedelta(days=1)
            game["date"] = str(gameday)
            game["true"] = 1 if not gamesdf.Neutral_Site[i] else 0
            key = str((game["home"][:-4],game["away"][:-4],game["date"]))
            upcoming_games[key] = game
        except:
            print(gamesdf.Game_Home[i],gamesdf.Game_Away[i])
            continue
    with open('sb_data/game_lines.json','r') as infile:
        game_lines = json.load(infile)
    for game in game_lines:
        try:
            home = sb_names[game['home']]
            away = sb_names[game['away']]
            d = game['date'].split()
            months = ["Jan","Feb","Mar","Apr","Nov","Dec"]
            j = 0
            for m in months:
                j += 1
                if m == d[0][:3]:
                    if j > 4:
                        d[0] = j + 6
                    else:
                        d[0] = j
                    break
            gameday = str(date(int(d[2]),d[0],int(d[1][:-1])))
            key = str((home,away,gameday))
            new_game = upcoming_games[key]
            new_game['spread_away'] = (float(game['spread_away'][:-6]),float(game['spread_away'][-5:-1]))
            new_game['spread_home'] = (float(game['spread_home'][:-6]),float(game['spread_home'][-5:-1]))
            new_game['spread'] = new_game['spread_home'][0]
            if game['total_over'] == "-":
                new_game['total_over'] = None
                new_game['total_under'] = None
                new_game['total'] = None
            else:
                over = game['total_over'].split()[1]
                under = game['total_under'].split()[1]
                new_game['total_over'] = (float(over[:-6]),float(over[-5:-1]))
                new_game['total_under'] = (float(under[:-6]),float(under[-5:-1]))
                new_game['total'] = new_game['total_over'][0]
            new_games.append(new_game)
        except:
            print("No game matched:",home,away)

def set_team_attributes():
    stat_list = ["kp_o","kp_d","kp_t","fto","ftd","three_o","three_d","rebo","rebd","to_poss","tof_poss"]
    for stat in stat_list:
        set_zscores(stat)

def set_zscores(stat):
    l = []
    for name,team in teams.items():
        l.append(team[stat])
    z = zscore(l)
    i=0
    stat_z = stat + "_z"
    for name,team in teams.items():
        team[stat_z] = z[i]
        i += 1

def set_game_attributes():
    all_games = []
    for game in regress_spread:
        all_games.append(game)
    for game in new_games:
        all_games.append(game)
    for game in test_games:
        all_games.append(game)
    for game in all_games:
        home = teams[game["home"]]
        away = teams[game["away"]]
        game["o"] = home["kp_o_z"] + away["kp_d_z"]
        game["d"] = -1 * (home["kp_d_z"] + away["kp_o_z"])
        game["htz"] = home["kp_t_z"]
        game["atz"] = away["kp_t_z"]
        game["fto"] = 0
        game["fto"] = home["fto_z"] + away["ftd_z"]
        game["ftd"] = -1 * (home["ftd_z"] + away["fto_z"])
        game["three_o"] = home["three_o_z"]
        game["three_d"] = -1 * away["three_o_z"]
        game["h3d"] = 1 if home["three_o_z"] > 1 and away["three_d_z"] > 1 else 0
        game["a3d"] = 1 if away["three_o_z"] > 1 and home["three_d_z"] > 1 else 0
        game["rebo"] = home["rebo_z"] - away["rebd_z"]
        game["rebd"] = home["rebd_z"] - away["rebo_z"]
        game["reb"] = 1 if game["rebo"] + game["rebd"] > 1 else 0
        game["to"] = 1 if home["to_poss_z"] + away["tof_poss_z"] > 1 else 0
        game["tof"] = 1 if home["tof_poss_z"] + away["to_poss_z"] > 1 else 0

with open('teams.json','r') as infile:
    teams = json.load(infile)
with open('games.json','r') as infile:
    games = json.load(infile)
# games = {}
with open('regress_spread.json','r') as infile:
    regress_spread = json.load(infile)
# regress_spread = []
new_games = []
test_games = []
espn_names, kp_names, os_names, sb_names = get_names()
update_all()

with open('teams.json', 'w') as outfile:
    json.dump(teams, outfile)
with open('games.json','w') as outfile:
    json.dump(games, outfile)
with open('regress_spread.json','w') as outfile:
    json.dump(regress_spread,outfile)
with open('new_games.json','w') as outfile:
    json.dump(new_games,outfile)
with open('test_games.json','w') as outfile:
    json.dump(test_games,outfile)
