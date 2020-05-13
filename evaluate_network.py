# coding: utf-8

# ====================
# 新パラメータ評価部
# ====================

# パッケージのインポート
from game import State, random_action
from pv_mcts import pv_mcts_action
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
from pathlib import Path
from glob import glob
from shutil import copy
import numpy as np
import re

# パラメータの準備
EN_GAME_COUNT = 16  # 1評価あたりのゲーム数（本家は400）
EN_TEMPERATURE = 1.0  # ボルツマン分布の温度


# ベストプレイヤーの交代
def update_best_player():
    copy('./model/latest.h5', './model/best.h5')
    print('Change BestPlayer')


# 奇数を下に丸め込む
def round_odd_num_under(n):
    if n % 2 == 1:
        return n - 1
    else:
        return n


class EvaluateNetwork():
    # 先手プレイヤーのポイント
    def first_player_point(self, ended_state):
        # 1:先手勝利, 0:先手敗北, 0.5:引き分け
        if ended_state.is_draw():
            return 0.5
        elif ended_state.is_lose():
            return 0
        else:
            return 1

    def evaluate(self, model_path_list, evaluate_random_with_first):
        self.model = np.empty(len(model_path_list), dtype=tf.python.keras.engine.training.Model)
        self.index = np.empty(len(model_path_list), dtype=int)

        # モデルとインデックスの初期化
        for i in range(len(model_path_list)):
            self.model[i] = load_model(model_path_list[i])
            # ファイル名からindexを取得
            self.index[i] = int(re.sub(r'(?=.+latest([0-9]+)).+\.h5', r'\1', model_path_list[i]))

        if evaluate_random_with_first:
            point = np.zeros(len(model_path_list))

            for i in range(len(model_path_list)):

                # PV MCTSで行動選択を行う関数の生成
                next_actions = [pv_mcts_action(self.model[i]), random_action]

                point[i] += self.get_game_result_point(next_actions, EN_GAME_COUNT)
                print('{}st AveragePoint: {}'.format(i + 1, point[i] / EN_GAME_COUNT))

            # あくまでランダムなので、結果が悪かった（中央値未満の）モデルに対して、もう一度評価し直し、評価値は2回の平均をとる
            for i in np.argsort(point)[:len(point[point < np.median(point)])]:
                next_actions = [pv_mcts_action(self.model[i]), random_action]
                point[i] = (point[i] + self.get_game_result_point(next_actions, EN_GAME_COUNT)) / 2
                print('{}st AveragePoint: {}'.format(self.index[i], point[i] / EN_GAME_COUNT))

            # 第一四分位数より大きいもので対決
            first_quartile = np.percentile(point, 25)
            self.model = self.model[point > first_quartile]
            self.index = self.index[point > first_quartile]
            # indexを計算するためにpointもフィルタ
            point = point[point > first_quartile]

            # pointが少ない順に並べ替え
            self.index = self.index[np.argsort(point)]
            self.model = self.model[np.argsort(point)]
            self.print_remaining_models()

        while len(self.model) > 1:
            for i in range(len(self.model)):
                if i >= len(self.model) // 2:
                    continue
                j = round_odd_num_under(len(self.model)) - i - 1
                if 0 <= j < len(self.model):
                    self.play_and_sort_model(i, j, EN_GAME_COUNT)

            # 弱い順に並んでいるので、約半分にする
            self.model = self.model[max(1, (len(self.model) - 1) // 2):]
            self.index = self.index[max(1, (len(self.index) - 1) // 2):]
            self.print_remaining_models()
            # print(len(self.index))

        print('Finaly latest{}'.format(self.index[0]))

        # モデルの破棄
        K.clear_session()
        del self.model

        # ベストプレイヤーの交代
        # if average_point >= 0.53:
        #     update_best_player()
        #     return True
        # else:
        #     return False

    def play_and_sort_model(self, a, b, count):
        score = self.get_game_result_point([pv_mcts_action(self.model[a]), pv_mcts_action(self.model[b])], count)
        if score == count / 2:
            # 勝敗がつかなければもう一度戦わせる
            self.play_and_sort_model(a, b, 3)
            return
        elif score < count / 2:
            print("latest{} Vs latest{} is latest{} win!".format(self.index[a], self.index[b], self.index[b]))
            # 事前レートが上（b）の方が買ったらそのまま
        elif score > count / 2:
            print("latest{} Vs latest{} is latest{} win!".format(self.index[a], self.index[b], self.index[a]))
            # 事前レートが下（a）の方が買ったらレートを入れ替え、a（元はb）を削除
            self.model[a], self.model[b] = self.model[b], self.model[a]
            self.index[a], self.index[b] = self.index[b], self.index[a]

    def print_remaining_models(self):
        print("Remaining models: {}".format(self.index))

    def get_game_result_point(self, next_actions, play_game_count):
        total_point = 0
        for i in range(play_game_count):
            # 1ゲームの実行
            if i % 2 == 0:
                total_point += self.play(next_actions)
            else:
                total_point += 1 - self.play(list(reversed(next_actions)))
        return total_point

    # 1ゲームの実行
    def play(self, next_actions):
        # 状態の生成
        state = State()

        # ゲーム終了までループ
        while True:
            # ゲーム終了時
            if state.is_done():
                break

            # 行動の取得
            next_action = next_actions[0] if state.is_black_turn else next_actions[1]

            # 次の状態の取得
            state.next(next_action(state))

        # 先手プレイヤーのポイントを返す
        return self.first_player_point(state)

# ネットワークの評価


def evaluate_network(model_path_list=glob('model/latest*.h5'), evaluate_random_with_first=True):
    EvaluateNetwork().evaluate(model_path_list, evaluate_random_with_first)


# 動作確認
if __name__ == '__main__':
    evaluate_network()
