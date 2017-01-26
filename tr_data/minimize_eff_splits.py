import pandas as pd
import json

for start_year in [2012, 2013, 2014, 2015, 2016, 2017]:
	teams = pd.read_csv('xeff_splits{}.csv'.format(start_year))

	with open('../vi_data/vegas_{}.json'.format(start_year),'r') as infile:
		games = json.load(infile)

	rows_to_keep = []

	for game in games:
		away_row = teams.ix[(teams['Name']==game['away']) & (teams['date'] == game['date'])]
		home_row = teams.ix[(teams['Name']==game['home']) & (teams['date'] == game['date'])]
		rows_to_keep.append(away_row)
		rows_to_keep.append(home_row)

	new = pd.concat(rows_to_keep, ignore_index=True)
	new.to_csv('xeff_splits{}.csv'.format(start_year), index=False)

	print("Finished {}".format(start_year))