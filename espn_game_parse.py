from bs4 import BeautifulSoup
import urllib.request as request
import urllib.error as error
import re
import sys
import time
import random
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
from socket import error as SocketError
import errno

class Game(object):
	def __init__(self, url, game_info):

		self.from_zone = tz.gettz('UTC')
		self.to_zone = tz.gettz('America/Chicago')

		self.game_id = url.split("=")[1]
		self.game_info = game_info


	def make_dataframes(self):
		dateTime = " ".join(self.game_info['tipoff'].split('T'))[:-1]
		utc = datetime.strptime(dateTime, '%Y-%m-%d %H:%M')
		eastern = utc.replace(tzinfo=self.from_zone).astimezone(self.to_zone)
		date, time = str(eastern)[:-6].split(" ")
		self.year = date.split('-')[0]
		self.tipoff = time
		self.date = "{}/{}".format(date.split("-")[1],date.split("-")[2])

		"""
		info = ['Game_ID', 'Away_Abbrv', 'Home_Abbrv', 'Away_Score', 'Attendance',
				'Home_Score', 'Away_Rank', 'Home_Rank', 'Away_Rec', 'Home_Rec', 'Away_1st', 'Away_2nd',
				'Home_1st', 'Home_2nd', 'Game_Year', 'Game_Date','Game_Tipoff', 'Game_Location',
				'Game_Away', 'Game_Home', "Away_OT", "Home_OT"]
		"""
		info = ['Game_ID', 'Away_Abbrv', 'Home_Abbrv', 'Away_Score', 'Home_Score',
				'Game_Away', 'Game_Home','Game_Year', 'Game_Date','Game_Tipoff',
				'Game_Location', 'Neutral_Site', 'Conference_Competition', 'Attendance']

		data = np.array([np.arange(len(info))])
		self.info_df = pd.DataFrame(data, columns=info)

		self.info_df['Game_ID'] = self.game_id
		self.info_df['Away_Abbrv'] = self.game_info['Away_Abbrv']
		self.info_df['Home_Abbrv'] = self.game_info['Home_Abbrv']
		self.info_df['Away_Score'] = self.game_info['Away_Score']
		self.info_df['Home_Score'] = self.game_info['Home_Score']
		self.info_df['Game_Away'] = self.game_info['Game_Away']
		self.info_df['Game_Home'] = self.game_info['Game_Home']
		self.info_df['Game_Year'] = self.year
		self.info_df['Game_Date'] = self.date
		self.info_df['Game_Tipoff'] = self.tipoff
		self.info_df['Game_Location'] = self.game_info['venue']
		self.info_df['Neutral_Site'] = self.game_info['neutral_site']
		self.info_df['Conference_Competition'] = self.game_info['conferenceCompetition']
		self.info_df['Attendance'] = self.game_info['attendance']
		#self.info_df['Away_Rank'] = self.away_rank
		#self.info_df['Home_Rank'] = self.home_rank
		#self.info_df['Away_Rec'] = self.away_rec
		#self.info_df['Home_Rec'] = self.home_rec
		#self.info_df['Away_1st'] = self.away_1st
		#self.info_df['Away_2nd'] = self.away_2nd
		#self.info_df['Away_OT'] = self.away_ot
		#self.info_df['Home_1st'] = self.home_1st
		#self.info_df['Home_2nd'] = self.home_2nd
		#self.info_df['Home_OT'] = self.home_ot
		#self.info_df['Officials'] = self.officials
		#self.info_df = pd.concat([self.info_df, self.tourney_df], axis=1)
