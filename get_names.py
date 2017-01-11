import pandas as pd
from fuzzywuzzy import fuzz
import json

def get_espn_names(name_list):
    team_pairs = set()
    team_set = set()
    for team in name_list:
        team_set.add(team)
    team_set2 = set()
    csvs = ["game_info2014.csv","game_info2015.csv","game_info2016.csv","game_info2017.csv"]
    for i in range(len(csvs)):
        gamesdf = pd.read_csv('espn_data/' + csvs[i])
        for team in gamesdf.Game_Home:
            team_set2.add(team)
        for team in gamesdf.Game_Away:
            team_set2.add(team)
    tmp = set()
    for team in team_set2:
        if team in team_set:
            tmp.add(team)
            team_set.remove(team)
            team_pairs.add((team,team))
    for team in tmp:
        team_set2.remove(team)
    tmp.clear()
    tmp = set()
    for team in team_set2:
        eastern = team.replace("Eastern","E")
        wash = eastern.replace("Washington","Washingtn")
        state = wash.replace("State","St")
        if state in team_set:
            team_set.remove(state)
            tmp.add(team)
            team_pairs.add((state,team))
        state2 = team.replace("St","State")
        sac = state2.replace("Sacramento","Sac")
        nw = sac.replace("Northwestern", "NW")
        app = nw.replace("Appalachian","App")
        es = app.replace("-Eastern Shore"," ES")
        fw = es.replace("Fort Wayne","IPFW")
        miss = fw.replace("Mississippi","Miss")
        if miss in team_set:
            team_set.remove(miss)
            tmp.add(team)
            team_pairs.add((miss,team))
        tenn = team.replace("Tennessee","TN")
        fran = tenn.replace("Francis","Fran")
        if fran in team_set:
            team_set.remove(fran)
            tmp.add(team)
            team_pairs.add((fran,team))
        s = team.replace("'s","s")
        saint = s.replace("Saint","St")
        st = saint.replace("St.","St")
        if st in team_set:
            team_set.remove(st)
            tmp.add(team)
            team_pairs.add((st,team))
        cent = team.replace("Cent","Central")
        car = cent.replace(" Carolina","C")
        if car in team_set:
            team_set.remove(car)
            tmp.add(team)
            team_pairs.add((car,team))
        north = team.replace("North","N")
        south = north.replace("South","S")
        if south in team_set:
            team_set.remove(south)
            tmp.add(team)
            team_pairs.add((south,team))
        tech = team.replace("Tenn","TN")
        fla = tech.replace("Florida Atl","Fla Atlantic")
        if fla in team_set:
            team_set.remove(fla)
            tmp.add(team)
            team_pairs.add((fla,team))
        sm = team.replace("Southern Miss", "S Mississippi")
        mass = sm.replace("Massachusetts", "U Mass")
        um = mass.replace("UMass", "Massachusetts")
        mar = um.replace("UM","Maryland ")
        om = mar.replace("Ole Miss","Mississippi")
        if om in team_set:
            team_set.remove(om)
            tmp.add(team)
            team_pairs.add((om,team))
        a = team.replace("UCF","Central FL")
        b = a.replace("FIU","Florida Intl")
        bc = b.replace("Baptist","Bap")
        c = bc.replace("UIC","IL-Chicago")
        d = c.replace("MD-E Shore","Maryland ES")
        e = d.replace("New Mexico St", "N Mex State")
        f = e.replace("PV A&M", "Prairie View")
        g = f.replace("SMU", "S Methodist")
        gi = g.replace("Northwestern","NW")
        i = gi.replace("VMI", "VA Military")
        ih = i.replace("Southeastern","SE")
        ii = ih.replace("UT Rio Grande Valley","TX-Pan Am")
        h = ii.replace("TCU", "TX Christian")
        if h in team_set:
            team_set.remove(h)
            tmp.add(team)
            team_pairs.add((h,team))
    for team in tmp:
        team_set2.remove(team)
    tmp.clear()
    for tr,espn in team_pairs:
        espn_names[espn] = tr
    team_pairs.clear()
    from fuzzywuzzy import fuzz
    for team1 in sorted(team_set):
        ratio = 0
        team = ""
        for team2 in team_set2:
            if fuzz.ratio(team1,team2) > ratio:
                ratio = fuzz.ratio(team1,team2)
                team = team2
        if ratio > 63:
            tmp.add(team1)
            team_set2.remove(team)
            team_pairs.add((team1,team))
    for team in tmp:
        team_set.remove(team)
    tmp.clear()
    team_set.remove("UC Davis")
    espn_names["UC Davis"] = "UC Davis"
    team_set.remove("Maryland BC")
    espn_names["UMBC"] = "Maryland BC"
    for team1 in sorted(team_set):
        ratio = 0
        team = ""
        for team2 in team_set2:
            if fuzz.ratio(team1,team2) > ratio:
                ratio = fuzz.ratio(team1,team2)
                team = team2
        tmp.add(team1)
        team_set2.remove(team)
        team_pairs.add((team1,team))
    for team in tmp:
        team_set.remove(team)
    tmp.clear()
    for tr,espn in team_pairs:
        espn_names[espn] = tr
    with open('espn_data/names_dict.json', 'w+') as outfile:
        json.dump(espn_names, outfile)

def get_kp_names(name_list):
    trset = set()
    espnset = set()
    matched = set()
    unmatched = set()
    pairs = set()
    kpdf17 = pd.read_json('kp_data/kenpom17.json')
    kpdf14 = pd.read_json('kp_data/kenpom14.json')
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
        ar = pa.replace('Arkansas Little','AR Lit')
        ts = ar.replace('Tennessee St.','Tenn St')
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
    with open('kp_data/names_dict.json', 'w+') as outfile:
        json.dump(kp_names, outfile)

