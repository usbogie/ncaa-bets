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
    print(VERBOSE)
except:
    pass

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
                        print('found {} for current team: {}'.format(element_name, new_team[element_name]))
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
                        print('regex {} didnt match {}'.format(regexes[ri].pattern, str(table_element)))
        teams.append(new_team)
        if VERBOSE:
            print('adding team: {}'.format(new_team))

    p = pp(indent=4)
    if VERBOSE:
        p.pprint(teams)
    year_str2 = str(year%100)
    with open('kenpom' + year_str2 + '.json', 'w+') as outfile:
        json.dump(teams, outfile)

extract_kenpom(2017)
