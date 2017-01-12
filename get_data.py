import pandas as pd
from datetime import date, timedelta
from scipy.stats.mstats import zscore
import math
import json

def get_names():
    print("Getting name_dicts")
    sites = ['espn','kp', 'sb']
    espn_names = {}
    kp_names = {}
    sb_names = {}
    dicts = [espn_names,kp_names,sb_names]
    for i in range(len(sites)):
        with open(sites[i] + '_data/names_dict.json', 'r+') as infile:
            dicts[i] = json.load(infile)
    return dicts

def get_team_stats(year_list = [2014,2015,2016,2017]):
    print("Getting team stats")
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
            teams[team]["reb"] = years[i].REB[j]
            teams[team]["to_poss"] = years[i].TOP[j]
            teams[team]["tof_poss"] = years[i].TOFP[j]
            teams[team]["games"] = []

def get_kp_stats(year_list = [2014,2015,2016,2017]):
    print("Getting kp stats")
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
    print("Getting old games from ESPN")
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
                game["home"] = espn_names[years[year].Game_Home[i].strip()] + str(year_list[year])
                game["away"] = espn_names[years[year].Game_Away[i].strip()] + str(year_list[year])
                game["home_espn"] = years[year].Game_Home[i].strip()
                game["away_espn"] = years[year].Game_Away[i].strip()
                d = years[year].Game_Date[i].split("/")
                d.append(years[year].Game_Year[i])
                gameday = date(int(d[2]),int(d[0]),int(d[1]))
                game["tipoff"] = years[year].Game_Tipoff[i]
                hour = int(game["tipoff"].split(":")[0])
                central = hour-1 if hour != 0 else 23
                game["tipstring"] = (str(central%12) if central != 12 else str(12)) + ("a" if central/12 == 0 else "p")
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
                game["home_winner"] = (game["margin"]/abs(game["margin"])) * .5
                if game["home_winner"] == .5:
                    game["winner"] = game["home"][:-4]
                else:
                    game["winner"] = game["away"][:-4]
                game["true_home_game"] = 1 if not years[year].Neutral_Site[i] else 0
                game["conf"] = 1 if years[year].Conference_Competition[i] else 0
                game["weekday"] = 0 if gameday.weekday() == 1 or gameday.weekday() == 7 else 1
            except:
                continue
