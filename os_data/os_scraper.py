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
                    2: 'o',
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
        j += 1
    if VERBOSE:
        p = pp(indent=4)
        p.pprint(data)
    year_str2 = str(year%100)
    with open('oddsshark' + year_str2 + '.json', 'w+') as outfile:
        json.dump(data, outfile)

links = []
names = []
for link,name in get_links():
    links.append(link)
    names.append(name)

get_oddsshark(2017,links,names)
