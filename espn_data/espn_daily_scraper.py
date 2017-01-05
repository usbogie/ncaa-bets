from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from espn_game_parse import Game
import urllib.request as request
import urllib.error as error
import pandas as pd
import numpy as np
import json
import random
import time

ua = UserAgent()

def get_data(game_url, ua, tourney_df, ncaa):
    game = Game(game_url, ua, tourney_df, ncaa)
    game.make_dataframes()

    gen_info = game.info_df
    """
    try:
        #players = game.players
        game_stats = game.gm_totals

    except:
        #players = None
        game_stats = None
    """
    print("Just finished: %s vs %s on %s" % (game.away_abbrv, game.home_abbrv, game.date))

    wait_time = round(max(10, 15 + random.gauss(0,3)), 2)
    time.sleep(wait_time)

    return gen_info

def update_espn_scores():
	base = "http://www.espn.com/mens-college-basketball/scoreboard/_/date/"
	date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d').replace('-','')
	url = base + date + '&confId=50'
	
	try:
		page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
	except error.HTTPError as e:
		try:
			wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
			time.sleep(wait_time)
			print("First attempt for %s failed. Trying again." % (d))
			page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
		except:
			print(e)
			sys.exit()

	content = page.read()
	soup = BeautifulSoup(content, "html5lib")

	gen_info = []

	links = []
	status_dict = {}
	for link in soup.find_all('script'):
		if 'window.espn.scoreboardData' in str(link.text):
			jsonValue1 = '{%s}' % (link.text.split('{', 1)[1].rsplit('}', 1)[0],)
			jsonValue = jsonValue1.split(';window')[0]
			value = json.loads(jsonValue)
			events = value['events']
			for event in events:
				links.append(event['links'][1]['href'])
				status_dict[event['id']] = event['status']['type']['shortDetail']

				if date[4:6] == '03' or date[4:6] == '04':
					game_notes = event['notes']['headline']
	
	for url in links:
		game_id = url.split("=")[-1]
		if status_dict[game_id] == 'Postponed' or status_dict[game_id] == 'Canceled':
			continue
		else:
			tourney_col = ['Tournament', 'Round', 'Away_Seed', 'Home_Seed']
			ncaa = False
			data = np.array([np.repeat(np.nan,4)])
			tourney_df = pd.DataFrame(data, columns=tourney_col)
			pos = links.index(url)
			try:
				note = game_notes[pos].text
				tourney_split = note.split(' - ')
				if tourney_split[0]:
					tourney_df['Tournament'] = tourney_split[0]
					round_split = tourney_split[-1].split(' AT ')
					if tourney_split[0] == "MEN'S BASKETBALL CHAMPIONSHIP":
						ncaa = True
					if round_split[0]:
						tourney_df['Round'] = round_split[0]
			except:
				pass

			gm_info = get_data(url, ua, tourney_df, ncaa)
			gen_info.append(gm_info)

	chance = range(100)
	choice = random.choice(chance)
	if choice < 10:
		big_wait_time = round(max(25, 28 + random.gauss(0,2)), 2)
		print("Big wait of %d seconds\n\n" % big_wait_time)
		time.sleep(big_wait_time)

update_espn_scores()