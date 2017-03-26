import numpy as np
import pickle

from sklearn import linear_model
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import ShuffleSplit, cross_val_score
from sklearn.metrics import r2_score, make_scorer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.utils import shuffle, check_random_state

from ctable import ctable

# It looks like polynomial regression works best here, but sometimes 
# degree=5 performs better than degree=3
POLY_DEGREE = 3

# We can't reliably include black in color table, so if dark colors fail
# use this to manually append this amount of black samples
BLACK_SAMPLES = 1


vctable = np.load('color-table.npy')
w, h, _ = ctable.shape

X = vctable.reshape(-1, 3).astype(np.float32) / 255
Y = ctable.reshape(-1, 3).astype(np.float32) / 255

max_X = max(X[-1])
X = X/max_X

for _ in range(BLACK_SAMPLES):
  X = np.append(X, [[0, 0, 0]], axis=0)
  Y = np.append(Y, [[0, 0, 0]], axis=0)

print('Number of samples: %d' % (len(X)))


"""
Of course AdaBoost makes it better, but much slower...
AdaBoostRegressor(MultiOutputRegressor(...))
"""

clf = Pipeline([
      ('standardscaler', StandardScaler(with_mean=True, with_std=True, copy=True)),
      ('poly', PolynomialFeatures(degree=POLY_DEGREE)),
      ('linear', linear_model.LinearRegression())])
      

clf.fit(X, Y) 

print('Self-score: ', clf.score(X, Y))
split = ShuffleSplit(n_splits=6, test_size=0.20, random_state=0)

print('CV score: ', cross_val_score(clf, X, Y, cv=split))


with open('model.data', 'wb') as f:
  f.write(pickle.dumps(clf))
