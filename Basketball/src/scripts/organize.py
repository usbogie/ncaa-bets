from organizers import add_features, organize_data, new_games, rankings
import helpers as h

def run():
	year_list = [h.this_season]
	#year_list = range(2011,h.this_season + 1)
	organize_data.get_old_games(year_list)
	organize_data.get_spreads(year_list)
	organize_data.get_sports_ref_data(year_list)
	h.save()
	add_features.betsy()
	new_games.get()
	rankings.get()