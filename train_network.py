# coding: utf-8

# ====================
# パラメータ更新部
# ====================

# パッケージのインポート
import os
import re
from glob import glob
import pickle
import numpy as np
import pandas as pd
from tensorflow.keras.callbacks import LearningRateScheduler, LambdaCallback, EarlyStopping
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
from dual_network import DN_INPUT_SHAPE
from config import BOARD_X_SIZE, BOARD_Y_SIZE, CELLS_COUNT
from game import board_rotation_and_reverse, board_rotation_and_reverse_all, policies_rotation_and_reverse_all


# 学習データの読み込み
def load_data(history_path):
    with open(history_path, mode='rb') as f:
        return pickle.load(f)


def board_array_convert_to_str_array(black_board_array, white_board_array):
    board_array = (np.array(black_board_array) + np.array(white_board_array)).tolist()
    return [''.join(map(str, board_array[i])) for i in range(len(board_array))]


# デュアルネットワークの学習
def train_network(model_path=sorted(glob('./model/*.h5'))[-1], learn_data_path_list=glob('./data/*.history'), epoch_count=200):
    # 学習率
    def step_decay(epoch):
        x = 0.0008
        if epoch >= 150:
            x = 0.0001
        elif epoch >= 100:
            x = 0.00025
        elif epoch >= 50:
            x = 0.0005
        return x

    # 最新モデルの読み込み
    model = load_model(model_path)

    for learn_data_path in learn_data_path_list:
        # 学習データの読み込み
        history = load_data(learn_data_path)
        # board, turn_nums, y_policies, y_values = zip(*history)
        board = []
        turn_nums = []
        y_policies = []
        y_values = []
        for i in range(len(history)):
            # 一次元の盤面・ポリシーを回転・反転させて8倍にしたリスト
            black_board = board_rotation_and_reverse_all(np.array(history[i][0][0]))
            white_board = board_rotation_and_reverse_all(np.array(history[i][0][1]))
            policies = policies_rotation_and_reverse_all(np.array(history[i][2]))
            # 重複を削除するために盤面をstringに変換したlist
            board_str = board_array_convert_to_str_array(black_board, white_board)
            # 重複を削除したblack_board_str
            unique_board_str = list(set(board_array_convert_to_str_array(black_board, white_board)))

            # ポリシーと盤面は重複を除いて追加
            for j in range(len(unique_board_str)):
                for k in range(len(board_str)):
                    if unique_board_str[j] == board_str[k]:
                        board.append([black_board[k], white_board[k]])
                        y_policies.append(policies[k])

                        # 一緒にターンと価値も追加
                        turn_nums.append(history[i][1])
                        y_values.append(history[i][3])
                        break

        # 学習のための入力データのシェイプの変換
        turn_nums = np.array(turn_nums)
        y_policies = np.array(y_policies)
        y_values = np.array(y_values)
        board = np.array(board)
        a, b, c = DN_INPUT_SHAPE
        board = board.reshape(len(board), c, a, b).transpose(0, 2, 3, 1)
        print("board: {} turn: {} policy: {} value: {}".format(len(board), len(turn_nums), len(y_policies), len(y_values)))
        # モデルのコンパイル
        model.compile(loss=['categorical_crossentropy', 'huber_loss'], optimizer='adam')

        lr_decay = LearningRateScheduler(step_decay)
        early_stopping = EarlyStopping(min_delta=0.1, patience=10, verbose=1)

        # 学習の実行
        history = model.fit([board, turn_nums], [y_policies, y_values], batch_size=64, epochs=epoch_count, validation_split=0.2,
                            verbose=1, callbacks=[lr_decay, early_stopping])
        print()
        model_index_str = len(glob('./model/latest*.h5')) + 1
        # 学習履歴をファイルに保存
        os.makedirs('./history/', exist_ok=True)
        pd.DataFrame.from_dict(history.history).to_csv('history/history{}.csv'.format(model_index_str), index=False)

        # モデルの保存
        model.save('./model/latest{}.h5'.format(model_index_str))
    # モデルの破棄
    K.clear_session()
    del model


# 動作確認
if __name__ == '__main__':
    train_network()
