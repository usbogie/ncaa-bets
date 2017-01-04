from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup as bs
from pprint import PrettyPrinter as pp
import re
from subprocess import call
import sys
import json

VERBOSE = False
try:
    if sys.argv[1] == '-v':
        VERBOSE = True
    print VERBOSE
except:
    pass

"""
Objective:
    Report the favorable spreads and over/unders

Variables:
    Regression:
        Adjusted Offense KP
        Adjusted Defense KP
        Tipoff?
        Total?

    Matchup:
        FTO: points as a percentage of points scored
        FTD: FTA per possession
            Good FTO, Bad FTD
            Good FTO, Good FTD
        3O: points as a percentage of points scored
        3D: FG%
            Good 3O, Bad 3D
            Good 3O, Good 3D
        Rebound Differential
            Good Rebound, Good Rebound
            Good Rebound, Bad Rebound
            Bad Rebound, Bad Rebound
        Turnovers per possession
        Turnovers forced per possession
            Protect Ball, Force turnovers
            Sloppy, Force turnovers
        KP Tempo
            High Temp, Low Temp
            High Temp, High Temp
            Low Temp, Low Temp

    Scrape:
        Team: {
            kenpom.com:
                School
                Year
                KP Adjusted O
                KP Adjusted D
                KP Adjusted T
            ncaa.com:
                PPG
                FTM
                Fouls
                3FG per game
                Opponent 3FG%
                Rebound Differential
                Turnovers per game
                Turnovers forced per game
        }

        Old Game: {
            OddShark.com:
                Spread
                Total
            ESPN:
                Tipoff
                Home Team
                Away Team
                Home Score
                Away Score
                True Home Game?
        }

        New Game: {
            Sportsbook.ag:
                Spread
                Total
            ESPN:
                Tipoff
                Home Team
                Away Team
                True Home Game
        }

Strategy:
    Categorize games (Home lock, Home slight edge, Home slight dog, Home long shot, Neutral Big, Neutral normal)
    Categorize matchups
    Get database of games with same matchup types, games
    Regress data with offense defense differences, tipoff, total
    Predict difference in spread
    Use probablity test to determine how likely a cover is
    Use this data on historical games and check performance
"""

"""
Get Database

Dictionaries
    teams: {
        name
        year
        kp_t
        ppg
        ftm
        fouls
        3fg
        opp_3fg
        reb
        to
        opp_to

        fto (FTM / PPG)
        ftd (Fouls / KP Tempo)
        3o (3FGM * 3 / PPG)
        to_poss (TO per game / KP Tempo)
        tof_poss (TO forced per game/ KP Tempo)

        kp_o
        kp_d
        good_fto (FTM / PPG)
        good_ftd (Fouls / KP Tempo)
        bad_ftd
        good_3o (3FGM * 3 / PPG)
        good_3d (3%)
        bad_3d
        good_reb (Rebound margin)
        bad_reb
        low_to (TO per game / KP Tempo)
        high_to
        agressive (TO forced per game/ KP Tempo)
        high_temp
        low_temp
    }

    old_games: {
        spread
        total
        tipoff (-1 early, 0 not)
        home
        h_adv (adj o - opp adj d)
        away
        a_adv
        true
        h_score
        a_score
        spread_difference
        winner
        pick
        confidence_level
        match_type
        h_attributes*
        a_attributes*
    }

    game_slate: {
        spread
        total
        tipoff (-1 early, 0 not)
        home
        h_adv
        away
        a_adv
        true
        confidence_level
        pick
        match_type
        h_attributes*
        a_attributes*
    }

    *Attribute arrays format:
        index 0:
            No advantage = 0
            Good FTO, Bad FTD = 1
            Good FTO, Good FTD = 2
        index 1:
            No advantage = 0
            Good 3O, Bad 3D = 1
            Good 3O, Good 3D = 2
        index 2:
            No advantage = 0
            Good Rebound, Good Rebound = 1
            Good Rebound, Bad Rebound = 2
            Bad Rebound, Bad Rebound = 3
        index 3:
            No advantage = 0
            Protect Ball, Force turnovers = 1
            Sloppy, Force turnovers = 2
        index 4:
            No advantage = 0
            High Temp, Low Temp = 1
            High Temp, High Temp = 2
            Low Temp, Low Temp = 3
"""