def get_sportsbook_info(year_list=[2014,2015,2016,2017],test=False):
    print("Getting sportsbook info from Vegas Insider")
    for game in regress_spread:
        regress_dict[game["key"]] = game
    for game in test_games:
        test_dict[game["key"]] = game
    years = []
    jsons = ['vegas_2014.json','vegas_2015.json','vegas_2016.json','vegas_2017.json']
    folder = 'vi_data/'
    for i in range(len(jsons)):
        if i + 2014 in year_list:
            ldf = pd.read_json(folder + jsons[i])
            years.append(ldf)
    for year in range(len(years)):
        for i in range(len(years[year].home)):
            try:
                a = ""
                h = sb_names[years[year].home[i]]
                a = sb_names[years[year].away[i]]
                d = years[year].date[i].split("/")
                y = year_list[year] if int(d[0]) < 8 else year_list[year] - 1
                datearray = [y,int(d[0]),int(d[1])]
                gamedateobject = date(datearray[0],datearray[1],datearray[2])
                key = str((h,a,str(gamedateobject)))
                game = {}
                game = games[key]
                game["key"] = key
                try:
                    if not test:
                        regress_dict[key]
                    else:
                        test_dict[key]
                    continue
                except:
                    pass
                if years[year].close_line[i] == "":
                    continue
                else:
                    game["spread"] = float(years[year].close_line[i])
                if game["spread"] > 65:
                    print("Found an error in vegas insider")
                if game["spread"] + game["margin"] < 0:
                    game["cover"] = game["away"][:-4]
                    game["home_cover"] = -.5
                elif game["spread"] + game["margin"] > 0:
                    game["cover"] = game["home"][:-4]
                    game["home_cover"] = .5
                else:
                    game["cover"] = "Tie"
                    game["home_cover"] = 0
                game["line_movement"] = 0 if years[year].open_line[i] == "" else game["spread"] - float(years[year].open_line[i])
                game["home_public_percentage"] = 50 if years[year].home_side_pct[i] == "" else float(years[year].home_side_pct[i])
                game["home_ats"] = years[year].home_ats[i].split("-")
                game["away_ats"] = years[year].away_ats[i].split("-")
                game["home_ats"] = 0 if game["home_ats"][0] == "0" and game["home_ats"][1] == "0" else int(game["home_ats"][0]) / (int(game["home_ats"][0])+int(game["home_ats"][1]))
                game["away_ats"] = 0 if game["away_ats"][0] == "0" and game["away_ats"][1] == "0" else int(game["away_ats"][0]) / (int(game["away_ats"][0])+int(game["away_ats"][1]))
                if math.isnan(game["spread"]):
                    continue
                if not test:
                    regress_spread.append(game)
                    regress_dict[key] = game
                else:
                    if y == year_list[year]:
                        test_games.append(game)
                        test_dict[key] = game
                # if len(teams[game["home"]]["games"]) == 0:
                #     teams[game["home"]]["games"].append(game["key"])
                # else:
                #     if game["key"] in teams[game["home"]]["games"]:
                #         continue
                #     for index,key in enumerate(teams[game["home"]]["games"]):
                #         datearray = games[key]["date"].split("-")
                #         dateobject = date(int(datearray[0]),int(datearray[1]),int(datearray[2]))
                #         if gamedateobject < dateobject:
                #             teams[game["home"]]["games"][index] = game["key"]
                #             for index2 in range(index+1,len(teams[game["home"]]["games"])):
                #                 tmp = teams[game["home"]]["games"][index2]
                #                 teams[game["home"]]["games"][index2] = key
                #                 key = tmp
                #             teams[game["home"]]["games"].append(key)
                #             break
                #         if index == len(teams[game["home"]]["games"]) - 1:
                #             teams[game["home"]]["games"].append(game["key"])
                # if len(teams[game["away"]]["games"]) == 0:
                #     teams[game["away"]]["games"].append(game["key"])
                # else:
                #     if game["key"] in teams[game["home"]]["games"]:
                #         continue
                #     for index,key in enumerate(teams[game["away"]]["games"]):
                #         datearray = games[key]["date"].split("-")
                #         dateobject = date(int(datearray[0]),int(datearray[1]),int(datearray[2]))
                #         if gamedateobject < dateobject:
                #             teams[game["away"]]["games"][index] = game["key"]
                #             for index2 in range(index+1,len(teams[game["away"]]["games"])):
                #                 tmp = teams[game["away"]]["games"][index2]
                #                 teams[game["away"]]["games"][index2] = key
                #                 key = tmp
                #             teams[game["away"]]["games"].append(key)
                #             break
                #         if index == len(teams[game["away"]]["games"]) - 1:
                #             teams[game["away"]]["games"].append(game["key"])
            except:
                continue

def get_new_games():
    print("Getting new games")
    gamesdf = pd.read_csv('espn_data/upcoming_games.csv')
    upcoming_games = {}
    for i in range(len(gamesdf.Game_Away)):
        try:
            game = {}
            game["home"] = espn_names[gamesdf.Game_Home[i].strip()] + str(2017)
            game["away"] = espn_names[gamesdf.Game_Away[i].strip()] + str(2017)
            game["home_espn"] = gamesdf.Game_Home[i].strip()
            game["away_espn"] = gamesdf.Game_Away[i].strip()
            d = gamesdf.Game_Date[i].split("/")
            d.append(gamesdf.Game_Year[i])
            gameday = date(int(d[2]),int(d[0]),int(d[1]))
            game["tipoff"] = gamesdf.Game_Tipoff[i]
            hour = int(game["tipoff"].split(":")[0])
            central = hour-1 if hour != 0 else 23
            game["tipstring"] = "{}:{} {}M CT".format((str(central%12) if central != 12 else str(12)),game["tipoff"].split(":")[1],("A" if central/12 == 0 else "P"))
            if hour < 6:
                gameday -= timedelta(days=1)
            game["date"] = str(gameday)
            game["true_home_game"] = 1 if not gamesdf.Neutral_Site[i] else 0
            game["conf"] = 1 if gamesdf.Conference_Competition[i] else 0
            game["weekday"] = 0 if gameday.weekday() == 1 or gameday.weekday() == 7 else 1
            key = str((game["home"][:-4],game["away"][:-4]))
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
            key = str((home,away))
            new_game = upcoming_games[key]
            try:
                new_dict[key]
                continue
            except:
                pass
            new_game['key'] = key
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
            new_dict[key] = new_game
        except:
            print("In sportsbook, no game matched:",sb_names[game["home"]],sb_names[game["away"]])

    with open('vi_data/vegas_today.json','r') as infile:
        vegas_info = json.load(infile)
    for game in vegas_info:
        try:
            home = sb_names[game['home']]
            away = sb_names[game['away']]
            key = str((home,away))
            new_game = new_dict[key]
            new_game["line_movement"] = 0 if game["open_line"] == "" else new_game["spread"] - float(game["open_line"])
            new_game["home_public_percentage"] = 50 if game["home_side_pct"] == "" else float(game["home_side_pct"])
            new_game["home_ats"] = game["home_ats"].split("-")
            new_game["away_ats"] = game["away_ats"].split("-")
            new_game["home_ats"] = 0 if new_game["home_ats"][0] == "0" and new_game["home_ats"][1] == "0" else int(new_game["home_ats"][0]) / (int(new_game["home_ats"][0])+int(new_game["home_ats"][1]))
            new_game["away_ats"] = 0 if new_game["away_ats"][0] == "0" and new_game["away_ats"][1] == "0" else int(new_game["away_ats"][0]) / (int(new_game["away_ats"][0])+int(new_game["away_ats"][1]))
            new_games.append(new_game)
            print("Found:",home,away)
        except:
            print("In vegas info, no game matched:",sb_names[game["home"]],sb_names[game["away"]])

