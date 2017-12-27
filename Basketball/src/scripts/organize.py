from organizers.organize_data import Organizer
import helpers as h

def run():
	year_list = [h.this_season]
	year_list = range(2011,h.this_season + 1)
	org = Organizer(year_list)
	org.run()
