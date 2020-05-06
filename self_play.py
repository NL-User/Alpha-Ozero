# coding: utf-8

# ====================
# セルフプレイ部
# ====================

from config import CELLS_COUNT
from game import State, action_convert_to_bit
from bit_function import convert_to_array
from pv_mcts import pv_mcts_scores
from datetime import datetime
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
from glob import glob
import pickle
import os
import platform

# パラメータの準備
SP_TEMPERATURE = 1.0 # ボルツマン分布の温度パラメータ

# 学習データの保存
def write_data(history):
    now = datetime.now()
    os.makedirs('./data/', exist_ok=True) # フォルダがない時は生成
    save_path = './data/{:04}{:02}{:02}{:02}{:02}{:02}.history'.format(
        now.year, now.month, now.day, now.hour, now.minute, now.second)
    with open(save_path, mode='wb') as f:
        pickle.dump(history, f)

# 1ゲームの実行
def play(model):
    # 学習データ
    history = []

    # 状態の生成
    state = State()

    while True:
        # ゲーム終了時
        if state.is_done():
            break
        
        # 合法手の確率分布の取得
        scores = pv_mcts_scores(model, state, SP_TEMPERATURE)

        # 学習データに状態と方策を追加
        policies = [0] * (CELLS_COUNT + 1)
        for i, policy in zip(state.legal_actions_index(), scores):
            policies[i + 1] = policy
        history.append([[convert_to_array(state.black_board), convert_to_array(state.white_board)], state.get_turn_num(), policies, None])

        # 行動の取得
        action = int(np.random.choice(state.legal_actions_index(), p=scores))
        action = action_convert_to_bit(action)

        # 次の状態の取得
        state = state.get_next(action)

    # 学習データに価値を追加
    value = state.get_reward(True)
    for i in range(len(history)):
        history[i][3] = value if i % 2 == 0 else -value
    return history

# セルフプレイ
def self_play(iterate_match_count = 1):
    # 学習データ
    history = []

    # 最新のモデルの読み込み
    model = load_model(sorted(glob('./model/*.h5'))[-1])

    # 複数回のゲームの実行
    for i in range(iterate_match_count):
        # 1ゲームの実行
        h = play(model)
        history.extend(h)

        # 出力
        print('\rSelfPlay {}/{}'.format(i+1, iterate_match_count), end='')
    print('')

    # 学習データの保存
    write_data(history)

    # モデルの破棄
    K.clear_session()
    del model

# 動作確認
if __name__ == '__main__':
    self_play()
