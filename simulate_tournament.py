import json

with open('ncaa_teams.json','r') as infile:
    ncaa_teams = json.load(infile)

bracket = {}

# Make Bracket
for i in range(1,5):
    bracket[i] = {}
    for j in range(1,17):
        bracket[i][j] = {}
for team in ncaa_teams:
    bracket[team['region']][team['seed']]['em'] = team['em']
    bracket[team['region']][team['seed']]['name'] = team['name']

winners = {}
for i in range(1,64):
    winners[i] = {}
for i in range(1,5):
    for j in range(1,17):
        if j > 8:
            winners[(i-1)*8+17-j]['und'] = bracket[i][j]['name']
            winners[(i-1)*8+17-j]['und_em'] = bracket[i][j]['em']
        else:
            winners[(i-1)*8+j]['fav'] = bracket[i][j]['name']
            winners[(i-1)*8+j]['fav_em'] = bracket[i][j]['em']
for i in range(6):
    rnd = 64 - 2 ** (6-i) + 1
    if i < 2:
        if i == 0:
            print("First Round\n")
        else:
            print("Round of 32\n")
        games = 8 // 2 ** i
        for k in range(games):
            if i == 0:
                print("{} Seeds:".format(k+1))
            else:
                print("{} v {}:".format(k+1,games*2-k))
            for j in range(4):
                game = rnd + games * j + k
                em_diff = round((winners[game]['fav_em'] - winners[game]['und_em']) * .35)
                print(em_diff, winners[game]['fav'], winners[game]['und'])
            for j in range(4):
                game = rnd + games * j + k
                y = input("Pick {}? ".format(winners[game]['fav']))
                winners[game]['winner'] = winners[game]['fav'] if y == 'y' else winners[game]['und']
                winner = (winners[game]['fav'],winners[game]['fav_em']) if y == 'y' else (winners[game]['und'],winners[game]['und_em'])
                next_k = k if k < games/2 else games-k-1
                next_rnd = 64 - 2 ** (6-(i+1)) + 1
                next_game = next_rnd + games/2 * j + next_k
                pick = 'fav' if k < games/2 else 'und'
                winners[next_game][pick] = winner[0]
                winners[next_game][pick+'_em'] = winner[1]
            print('\n')
    elif i == 2:
        print("Sweet 16\n")
        for j in range(4):
            first = rnd + j * 2
            for k in range(2):
                em_diff = round((winners[first+k]['fav_em'] - winners[first+k]['und_em']) * .35)
                print(em_diff, winners[first+k]['fav'], winners[first+k]['und'])
            for k in range(2):
                y = input("Pick {}? ".format(winners[first+k]['fav']))
                winners[first+k]['winner'] = winners[first+k]['fav'] if y == 'y' else winners[first+k]['und']
                winner = (winners[first+k]['fav'],winners[first+k]['fav_em']) if y == 'y' else (winners[first+k]['und'],winners[first+k]['und_em'])
                next_rnd = 64 - 2 ** (6-(i+1)) + 1
                next_game = next_rnd + j
                pick = 'fav' if not k else 'und'
                winners[next_game][pick] = winner[0]
                winners[next_game][pick+'_em'] = winner[1]
            print('\n')
    else:
        if i == 3:
            print("Elite 8\n")
        elif i == 4:
            print("Final 4\n")
        else:
            print("Championship\n")
        games = 2 ** (5-i)
        for j in range(games):
            em_diff = round((winners[rnd+j]['fav_em'] - winners[rnd+j]['und_em']) * .35)
            print(em_diff, winners[rnd+j]['fav'], winners[rnd+j]['und'])
        for j in range(games):
            y = input("Pick {}? ".format(winners[rnd+j]['fav']))
            winners[rnd+j]['winner'] = winners[rnd+j]['fav'] if y == 'y' else winners[rnd+j]['und']
            winner = (winners[rnd+j]['fav'],winners[rnd+j]['fav_em']) if y == 'y' else (winners[rnd+j]['und'],winners[rnd+j]['und_em'])
            next_rnd = 64 - 2 ** (6-(i+1)) + 1
            if next_rnd == 64:
                break
            next_game = next_rnd + j//2
            pick = 'fav' if not (j % 2) else 'und'
            winners[next_game][pick] = winner[0]
            winners[next_game][pick+'_em'] = winner[1]
        print('\n')

f = open('bracket_results.txt','w+')
results = []
for i in range(1,64):
    if i == 1:
        print("Round of 32")
        results.append("Round of 32\n")
    elif i == 33:
        print("\nSweet 16")
        results.append("\nSweet 16\n")
    elif i == 49:
        print("\nElite 8")
        results.append("\nElite 8\n")
    elif i == 57:
        print("\nFinal 4")
        results.append("\nFinal 4\n")
    elif i == 61:
        print("\nChampionship")
        results.append("\nChampionship\n")
    elif i == 63:
        print("\nChampion")
        results.append("\nChampion\n")
    print(winners[i]['winner'])
    results.append("{}\n".format(winners[i]['winner']))
f.writelines(results)
