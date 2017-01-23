import pandas as pd

for start_year in [2012,2013,2014,2015,2016,2017]:
	teams = pd.read_csv('xeff_splits{}.csv'.format(start_year))

	new = teams.sort_values(by=['Name','date']).drop_duplicates(subset=['ORTG','ORTGlast3','home_ORTG','away_ORTG','ORTGprevSeason',
											   'DRTG','DRTGlast3','home_DRTG','away_DRTG','DRTGprevSeason'], keep='last')

	new.to_csv('xeff_splits{}.csv'.format(start_year))