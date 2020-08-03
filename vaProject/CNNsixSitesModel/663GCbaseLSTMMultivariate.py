# multivariate cnn lstm
from numpy import array
from keras.models import Sequential
from keras.layers import LSTM
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import TimeDistributed
from keras.layers import Dropout
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.optimizers import Adam
import os
import numpy as np
import pandas as pd
import tensorflow as tf
import random
import matplotlib.pyplot as plt
import math

seed = 2
os.environ['PYTHONHASHSEED'] = str(seed)
np.random.seed(seed)
tf.set_random_seed(seed)
random.seed(seed)


def split_sequences(sequences, n_steps_in, n_steps_out):
    X, y = list(), list()
    for i in range(len(sequences)):
        # find the end of this pattern
        end_ix = i + n_steps_in
        out_end_ix = end_ix + n_steps_out
        # check if we are beyond the dataset
        if out_end_ix > len(sequences):
            break
        # gather input and output parts of the pattern
        seq_x, seq_y = sequences[i:end_ix, :], sequences[end_ix:out_end_ix, 0]
        X.append(seq_x)
        y.append(seq_y)
    return array(X), array(y)


path = '../editData/663GCdataMultivariateLSTM.csv'
# path = '../editData/663GEdataMultivariateLSTM.csv'
# path = '../editData/663A4dataMultivariateLSTM.csv'
# path = '../editData/663GDdataMultivariateLSTM.csv'
# path = '../editData/663GAdataMultivariateLSTM.csv'
# path = '../editData/663dataMultivariateLSTM.csv'
# path = '../editData/663GBdataMultivariateLSTM.csv'

df = pd.read_csv(path)
df = df[['n_walkins', 'dayofweek', 'day', 'month', 'year']]
df = df[(df['dayofweek'] != 5) & (df['dayofweek'] != 6)]
df = df[['n_walkins', 'dayofweek', 'day', 'month', 'year']]
data = df.values

# choose a number of time steps
n_steps_in, n_steps_out = 16, 1  # n_steps_out means the number of future steps. 1 means predicting one future
train_ratio = 0.30

train_mean = np.mean(data[:math.floor(len(data) * train_ratio)], axis=0)
train_std = np.std(data[:math.floor(len(data) * train_ratio)], axis=0)

data = (data - train_mean) / train_std

X_train, y_train = split_sequences(data[:math.floor(len(data) * train_ratio)], n_steps_in, n_steps_out)
X_test, y_test = split_sequences(data[math.floor(len(data) * train_ratio):], n_steps_in, n_steps_out)

# reshape from [samples, timesteps] into [samples, subsequences, timesteps, features]
n_features = X_train.shape[2]
n_seq = 4
n_steps = 4
X_train = X_train.reshape((X_train.shape[0], n_seq, n_steps, n_features))

# define model
model = Sequential()
model.add(
    TimeDistributed(Conv1D(filters=40, kernel_size=1, activation='relu'), input_shape=(None, n_steps, n_features)))
model.add(TimeDistributed(MaxPooling1D(pool_size=2)))
model.add(TimeDistributed(Flatten()))
model.add(LSTM(30, activation='relu'))
model.add(Dense(1))
model.compile(optimizer=Adam(lr=0.001), loss='mae')

# fit model
X_test = X_test.reshape((X_test.shape[0], n_seq, n_steps, n_features))

history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=20, verbose=0)
yhat = model.predict(x=X_test, verbose=0)

y_test = y_test * train_std[0] + train_mean[0]
yhat = yhat * train_std[0] + train_mean[0]

pd.DataFrame({'loss': history.history['loss'], 'val_loss': history.history['val_loss']}).plot()
plt.show()

# post processing
yhat = pd.Series(yhat.reshape(-1)).apply(math.floor).apply(lambda x: x if x > 0 else 0)
y_test = pd.Series(y_test.reshape(-1))
loss_mae = np.abs(yhat - y_test).mean()
print('MAE')
print(loss_mae)
# pd.DataFrame({'predict': yhat, 'target': y_test}).plot(title='loss_mae ' + str(loss_mae))
# plt.show()
#
#
# np.abs(pd.Series([df['n_walkins'][:math.floor(len(df) * train_ratio)].mean()] * y_test.shape[0]) - y_test).mean()

