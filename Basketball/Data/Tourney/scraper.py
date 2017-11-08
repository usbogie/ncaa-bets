import urllib.request as request
import urllib.error as error
from bs4 import BeautifulSoup, Comment, Tag, NavigableString
from fake_useragent import UserAgent
import pandas as pd
import numpy as np
import sys
import json
from pprint import pprint


ua = UserAgent()

try:
	with open('names_dict.json','r') as infile:
		names_dict = json.load(infile)
except:
	with open('Data/Tourney/names_dict.json','r') as infile:
		names_dict = json.load(infile)

def get_soup(url):
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
			return None
	content = page.read()
	return BeautifulSoup(content, "html5lib")

def get_games(year=2016):
	soup = get_soup("http://www.sports-reference.com/cbb/postseason/{}-ncaa.html".format(year))
	locations = [x.text.lower() for x in soup.find('div', {'class': 'switcher filter'}).contents[1::2]][:4]+['national']
	games = []
	for location in locations:
		region = soup.find('div', {'id': location})
		for tourney_round in region.findAll('div', {'class':'round'}):
			for game in tourney_round.contents[::2]:
				try:
					top_soup = game.contents[3]
					bottom_soup = game.contents[5]
				except:
					print(tourney_round)
					# declaring winner of bracket, not a game. Ok to skip
					continue
				game = {}
				top_score = int(top_soup.contents[7].text)
				bottom_score = int(bottom_soup.contents[7].text)
				winner_soup = top_soup if top_score > bottom_score else bottom_soup
				loser_soup = bottom_soup if top_score > bottom_score else top_soup
				game['winner'] = names_dict[winner_soup.contents[5].text]
				game['winner_seed'] = winner_soup.contents[3].text
				game['winner_score'] = winner_soup.contents[7].text
				game['loser'] = names_dict[loser_soup.contents[5].text]
				game['loser_seed'] = loser_soup.contents[3].text
				game['loser_score'] = loser_soup.contents[7].text
				game['region'] = location
				games.append(game)
	print(json.dumps(games, indent=2, sort_keys=False))
	return games



if __name__ == '__main__':
	cur_year = 2016
	tourney = get_games(year=cur_year)
	#tourney.to_csv('tourney_info{}.csv'.format(cur_year), index=False)
	print("Updated cbbref")