def get_os_names(name_list):
    osdf = pd.read_json('os_data/oddsshark14.json')
    osset = set()
    teamset = set()
    trset = set()
    for team in osdf.home:
        osset.add(team)
    for name in name_list:
        teamset.add(name)
        trset.add(name)
    tmp = set()
    for team in osset:
        if team in teamset:
            tmp.add(team)
            os_names[team] = team
        else:
            try:
                os_names[team] = espn_names[team]
                tmp.add(team)
            except:
                try:
                    os_names[team] = kp_names[team]
                    tmp.add(team)
                except:
                    continue
    for team in tmp:
        osset.remove(team)
    tmp.clear()
    for team in list(espn_names.keys()):
        teamset.add(team)
    for team in list(kp_names.keys()):
        teamset.add(team)
    check_later = set()
    for team in osset:
        u = team.replace(" University","")
        mia = u.replace("Miami","Miami (FL)")
        siu = mia.replace("Southern Illinois-Edwardsville","SIU Edward")
        sfb = siu.replace("St. Francis-Brooklyn","St Fran (NY)")
        sfp = sfb.replace("St. Francis-Pennsylvania", "St Fran (PA)")
        dash = sfp.replace("-"," ")
        st = dash.replace("State","St")
        utrgv = st.replace("UTRGV","TX-Pan Am")
        s = utrgv.replace("Southern","S")
        if s in teamset:
            tmp.add(team)
            check_later.add((team,s))
    for team in tmp:
        osset.remove(team)
    tmp.clear()
    for team in sorted(osset):
        ratio = 0
        t = ""
        for t2 in teamset:
            if fuzz.ratio(team,t2) > ratio:
                ratio = fuzz.ratio(team,t2)
                t = t2
        check_later.add((team,t))
    for team,other in check_later:
        if other in trset:
            os_names[team] = other
        else:
            try:
                os_names[team] = espn_names[other]
            except:
                os_names[team] = kp_names[other]
    with open('os_data/names_dict.json', 'w+') as outfile:
        json.dump(os_names, outfile)

def get_sb_names(name_list):
    sbdf = pd.read_json('sb_data/game_lines.json')
    sbset = set()
    teamset = set()
    trset = set()
    for team in sbdf.home:
        sbset.add(team)
    for team in sbdf.away:
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
            dicts = [sb_names,espn_names,kp_names,os_names]
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
    for team in list(os_names.keys()):
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
        check_later.add((team,t))
    for team,other in check_later:
        if other in trset:
            sb_names[team] = other
        else:
            try:
                sb_names[team] = espn_names[other]
            except:
                try:
                    sb_names[team] = kp_names[other]
                except:
                    sb_names[team] = os_names[other]
    with open('sb_data/names_dict.json', 'w+') as outfile:
        json.dump(sb_names, outfile)
def get_lines_names(name_list):
    ldf = pd.read_json('lines_data/lines2017.json')
    lset = set()
    teamset = set()
    trset = set()
    for team in ldf.home:
        lset.add(team)
    for team in ldf.away:
        lset.add(team)
    for name in name_list:
        teamset.add(name)
        trset.add(name)
    tmp = set()
    for team in lset:
        if team in trset:
            lines_names[team] = team
            tmp.add(team)
        else:
            dicts = [lines_names,sb_names,espn_names,kp_names,os_names]
            for d in dicts:
                try:
                    lines_names[team] = d[team]
                    tmp.add(team)
                    break
                except:
                    pass
    for team in tmp:
        lset.remove(team)
    tmp.clear()
    for team in list(espn_names.keys()):
        teamset.add(team)
    for team in list(kp_names.keys()):
        teamset.add(team)
    for team in list(os_names.keys()):
        teamset.add(team)
    for team in list(sb_names.keys()):
        teamset.add(team)
    check_later = set()
    for team in lset:
        p = team.replace('.','')
        ut = p.replace('Texas','UT')
        chi = ut.replace('IL','CHI')
        d = chi.replace('-',' ')
        u = d.replace(' University','')
        pa = u.replace(' (PA)','')
        s = pa.replace('Virginia','VA')
        if s in teamset:
            check_later.add((team,s))
            tmp.add(team)
    for team in tmp:
        lset.remove(team)
    tmp.clear()
    for team in sorted(lset):
        ratio = 0
        t = ""
        for t2 in teamset:
            if fuzz.ratio(team,t2) > ratio:
                ratio = fuzz.ratio(team,t2)
                t = t2
    for team,other in check_later:
        print(team,other)
        if other in trset:
            lines_names[team] = other
        else:
            try:
                lines_names[team] = espn_names[other]
            except:
                try:
                    lines_names[team] = kp_names[other]
                except:
                    try:
                        lines_names[team] = os_names[other]
                    except:
                        lines_names[team] = sb_names[team]
    with open('lines_data/names_dict.json', 'w+') as outfile:
        json.dump(lines_names, outfile)
trdf = pd.read_csv("tr_data/team_stats14.csv")
with open('espn_data/names_dict.json','r') as infile:
    espn_names = json.load(infile)
with open('kp_data/names_dict.json','r') as infile:
    kp_names = json.load(infile)
with open('os_data/names_dict.json','r') as infile:
    os_names = json.load(infile)
with open('sb_data/names_dict.json','r') as infile:
    sb_names = json.load(infile)
with open('lines_data/names_dict.json','r') as infile:
    lines_names = json.load(infile)
get_sb_names(trdf.Name)
get_lines_names(trdf.Name)
for key in sorted(sb_names.keys()):
    if key != sb_names[key]:
        print(key,sb_names[key])
