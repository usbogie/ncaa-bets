from bs4 import BeautifulSoup
import urllib.request as request
import urllib.error as error
import re
import sys
import time
import random
import itertools
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz

def get_page(url, ua):
    try:
        page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
        return page
    except error.HTTPError as e:
        try:
            print("First attempt for %s failed. %s" % (url, e.code))
            wait_time = round(max(10, 15 + random.gauss(0,2.5)), 2)
            time.sleep(wait_time)
            page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
            return page
        except error.HTTPError as e:
            try:
                print("Second attempt for %s failed. Big sleep. Error: %s" % (url, e.code))
                wait_time = round(max(60, 66 + random.gauss(0,2.5)), 2)
                time.sleep(wait_time)
                page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
                return page
            except error.HTTPError as e:
                if hasattr(e, 'reason'):
                    print('Failed to reach url')
                    print('Reason: ', e.reason)
                    sys.exit()
                elif hasattr(e, 'code'):
                    if e.code == 404:
                        print('Error: ', e.code)
                        sys.exit()

class Game(object):
    def __init__(self, url, ua, tourney_df, ncaa_bool):

        self.from_zone = tz.gettz('UTC')
        self.to_zone = tz.gettz('America/New_York')

        game_summary_url = url.replace('boxscore','game')

        page = get_page(url, ua)
        page2 = get_page(game_summary_url, ua)

        content = page.read()
        content_summary = page2.read()

        self.soup = BeautifulSoup(content, "html5lib")
        self.soup2 = BeautifulSoup(content_summary, "html5lib")
        self.game_id = url.split("=")[1]
        self.tourney_df = tourney_df
        self.ncaa_bool = ncaa_bool

        if 'OT' in self.soup.find("span", {"class": "game-time"}).text:
            self.ot = True
        else:
            self.ot = False


    def get_raw(self):
        scripts = self.soup.find_all("script", {"type": "text/javascript"})
        dateTime = None
        for script in scripts:
            if 'espn.gamepackage.timestamp' in script.text:
                dateTime = script.text.split('espn.gamepackage.timestamp')[1].split("espn.gamepackage.status")[0].split("\"")[1]

        dateTime = " ".join(dateTime.split('T'))[:-1]
        utc = datetime.strptime(dateTime, '%Y-%m-%d %H:%M')
        eastern = utc.replace(tzinfo=self.from_zone).astimezone(self.to_zone)
        date, time = str(eastern)[:-6].split(" ")
        self.year = date.split('-')[0]
        self.tipoff = time
        self.date = date.split("-")[1]+'/'+date.split("-")[2]

        away = self.soup.find("div", {"class": "team away"})
        self.away_tm = away.find("span", {"class": "long-name"}).text
        try:
            self.away_score = away.find("div", {"class": "score-container"}).text
            self.away_rank = np.nan
        except ValueError:
            rank_score = [i.text for i in away.find_all("span")]
            rank = re.compile("\d+").findall(rank_score[0])
            if self.ncaa_bool == True:
                self.tourney_df['Away_Seed'] = int(rank[0])
                self.away_rank = np.nan
            else:
                self.away_rank = int(rank[0])
            self.away_score = int(rank_score[1])

        home = self.soup.find("div", {"class": "team home"})
        self.home_tm = home.find("span", {"class": "long-name"}).text
        try:
            self.home_score = home.find("div", {"class": "score-container"}).text
            self.home_rank = np.nan
        except ValueError:
            rank_score = [i.text for i in home.find_all("span")]
            rank = re.compile("\d+").findall(rank_score[0])
            if self.ncaa_bool == True:
                self.tourney_df['Home_Seed'] = int(rank[0])
                self.home_rank = np.nan
            else:
                self.home_rank = int(rank[0])
            self.home_score = int(rank_score[1])

        linescore = self.soup.find("table", {"id": "linescore"})
        cells = [td.text for td in linescore.find_all("td")]
        n_col = int(len(cells)/2)
        shape = (2, n_col)
        cells = np.array(cells)
        cells = cells.reshape(shape)
        cells = np.delete(cells, -1, 1)

        self.away_abbrv = cells[0,0]
        self.home_abbrv = cells[1,0]
        """
        try:
            self.away_1st = int(cells[0,1])
            self.away_2nd = int(cells[0,2])

            self.home_1st = int(cells[1,1])
            self.home_2nd = int(cells[1,2])
        except ValueError:
            # some games have no values in 2nd half score columns
            self.away_1st = np.nan
            self.away_2nd = np.nan

            self.home_1st = np.nan
            self.home_2nd = np.nan

        try:
            ot = np.array(cells[:, 3:], dtype=int)
            self.ot = True
        except:
            self.ot = False

        if self.ot == False:
            self.away_ot = np.nan
            self.home_ot = np.nan
        else:
            self.away_ot = sum(ot[0,:])
            self.home_ot = sum(ot[1,:])

        #######################################
        # Grabbing player specific data
        plyr_tables = self.soup.find_all("table", {"class":"mod-data"})[:2]

        away_rows = plyr_tables[0].find_all("tr")
        home_rows = plyr_tables[1].find_all("tr")

        # Getting raw data cells by row for away team
        away_stats = [i.find_all("td") for i in away_rows if not i.find("th")]
        # filters out the non-players rows, then cleaning them to just the text
        away_stats = [x for x in away_stats if re.match("^[A-Za-z]", x[0].text)]
        self.away_stats = [[x.text for x in r] for r in away_stats]

        # Same thing but for home team now
        home_stats = [i.find_all("td") for i in home_rows if not i.find("th")]
        # filters out the non-players rows, then cleaning them to just the text
        home_stats = [x for x in home_stats if re.match("^[A-Za-z]", x[0].text)]
        self.home_stats = [[x.text for x in r] for r in home_stats]
        """
        game_details = self.soup2.find("div", {"class":"location-details"})
        self.location = game_details.find("li").text.split()
        self.location = " ".join(self.location[:2])

    def make_dataframes(self):
        # call the first function that parses the data
        self.get_raw()
        """
        if self.away_stats != 'N/A' and self.home_stats != 'N/A':
            headers = ["Player", "Min", "FGM-A", "3PM-A", "FTM-A", "OREB", "DREB", "REB", "AST", "STL",
                       "BLK", "TO", "PF", "PTS"]

            numeric_col = ['FGM', 'FGA', '3PM', '3PA', 'FTM', 'FTA', 'OREB', 'DREB', 'REB',
                'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS']


            try:
                self.away_df = pd.DataFrame(self.away_stats, columns=headers)
                players = []
                positions = []
                for index, row in self.away_df.iterrows():
                    split_point = int(len(row['Player'])/2)
                    positions.append(row['Player'][-1])
                    players.append(row['Player'][:split_point])
                self.away_df['Player'] = players
                self.away_df['Position'] = positions

                self.away_df['FGM'], self.away_df['FGA'] = zip(*self.away_df['FGM-A'].apply(lambda x: x.split('-', 1)))
                self.away_df['3PM'], self.away_df['3PA'] = zip(*self.away_df['3PM-A'].apply(lambda x: x.split('-', 1)))
                self.away_df['FTM'], self.away_df['FTA'] = zip(*self.away_df['FTM-A'].apply(lambda x: x.split('-', 1)))
                self.away_df[numeric_col] = self.away_df[numeric_col].astype(np.int64)
                self.away_df = self.away_df.drop(['FGM-A', '3PM-A', 'FTM-A'], axis=1)
                self.away_df['Game_ID'] = self.game_id
                self.away_df['Home_Away'] = 'Away'
                self.away_df['Team'] = self.away_abbrv
                self.away_df = self.away_df[:-1]

            except:
                # No minutes column in random games, and false positive on only having 13 columns,
                # so need to delete Defensive Rebounds
                headers.remove('Min')
                for row in self.away_stats:
                    del row[5]
                for row in self.home_stats:
                    del row[5]

                self.away_df = pd.DataFrame(self.away_stats, columns=headers)
                # Probably a more pythonic way of doing all this, but splitting all columns and setting as ints
                try:
                    self.away_df['Player'], self.away_df['Position'] = zip(*self.away_df['Player'].apply(lambda x: x.split(', ', 1)))
                except:
                    for i in self.away_df['Player']:
                        if ',' not in i:
                            try:
                                idx = np.where(self.away_df['Player'] == i)[0].item()
                                self.away_df['Player'][idx] += ', N/A'
                            except:
                                # Problematic when person with same names on same team,
                                # exception handling for them appearing twice
                                idx1 = np.where(self.away_df['Player'] == i)[0][0].item()
                                if ',' not in self.away_df['Player'][idx1]:
                                    self.away_df['Player'][idx1] += ', N/A'

                    self.away_df['Player'], self.away_df['Position'] = zip(*self.away_df['Player'].apply(lambda x: x.split(', ', 1)))

                self.away_df['FGM'], self.away_df['FGA'] = zip(*self.away_df['FGM-A'].apply(lambda x: x.split('-',1)))
                self.away_df['3PM'], self.away_df['3PA'] = zip(*self.away_df['3PM-A'].apply(lambda x: x.split('-',1)))
                self.away_df['FTM'], self.away_df['FTA'] = zip(*self.away_df['FTM-A'].apply(lambda x: x.split('-',1)))
                self.away_df[numeric_col] = self.away_df[numeric_col].astype(np.int64)
                self.away_df = self.away_df.drop(['FGM-A', '3PM-A', 'FTM-A'], axis=1)
                self.away_df['Game_ID'] = self.game_id
                self.away_df['Home_Away'] = 'Away'
                self.away_df['Team'] = self.away_abbrv
                self.away_df = self.away_df[:-1]
            # Again, for the home team
            self.home_df = pd.DataFrame(self.home_stats, columns=headers)
            try:
                players = []
                positions = []
                for index, row in self.home_df.iterrows():
                    split_point = len(row['Player'])/2
                    positions.append(row['Player'][-1])
                    players.append(row['Player'][:split_point])

                self.home_df['Player'] = players
                self.home_df['Position'] = positions

                #self.home_df['Player'], self.home_df['Position'] = zip(*self.home_df['Player'].apply(lambda x: x.split(', ', 1)))
            except:
                names = [i for i in self.home_df['Player']]
                for i in names:
                    if ',' not in i:
                        try:
                            idx = np.where(self.home_df['Player'] == i)[0].item()
                            self.home_df['Player'][idx] += ', N/A'
                        except:
                            idx1 = np.where(self.home_df['Player'] == i)[0][0].item()
                            if ',' not in self.home_df['Player'][idx]:
                                self.home_df['Player'][idx1] += ', N/A'
                            else:
                                idx2 = np.where(self.home_df['Player'] == i)[0][1].item()
                                self.home_df['Player'][idx2] += ', N/A'

                self.home_df['Player'], self.home_df['Position'] = zip(*self.home_df['Player'].apply(lambda x: x.split(', ', 1)))

            self.home_df['FGM'], self.home_df['FGA'] = zip(*self.home_df['FGM-A'].apply(lambda x: x.split('-', 1)))
            self.home_df['3PM'], self.home_df['3PA'] = zip(*self.home_df['3PM-A'].apply(lambda x: x.split('-', 1)))
            self.home_df['FTM'], self.home_df['FTA'] = zip(*self.home_df['FTM-A'].apply(lambda x: x.split('-', 1)))
            self.home_df[numeric_col] = self.home_df[numeric_col].astype(np.int64)
            self.home_df = self.home_df.drop(['FGM-A', '3PM-A', 'FTM-A'], axis=1)
            self.home_df['Game_ID'] = self.game_id
            self.home_df['Home_Away'] = 'Home'
            self.home_df['Team'] = self.home_abbrv
            self.home_df = self.home_df[:-1]

            self.players = pd.concat([self.away_df, self.home_df], ignore_index=False)

            # Making team totals dataframes
            data = np.array([np.arange(len(numeric_col))]) # empty row for filling in aggregated data
            self.a_totals = pd.DataFrame(data, columns=numeric_col)
            awayadded = self.away_df.sum(axis=0, numeric_only=True)
            for column in numeric_col:
                self.a_totals[column] = awayadded[column]
            self.a_totals['Team'] = self.away_tm
            self.a_totals['Home_Away'] = 'Away'
            self.a_totals['Game_ID'] = self.game_id

            data = np.array([np.arange(len(numeric_col))])
            self.h_totals = pd.DataFrame(data, columns=numeric_col)
            homeadded = self.home_df.sum(axis=0, numeric_only=True)
            for column in numeric_col:
                self.h_totals[column] = homeadded[column]
            self.h_totals['Team'] = self.home_tm
            self.h_totals['Home_Away'] = 'Home'
            self.h_totals['Game_ID'] = self.game_id

            self.gm_totals = pd.concat([self.a_totals, self.h_totals], ignore_index=False)
        """
        #######################################

        """
        info = ['Game_ID', 'Away_Abbrv', 'Home_Abbrv', 'Away_Score', 'Attendance',
                'Home_Score', 'Away_Rank', 'Home_Rank', 'Away_Rec', 'Home_Rec', 'Away_1st', 'Away_2nd',
                'Home_1st', 'Home_2nd', 'Game_Year', 'Game_Date','Game_Tipoff', 'Game_Location',
                'Game_Away', 'Game_Home', "Away_OT", "Home_OT"]
        """
        info = ['Game_ID', 'Away_Abbrv', 'Home_Abbrv', 'Away_Score', 'Home_Score', 'Game_Away', 'Game_Home',
                'Game_Year', 'Game_Date','Game_Tipoff', 'Game_Location']

        data = np.array([np.arange(len(info))])
        self.info_df = pd.DataFrame(data, columns=info)

        self.info_df['Game_ID'] = self.game_id
        self.info_df['Away_Abbrv'] = self.away_abbrv
        self.info_df['Home_Abbrv'] = self.home_abbrv
        self.info_df['Away_Score'] = self.away_score
        self.info_df['Home_Score'] = self.home_score
        self.info_df['Game_Away'] = self.away_tm
        self.info_df['Game_Home'] = self.home_tm
        self.info_df['Game_Year'] = self.year
        self.info_df['Game_Date'] = self.date
        self.info_df['Game_Tipoff'] = self.tipoff
        self.info_df['Game_Location'] = self.location
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
        #self.info_df['Attendance'] = self.attendance
        self.info_df = pd.concat([self.info_df, self.tourney_df], axis=1)
