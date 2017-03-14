from fuzzywuzzy import fuzz
import pandas as pd
import json

def get_cbbr_names():
    cbbrdf = pd.read_csv('cbbref_data/game_info2017.csv')
    cbbrdf2 = pd.read_csv('cbbref_data/game_info2013.csv')
    cbbrset = set()
    teamset = set()
    espnset = set()
    for kp,espn in sb_names.items():
        teamset.add(espn)
        espnset.add(espn)
    for team in cbbrdf.team:
        cbbrset.add(team)
    for team in cbbrdf2.team:
        cbbrset.add(team)
    tmp = set()
    for team in cbbrset:
        if team in espnset:
            cbbr_names[team] = team
            tmp.add(team)
        else:
            dicts = [cbbr_names,sb_names,kp_names]
            for d in dicts:
                try:
                    cbbr_names[team] = d[team]
                    tmp.add(team)
                    break
                except:
                    pass
    for team in tmp:
        cbbrset.remove(team)
    tmp.clear()
    for team in list(kp_names.keys()):
        teamset.add(team)
    for team in list(sb_names.keys()):
        teamset.add(team)
    check_later = set()
    # for team in cbbrset:
    #     p = team.replace('.','')
    #     ut = p.replace('Texas','UT')
    #     chi = ut.replace('IL','CHI')
    #     d = chi.replace('-',' ')
    #     u = d.replace(' University','')
    #     pa = u.replace(' (PA)','')
    #     s = pa.replace('Virginia','VA')
    #     if s in teamset:
    #         check_later.add((team,s))
    #         tmp.add(team)
    # for team in tmp:
    #     cbbrset.remove(team)
    # tmp.clear()
    for team in sorted(cbbrset):
        ratio = 0
        t = ""
        for t2 in teamset:
            if fuzz.ratio(team,t2) > ratio:
                ratio = fuzz.ratio(team,t2)
                t = t2
        print(team,t,ratio)
        s = input("Type 'y' if names match")
        if s == 'y':
            check_later.add((team,t))
        else:
            espn_name = input("Type ESPN name:")
            check_later.add((team,espn_name))
    for team,other in check_later:
        if other in espnset:
            cbbr_names[team] = other
        else:
            try:
                cbbr_names[team] = kp_names[other]
            except:
                cbbr_names[team] = sb_names[other]
    print(len(cbbr_names.keys()))
    with open('cbbref_data/new_names_dict.json', 'w+') as outfile:
        json.dump(cbbr_names, outfile)

def get_tr_names():
    trdf = pd.read_csv('tr_data/xteam_stats2017.csv')
    trset = set()
    teamset = set()
    espnset = set()
    for sb,espn in sb_names.items():
        teamset.add(espn)
        espnset.add(espn)
    for team in trdf.Name:
        trset.add(team)
    tmp = set()
    for team in trset:
        if team in espnset:
            tr_names[team] = team
            tmp.add(team)
        else:
            dicts = [tr_names,sb_names,kp_names,cbbr_names]
            for d in dicts:
                try:
                    tr_names[team] = d[team]
                    tmp.add(team)
                    break
                except:
                    pass
    for team in tmp:
        trset.remove(team)
    tmp.clear()
    for team in list(kp_names.keys()):
        teamset.add(team)
    for team in list(sb_names.keys()):
        teamset.add(team)
    for team in list(cbbr_names.keys()):
        teamset.add(team)
    check_later = set()
    # for team in trset:
    #     p = team.replace('.','')
    #     ut = p.replace('Texas','UT')
    #     chi = ut.replace('IL','CHI')
    #     d = chi.replace('-',' ')
    #     u = d.replace(' University','')
    #     pa = u.replace(' (PA)','')
    #     s = pa.replace('Virginia','VA')
    #     if s in teamset:
    #         check_later.add((team,s))
    #         tmp.add(team)
    # for team in tmp:
    #     trset.remove(team)
    # tmp.clear()
    for team in sorted(trset):
        ratio = 0
        t = ""
        for t2 in teamset:
            if fuzz.ratio(team,t2) > ratio:
                ratio = fuzz.ratio(team,t2)
                t = t2
        print(team,t,ratio)
        s = input("Type 'y' if names match")
        if s == 'y':
            check_later.add((team,t))
        else:
            espn_name = input("Type ESPN name:")
            check_later.add((team,espn_name))
    for team,other in check_later:
        if other in espnset:
            tr_names[team] = other
        else:
            try:
                tr_names[team] = kp_names[other]
            except:
                try:
                    tr_names[team] = sb_names[other]
                except:
                    tr_names[team] = cbbr_names[other]
    print(len(tr_names.keys()))
    with open('tr_data/new_names_dict.json', 'w+') as outfile:
        json.dump(tr_names, outfile)

