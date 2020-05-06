# coding: utf-8

# ====================
# パラメータ更新部
# ====================

# パッケージのインポート
from dual_network import DN_INPUT_SHAPE
from tensorflow.keras.callbacks import LearningRateScheduler, LambdaCallback, EarlyStopping
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
import numpy as np
import pickle
import os
from glob import glob
import pandas as pd


# 学習データの読み込み
def load_data():
    history_path = sorted(glob('./data/*.history'))[-1]
    with open(history_path, mode='rb') as f:
        return pickle.load(f)

# デュアルネットワークの学習
def train_network(epoch_count=200):
    # 学習データの読み込み
    history = load_data()
    xs, turn_nums, y_policies, y_values = zip(*history)

    # 学習のための入力データのシェイプの変換
    a, b, c = DN_INPUT_SHAPE
    xs = np.array(xs)
    xs = xs.reshape(len(xs), c, a, b).transpose(0, 2, 3, 1)
    turn_nums = np.array(turn_nums)
    y_policies = np.array(y_policies)
    y_values = np.array(y_values)
    # 最新モデルの読み込み
    model = load_model(sorted(glob('./model/*.h5'))[-1])

    # モデルのコンパイル
    model.compile(loss=['categorical_crossentropy', 'huber_loss'], optimizer='adam')

    # 学習率
    def step_decay(epoch):
        x = 0.0008
        if epoch >= 150: x = 0.0001
        elif epoch >= 100: x = 0.00025
        elif epoch >= 50: x = 0.0005
        return x
    lr_decay = LearningRateScheduler(step_decay)
    early_stopping = EarlyStopping(min_delta=0.0, patience=10, verbose=1)

    # 学習の実行
    history = model.fit([xs, turn_nums], [y_policies, y_values], batch_size=32, epochs=epoch_count, validation_split=0.2,
            verbose=1, callbacks=[lr_decay, early_stopping])
    print('')

    model_index_str = str(len(glob('./model/latest*.h5')) + 1)
    # 学習履歴をファイルに保存
    os.makedirs('./history/', exist_ok=True)
    pd.DataFrame.from_dict(history.history).to_csv('history/history' + model_index_str + '.csv',index=False)

    # 最新プレイヤーのモデルの保存
    model.save('./model/latest' + model_index_str + '.h5')

    # モデルの破棄
    K.clear_session()
    del model

# 動作確認
if __name__ == '__main__':
    train_network()
