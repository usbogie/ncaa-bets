from organizers import Betsy2 as b
from organizers import join_scraped_data as jsd
from organizers import new_games as ng
from organizers import rankings as r
import helpers as h

year_list = [h.this_season]
#year_list = range(2011,h.this_season + 1)
jsd.get_old_games(year_list)
jsd.get_spreads(year_list)
jsd.get_sports_ref_data(year_list)
h.save()
b.betsy()
ng.get()
r.get()