def get_sb_names():
    sbdf = pd.read_json('sb_data/game_lines.json')
    sbset = set()
    teamset = set()
    espnset = set()
    for sb,espn in sb_names.items():
        teamset.add(espn)
        espnset.add(espn)
    for team in sbdf.home:
        sbset.add(team)
    for team in sbdf.away:
        sbset.add(team)
    tmp = set()
    for team in sbset:
        if team in espnset:
            sb_names[team] = team
            tmp.add(team)
        else:
            dicts = [sb_names,tr_names,kp_names,cbbr_names]
            for d in dicts:
                try:
                    sb_names[team] = d[team]
                    tmp.add(team)
                    break
                except:
                    pass
    for team in tmp:
        sbset.remove(team)
    tmp.clear()
    for team in list(kp_names.keys()):
        teamset.add(team)
    for team in list(tr_names.keys()):
        teamset.add(team)
    for team in list(cbbr_names.keys()):
        teamset.add(team)
    check_later = set()
    # for team in sbset:
    #     p = team.replace('.','')
    #     ut = p.replace('Texas','UT')
    #     chi = ut.replace('IL','CHI')
    #     d = chi.replace('-',' ')
    #     u = d.replace(' University','')
    #     pa = u.replace(' (PA)','')
    #     s = pa.replace('Virginia','VA')
    #     if s in teamset:
    #         check_later.add((team,s))
    #         tmp.add(team)
    # for team in tmp:
    #     sbset.remove(team)
    # tmp.clear()
    for team in sorted(sbset):
        ratio = 0
        t = ""
        for t2 in teamset:
            if fuzz.ratio(team,t2) > ratio:
                ratio = fuzz.ratio(team,t2)
                t = t2
        print(team,t,ratio)
        s = input("Type 'y' if names match")
        if s == 'y':
            check_later.add((team,t))
        else:
            espn_name = input("Type ESPN name:")
            check_later.add((team,espn_name))
    for team,other in check_later:
        if other in espnset:
            sb_names[team] = other
        else:
            try:
                sb_names[team] = kp_names[other]
            except:
                try:
                    sb_names[team] = tr_names[other]
                except:
                    sb_names[team] = cbbr_names[other]
    print(len(sb_names.keys()))
    with open('sb_data/new_names_dict.json', 'w+') as outfile:
        json.dump(sb_names, outfile)