def extract_kenpom(year):
    import re
    regexes = [re.compile('<td>([0-9\-\+\.]*)</td>'),
               re.compile('<td class="td-[\w \-]*">([0-9\.]*)</td>'),
               re.compile('<td class="td-[\w \-]*"><span class="seed">([0-9]*)</span></td>'),
               re.compile('<td [a-z]*="[\w \-:;]*"><a href="[\w \.\?\=&\+%0-9]*">([\w \.&;\']*)</a>')
               ]


    index_lookup = {0: 'rank',
                    1: ('name', 3),
                    2: 'conf',
                    3: 'record',
                    4: ('adjEM', 0),
                    5: ('adjO', 1),
                    6: 'adjO_seed',
                    7: ('adjD', 1),
                    8: 'adjD_seed',
                    9: ('adjT', 1),
                    10: 'adjT_seed',
                    11: 'luck',
                    12: 'luck_seed',
                    13: 'sos_adjEM',
                    14: 'sos_adjEM_seed',
                    15: 'sos_oppO',
                    16: 'sos_oppO_seed',
                    17: 'sos_oppD',
                    18: 'sos_oppD_seed',
                    19: 'ncsos_adjEM',
                    20: 'ncsos_adjEM_seed'}

    targets = set(['name', 'adjO', 'adjD', 'adjT'])
    year_str = '?y=' + str(year)
    if year == 2017:
        year_str = ''
    s = bs(urlopen('http://kenpom.com/index.php' + year_str))
    team_entries = [tr.findAll('td') for tr in s.findAll('tr')][2:]
    teams = []
    for team in team_entries:
        if not team:
            continue
        if VERBOSE:
            call('clear')
        new_team = {}
        for i,table_element in enumerate(team):
            if not isinstance(index_lookup[i], tuple):
                continue
            element_name, ri = index_lookup[i]
            if element_name in targets:
                try:
                    new_team[element_name] = regexes[ri].match(str(table_element)).groups()[0].replace(';', '')
                    if VERBOSE:
                        print 'found {} for current team: {}'.format(element_name, new_team[element_name])
                except:
                    try:
                        tbl_str = str(table_element)
                        match1 = "y=" + str(year) + "\">"
                        match2 = "</a>"
                        for i in range(len(tbl_str)):
                            if tbl_str[i:i+8] == match1:
                                for j in range(len(tbl_str)-i):
                                    if tbl_str[i+j+8:i+j+12] == match2:
                                        new_team[element_name] = tbl_str[i+8:i+8+j].replace(';','')
                                        break
                                break
                    except:
                        print 'regex {} didnt match {}'.format(regexes[ri].pattern, str(table_element))
        teams.append(new_team)
        if VERBOSE:
            print 'adding team: {}'.format(new_team)

    p = pp(indent=4)
    if VERBOSE:
        p.pprint(teams)
    year_str2 = str(year%100)
    with open('kenpom' + year_str2 + '.json', 'w+') as outfile:
        json.dump(teams, outfile)

def get_links():
    s = str(bs(urlopen('http://www.oddsshark.com/stats/gamelogs/basketball/ncaab')))
    match = "/stats/gamelog/basketball/ncaab/"
    name_match = "</a>"
    links = []
    for i in range(len(s)-32):
        if s[i:i+32] == match:
            link = s[i+32:i+37]
            for j in range(50):
                if s[i+j+58:i+j+62] == name_match:
                    name = s[i+58:i+j+58].replace('amp;','')
                    links.append((link,name.replace('&#039;','\'')))
    return links

def game_occurred_yet(block):
    r = re.compile('<td>([\w 0-9,]*)</td>')
    import datetime
    ex = r.match(str(block[0])).groups()[0].lower().replace(',', '')
    ex = ex[0].upper() + ex[1:]
    date = datetime.datetime.strptime(ex, '%b %d %Y')
    return not date > datetime.datetime.now()


def extract_name(block):
    r = re.compile('<td> <span> ([vs@])* </span> ([\w .\'&-;]*)</td>')
    home_away = r.match(str(block[1])).groups()[0]
    opponent = r.match(str(block[1])).groups()[1].strip()
    if home_away == '@':
        return None
    return opponent
    """
    matchup = None
    try:
        matchup = str(block[-2]).split('\"')[1].split('/')[-1].split('-')
    except:
        print 'couldnt get a regex match'
    extract = matchup[:matchup.index('betting')]
    if '@' in home_away:
        print 'a'
        if VERBOSE:
            print 'Getting odds for {}...'.format('-'.join(extract[:extract.index(opponent[0])]))
        return '-'.join(extract[:extract.index(opponent[0])])
    else:
        team_first_name = extract[extract.index(opponent[0]) + len(opponent)]
        last_name = int(team_first_name[-1] != 's')
        if VERBOSE:
            print 'Getting odds for {}...'.format('-'.join(extract[:extract.index(opponent[0])]))
        return '-'.join(extract[extract.index(team_first_name) + last_name + 1:])
    """

def get_oddsshark(year,links,names):
    data = None
    url = 'http://www.oddsshark.com/stats/gamelog/basketball/ncaab'
    rgx = re.compile('<td>([a-zA-Z\.\+0-9 ]+)</td>')
    index_lookup = {0: 'ats',
                    1: 'spread',
                    2: 'o/u',
                    3: 'total'}
    data = []
    if year == 2017:
        year_str = ''
    else:
        year_str = "/" + str(year)
    j = 0
    for i in links: #TODO figure out how to get all matchup links, and also key entries by AWAY @ HOME
        if VERBOSE:
            print 'finding team {}'.format(i)
        s = bs(urlopen('{}/{}{}'.format(url,i,year_str)))
        entries = [tr.findAll('td') for tr in s.findAll('tr')]
        if not entries:
            if VERBOSE:
                print 'skipping odds table, no entries...'
            continue
        if not str(entries[0]):
            if VERBOSE:
                print 'skipping odds table, no entries...'
            continue
        for entry in entries:
            if not entry or not game_occurred_yet(entry):
                continue
            game_info = {'home': names[j],
                         'away': extract_name(entry)}
            if not game_info['away']:
                continue
            game_info['date'] = str(entry[0])[4:-5]
            for i,box in enumerate(entry[5:9]):
                if str(box)[4:-5] == "":
                    game_info[index_lookup[i]] = None
                else:
                    game_info[index_lookup[i]] = str(box)[4:-5].strip()
                if i == 3:
                    data.append(game_info)
        print(names[j])
        j += 1
    if VERBOSE:
        p = pp(indent=4)
        p.pprint(data)
    year_str2 = str(year%100)
    with open('oddsshark' + year_str2 + '.json', 'w+') as outfile:
        json.dump(data, outfile)

extract_kenpom(2017)

links = []
names = []
for link,name in get_links():
    links.append(link)
    names.append(name)

get_oddsshark(2017,links,names)
