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

with open('kp_data/new_names_dict.json','r') as infile:
    kp_names = json.load(infile)
with open('sb_data/new_names_dict.json','r') as infile:
    sb_names = json.load(infile)
with open('cbbref_data/new_names_dict.json','r') as infile:
    cbbr_names = json.load(infile)
with open('tr_data/new_names_dict.json','r') as infile:
    tr_names = json.load(infile)

get_cbbr_names()
