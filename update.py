import espn_daily_scraper as espn
from kp_data import kp_scraper as kp
from os_data import os_scraper as os
from sb_data import sportsbook_scraper as sb

espn.()
kp.extract_kenpom(2017)
#os.get_oddsshark(2017,links,names) # Slow
sb.get_todays_sportsbook_lines()
