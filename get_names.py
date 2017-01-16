import pandas as pd
from fuzzywuzzy import fuzz
import json

def get_sb_names(name_list):
    sbdf = pd.read_json('sb_data/game_lines.json')
    vidf = pd.read_json('vi_data/vegas_today.json')
    sbset = set()
    teamset = set()
    trset = set()
    for team in sbdf.home:
        sbset.add(team)
    for team in sbdf.away:
        sbset.add(team)
    for team in vidf.home:
        sbset.add(team)
    for team in vidf.away:
        sbset.add(team)
    for name in name_list:
        teamset.add(name)
        trset.add(name)
    tmp = set()
    for team in sbset:
        if team in trset:
            sb_names[team] = team
            tmp.add(team)
        else:
            dicts = [sb_names,espn_names,kp_names]
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
    for team in list(espn_names.keys()):
        teamset.add(team)
    for team in list(kp_names.keys()):
        teamset.add(team)
    check_later = set()
    for team in sbset:
        utsa = team.replace("Texas San Antonio","TX-San Ant")
        if utsa in teamset:
            tmp.add(team)
            check_later.add((team,utsa))
    for team in tmp:
        sbset.remove(team)
    tmp.clear()
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
            tr_name = input("Type tr name:")
            check_later.add((team,tr_name))
    for team,other in check_later:
        if other in trset:
            sb_names[team] = other
        else:
            try:
                sb_names[team] = espn_names[other]
            except:
                sb_names[team] = kp_names[other]
    with open('sb_data/names_dict.json', 'w+') as outfile:
        json.dump(sb_names, outfile)
    with open('vi_data/names_dict.json', 'w+') as outfile:
        json.dump(sb_names, outfile)

trdf = pd.read_csv("tr_data/team_stats14.csv")
with open('espn_data/names_dict.json','r') as infile:
    espn_names = json.load(infile)
with open('kp_data/names_dict.json','r') as infile:
    kp_names = json.load(infile)
with open('sb_data/names_dict.json','r') as infile:
    sb_names = json.load(infile)
get_sb_names(trdf.Name)
