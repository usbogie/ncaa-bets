from ml import decision_tree as dt
#from ml import decision_tree_ou as dto
from ml import ml_shared as mls


def test():
    game_list = mls.get_game_list()
    #dt.run_gridsearch()
    #dt.find_min_samples()
    dt.test(game_list)
    #dto.test()

def today():
    game_list = mls.get_game_list()
    dt.predict_today(game_list)
    #dto.predict_today()
