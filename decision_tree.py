from pprint import pprint
import numpy as np

def partition(a):
    return {c: (a==c).nonzero()[0] for c in np.unique(a)}

def entropy(s):
    res = 0
    val, counts = np.unique(s, return_counts=True)
    freqs = counts.astype('float')/len(s)
    for p in freqs:
        if p != 0.0:
            res -= p * np.log2(p)
    return res

def mutual_information(y, x):
    res = entropy(y)
    # We partition x, according to attribute values x_i
    val, counts = np.unique(x, return_counts=True)
    freqs = counts.astype('float')/len(x)
    # We calculate a weighted average of the entropy
    for p, v in zip(freqs, val):
        res -= p * entropy(y[x == v])
    return res

def is_pure(s):
    return len(set(s)) == 1

def recursive_split(x, y, feature_dict):
    # If there could be no split, just return the original set
    if is_pure(y) or len(y) == 0:
        return y
    # We get attribute that gives the highest mutual information
    gain = np.array([mutual_information(y, x_attr) for x_attr in x.T])
    selected_attr = np.argmax(gain)

    # If there's no gain at all, nothing has to be done, just return the original set
    if np.all(gain < 1e-6):
        return y
    sets = partition(x[:, selected_attr])
    res = {}
    for k, v in sets.items():
        y_subset = y.take(v, axis=0)
        x_subset = x.take(v, axis=0)

        res["{} = {}".format(feature_dict[selected_attr], k)] = recursive_split(x_subset, y_subset, feature_dict)
    return res

if __name__ == '__main__':
    x1 = [0, 1, 1, 2, 2, 2]
    x2 = [0, 0, 1, 1, 1, 0]
    y = np.array([0, 0, 0, 1, 1, 0])
    X = np.array([x1, x2]).T
    pprint(recursive_split(X, y))
