import os
import helpers as h

this_season = h.this_season
path = h.path

def get():
    data_path = os.path.join(path,'..','data','rankings','rankings.txt')
    f2 = open(data_path, 'w')
    rankings = []
    for key,team in h.teams.items():
        try:
            team["adj_em"] = team["adj_ortg"][-1] - team["adj_drtg"][-1]
        except:
            continue
    em_list = []
    for key,team in h.teams.items():
        try:
            if team["year"] == this_season:
                em_list.append((team["adj_em"],team["name"],team["adj_ortg"][-1],team["adj_drtg"][-1]))
        except:
            continue
    for idx,team in enumerate(sorted(em_list,reverse=True)):
        rankings.append("{} {}\tEM: {}\tORTG: {}\tDRTG: {}\n".format(str(idx+1).ljust(4),team[1].ljust(25),str(round(team[0]/2,2)).ljust(8),str(round(team[2],2)).ljust(8),str(round(team[3],2)).ljust(8)))
    f2.writelines(rankings)