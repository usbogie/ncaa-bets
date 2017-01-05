import pandas as pd
from datetime import date, timedelta
from scipy.stats.mstats import zscore
import math
import json

def get_names():
    sites = ['espn','kp','os']
    espn_names = {}
    kp_names = {}
    os_names = {}
    dicts = [espn_names,kp_names,os_names]
    for i in range(len(sites)):
        with open(sites[i] + '_data/names_dict.json', 'r+') as infile:
            dicts[i] = json.load(infile)
    return dicts

def get_ncaa_stats(year_list = [2014,2015,2016,2017]):
    years = []
    csvs = ["NCAAM_2014.csv","NCAAM_2015.csv","NCAAM_2016.csv","NCAAM_2017.csv"]
    for i in range(len(csvs)):
        if i + 2014 in year_list:
            gamesdf = pd.read_csv('ncaa_data/' + csvs[i])
            years.append(gamesdf)
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

def update_ncaa_stats():
    # Scrape data
    ncaa_2017 = pd.read_csv('ncaa_data/NCAAM_2017.csv')
    j = 0
    new_teams = []
    for name,team in teams.items():
        if team[-4] == "2017":
            new_teams.append(teams[team])
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
            name = kp_names[years[i].name[j]] + str(2014 + i)
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
        if year+2014 not in year_list:
            continue
        for i in range(len(years[year].Game_Away)):
            try:
                game = {}
                game["home"] = espn_names[years[year].Game_Home[i]] + str(2014+year)
                game["away"] = espn_names[years[year].Game_Away[i]] + str(2014+year)
                game["game_type"] = "old"
                home = teams[game["home"]]
                away = teams[game["away"]]
                game["h_score"] = years[year].Home_Score[i]
                game["a_score"] = years[year].Away_Score[i]
                game["margin"] = game["h_score"] - game["a_score"]
                game["home_winner"] = (game["margin"]/abs(game["margin"])) * .5 + .5
                if game["home_winner"] == 1:
                    game["winner"] = game["home"][:-4]
                else:
                    game["winner"] = game["away"][:-4]
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
                game["date"] = str(gameday)
                game["weekday"] = gameday.weekday()
                key = (game["home"][:-4],game["away"][:-4],game["date"])
                games[key] = game
                game["location"] = years[year].Game_Location[i]
                try:
                    home["homes"][game["location"]] += 1
                except:
                    home["homes"][game["location"]] = 1
            except:
                continue

    for name,team in teams.items():
        try:
            team["home"] = max(team["homes"],key=team["homes"].get)
            team["homes"] = None
        except:
            team["home"] = None
    for key,game in games.items():
        game["true"] = 0
        if teams[game["home"]]["home"] == game["location"]:
            game["true"] = 1
        if game["weekday"] > 1 and game["weekday"] < 7 and game["true"] == 1:
            game["weekday"] = 1
        else:
            game["weekday"] = 0

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
                key = (h,a,d)
                game = games[key]
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
                regress_games.append(game)
            except:
                continue

def set_team_attributes():
    stat_list = ["kp_o","kp_d","fto","ftd","three_o","perc3","three_d","rebo","rebd","to_poss","tof_poss"]
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
    for key,game in games.items():
        home = teams[game["home"]]
        away = teams[game["away"]]
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
            game["three_o"] = home["three_o_z"] + away["three_d_z"]
        game["three_d"] = 0
        if away["three_o_z"] > 0:
            game["three_d"] = -1 * away["three_o_z"] + home["three_d_z"]
        game["rebo"] = home["rebo_z"] - away["rebd_z"]
        game["rebd"] = home["rebd_z"] - away["rebo_z"]
        game["to"] = -1 * (home["to_poss_z"] + away["tof_poss_z"])
        game["tof"] = home["tof_poss_z"] + away["to_poss_z"]
        stat_list = ["fto","ftd","three_o","perc3","three_d","rebo","rebd","to_poss","tof_poss"]
        for stat in stat_list:
            statz = stat + "_z"
            hz = "h" + statz
            az = "a" + statz
            game[hz] = home[statz]
            game[az] = away[statz]

teams = {}
games = {}
regress_games = []
espn_names, kp_names, os_names = get_names()
get_ncaa_stats()
get_kp_stats()
get_old_games()
get_os_info()
set_team_attributes()
set_game_attributes()

rgdf = pd.DataFrame.from_dict(regress_games)
rgdf.to_csv('games.csv')
