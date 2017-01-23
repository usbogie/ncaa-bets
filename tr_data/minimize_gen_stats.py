import pandas as pd

for start_year in [12,13,14,15,16,17]:
	teams = pd.read_csv('xteam_stats{}.csv'.format(start_year))

	new = teams.sort_values(by=['Name','date']).drop_duplicates(subset=['Name','FTO','FTOlast3','FTOprevSeason',
																		'FTD','FTDlast3','FTDprevSeason','Three_O',
																		'Three_Olast3','Three_OprevSeason','Three_D',
																		'Three_Dlast3','Three_DprevSeason','REBO',
																		'REBOlast3','REBOprevSeason','REBD','REBDlast3',
																		'REBDprevSeason','REB','REBlast3','REBprevSeason',
																		'TOP','TOPlast3','TOPprevSeason','TOFP','TOFPlast3',
																		'TOFPprevSeason','POSS','POSSlast3','POSSprevSeason'], keep='last')

	new.to_csv('xteam_stats{}.csv'.format(start_year))