from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup
from itertools import izip
import re
import json

def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return izip(*[iter(iterable)]*n)

def get_todays_sportsbook_lines():
    url = "https://www.sportsbook.ag/sbk/sportsbook4/ncaa-basketball-betting/game-lines.sbk"
    soup = BeautifulSoup(urlopen(url))
    teams = [team.text for team in soup.findAll('span', {'class': 'team-title'})]
    money_lines = [item.a.div.text for item in soup.findAll('div', {'class': 'column money pull-right'})]
    spreads = [item.a.div.text for item in soup.findAll('div', {'class': 'column spread pull-right'})]
    totals = [item.a.div.text for item in soup.findAll('div', {'class': 'column total pull-right'})]
    date = re.sub('\s+',' ', soup.find('div', {'class': 'col-xs-12 date'}).text)

    games = []
    for i, j in grouped(range(len(teams)), 2):
        game = {}
        game['away'] = teams[i]
        game['home'] = teams[j]
        game['money_line_away'] = totals[i]
        game['money_line_home'] = totals[j]
        game['spread_away'] = spreads[i]
        game['spread_home'] = spreads[j]
        game['total_over'] = money_lines[i]
        game['total_under'] = money_lines[j]
        game['date'] = date
        games.append(game)
    with open('game_lines.json','w') as outfile:
        json.dump(games,outfile)
get_todays_sportsbook_lines()