def get_espn_names():
    years = []
    csvs = ["game_info2012.csv","game_info2013.csv","game_info2014.csv","game_info2015.csv","game_info2016.csv","game_info2017.csv"]
    for i, csv in enumerate(csvs):
        gamesdf = pd.read_csv('espn_data/' + csv)
        years.append(gamesdf)
    espn_set = set()
    for idx, year in enumerate(years):
        for i, row in year.iterrows():
            espn_set.add(row.Game_Home.strip())
            espn_set.add(row.Game_Away.strip())

    for alt,reg in espn_names.items():
        if alt in espn_set:
            espn_set.remove(alt)
        if reg in espn_set:
            espn_set.remove(reg)

    tmp = set()
    for team in espn_set:
        dicts = [sb_names,tr_names,kp_names,cbbr_names]
        for d in dicts:
            try:
                espn_names[team] = d[team]
                tmp.add(team)
                break
            except:
                pass
    for team in tmp:
        espn_set.remove(team)
    tmp.clear()

    teamset = set()
    for alt,reg in list(espn_names.items()):
        teamset.add(alt)
        teamset.add(reg)
    for team in list(kp_names.keys()):
        teamset.add(team)
    for team in list(tr_names.keys()):
        teamset.add(team)
    for team in list(cbbr_names.keys()):
        teamset.add(team)
    for team in list(sb_names.keys()):
        teamset.add(team)
    check_later = set()

    print(len(espn_set))
    for team in sorted(espn_set):
        ratio = 0
        t = ""
        for t2 in teamset:
            if fuzz.ratio(team,t2) > ratio:
                ratio = fuzz.ratio(team,t2)
                t = t2
        print(team,t,ratio)
        s = input("Type 'y' if names match, 'n' if not d1")
        if s == 'y':
            check_later.add((team,t))
        elif s == 'n':
            pass
        else:
            espn_name = input("Type ESPN name:")
            check_later.add((team,espn_name))
    for team,other in check_later:
        if other in espn_set:
            espn_names[team] = other
        else:
            try:
                espn_names[team] = kp_names[other]
            except:
                try:
                    espn_names[team] = tr_names[other]
                except:
                    espn_names[team] = cbbr_names[other]
    print(len(espn_names.keys()))

    with open('espn_data/new_names_dict.json', 'w+') as outfile:
        json.dump(espn_names, outfile)

with open('kp_data/new_names_dict.json','r') as infile:
    kp_names = json.load(infile)
with open('sb_data/new_names_dict.json','r') as infile:
    sb_names = json.load(infile)
with open('cbbref_data/new_names_dict.json','r') as infile:
    cbbr_names = json.load(infile)
with open('tr_data/new_names_dict.json','r') as infile:
    tr_names = json.load(infile)
with open('espn_data/new_names_dict.json','r') as infile:
    espn_names = json.load(infile)

bracket = pd.read_csv('bracket.csv')
teams = list(bracket.Teams)
for i in range(len(teams)):
    teams[i] = teams[i].split(' ')[1:]
    new_team = ''
    for word in teams[i]:
        new_team += word + ' '
    teams[i] = new_team[:-1]

get_espn_names()

bracket_names = {}

bset = set()
teamset = set()
espnset = set()
for sb,espn in sb_names.items():
    teamset.add(espn)
    espnset.add(espn)
for team in teams:
    bset.add(team)
tmp = set()
for team in bset:
    if team in espnset:
        bracket_names[team] = team
        tmp.add(team)
    else:
        dicts = [tr_names,kp_names,cbbr_names]
        for d in dicts:
            try:
                bracket_names[team] = d[team]
                tmp.add(team)
                break
            except:
                pass
for team in tmp:
    bset.remove(team)
tmp.clear()
for team in list(kp_names.keys()):
    teamset.add(team)
for team in list(tr_names.keys()):
    teamset.add(team)
for team in list(cbbr_names.keys()):
    teamset.add(team)
check_later = set()
# for team in bset:
#     p = team.replace('.','')
#     ut = p.replace('Texas','UT')
#     chi = ut.replace('IL','CHI')
#     d = chi.replace('-',' ')
#     u = d.replace(' University','')
#     pa = u.replace(' (PA)','')
#     s = pa.replace('Virginia','VA')
#     if s in teamset:
#         check_later.add((team,s))
#         tmp.add(team)
# for team in tmp:
#     bset.remove(team)
# tmp.clear()
for team in sorted(bset):
    ratio = 0
    t = ""
    for t2 in teamset:
        if fuzz.ratio(team,t2) > ratio:
            ratio = fuzz.ratio(team,t2)
            t = t2
    print(team,t,ratio)
    s = input("Type 'y' if names match")
    if s == 'y':
        check_later.add((team,t))
    else:
        espn_name = input("Type ESPN name:")
        check_later.add((team,espn_name))
for team,other in check_later:
    if other in espnset:
        bracket_names[team] = other
    else:
        try:
            bracket_names[team] = kp_names[other]
        except:
            try:
                bracket_names[team] = tr_names[other]
            except:
                bracket_names[team] = cbbr_names[other]
print(len(bracket_names.keys()))
with open('bracket_names_dict.json', 'w+') as outfile:
    json.dump(bracket_names, outfile)