def set_team_attributes():
    print("Setting team attributes")
    stat_list = ["kp_o","kp_d","kp_t","fto","ftd","three_o","three_d","rebo","rebd","reb","to_poss","tof_poss"]
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

def set_game_attributes(new = False,test = False):
    all_games = []
    if not new and not test:
        data = regress_spread
        print("Setting game attributes")
    elif new:
        data = new_games
        print("Setting game attributes for new games")
    elif test:
        data = test_games
        print("Setting game attributes for test games")
    for i,game in enumerate(data):
        home = teams[game["home"]]
        away = teams[game["away"]]
        game["home_off_adv"] = home["kp_o_z"] + away["kp_d_z"]
        game["away_off_adv"] = home["kp_d_z"] + away["kp_o_z"]
        game["home_tempo_z"] = home["kp_t_z"]
        game["away_tempo_z"] = away["kp_t_z"]
        game["home_three_adv"] = 1 if home["three_o_z"] > 1 else 0
        game["home_three_d_adv"] = 1 if home["three_d_z"] < 1 and away["three_o_z"] > 1 else 0
        game["away_three_adv"] = 1 if away["three_o_z"] > 1 else 0
        game["away_three_d_adv"] = 1 if away["three_d_z"] < 1 and home["three_o_z"] > 1 else 0
        game["home_reb_adv"] = home["reb"] - away["reb"]
        game["to"] = 1 if home["to_poss_z"] > 1 and away["tof_poss_z"] > 1 else 0
        game["tof"] = 1 if home["tof_poss_z"] > 1 and away["to_poss_z"] > 1 else 0
        game["weekday"] = 0 if game["weekday"] == -1 else game["weekday"]
def update_all():
    year_list = [2014,2015]

    # Updates team dictionary
    # get_team_stats(year_list) # Comment if team_stats hasn't been updated
    # get_kp_stats(year_list) # Comment if kenpom hasn't been updated

    # Updates games dictionary
    # get_old_games() # Comment if game_info hasn't been updated

    # Gets games that will be regressed
    get_sportsbook_info(year_list) # Comment if vegas hasn't been updated
    get_sportsbook_info([2016],test=True)

    get_new_games() # Comment if upcoming_games and game_lines hasn't been updated

    # Updates team dictionary
    set_team_attributes() # Comment if teams won't change

    # Updates games dictionary
    # Updates regress games
    set_game_attributes() # Always run
    set_game_attributes(new = True) # Comment if new games aren't being added
    set_game_attributes(test = True) # Comment if test games aren't being added

teams = {}
games = {}
regress_spread = []
new_games = []
test_games = []
with open('teams.json','r') as infile:
    teams = json.load(infile)
with open('games.json','r') as infile:
    games = json.load(infile)
# with open('regress_spread.json','r') as infile:
#     regress_spread = json.load(infile)
# with open('test_games.json','r') as infile:
#     test_games = json.load(infile)
regress_dict = {}
new_dict = {}
test_dict = {}

espn_names, kp_names, sb_names = get_names()
update_all()

# with open('teams.json', 'w') as outfile:
#     json.dump(teams, outfile)
# with open('games.json','w') as outfile:
#     json.dump(games, outfile)
with open('regress_spread.json','w') as outfile:
    json.dump(regress_spread,outfile)
with open('new_games.json','w') as outfile:
    json.dump(new_games,outfile)
with open('test_games.json','w') as outfile:
    json.dump(test_games,outfile)
