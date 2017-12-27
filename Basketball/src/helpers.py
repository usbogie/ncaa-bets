import json
import sys
import os
import pandas as pd
from datetime import datetime, timedelta, date

path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(path,'..','data')
database = os.path.join(data_path,'games')
this_season = date.today().year + 1 if date.today().month > 4 else date.today().year
first_season = 2011
all_years = range(first_season, this_season + 1)

months = {
    11: 'November',
    12: 'December',
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April'
}

def read_names():
    names_path = os.path.join(path,'names','names.json')
    with open(names_path,'r') as infile:
        return json.load(infile)