# coding: utf-8

# ====================
# 学習サイクルの実行
# ====================

# パッケージのインポート
from dual_network import dual_network
from self_play import self_play
from train_network import train_network
from evaluate_network import evaluate_network
from glob import glob


def train_cycle():
    # デュアルネットワークの作成
    if  len(glob('./model/*.h5')) == 0:
        dual_network()

    for i in range(10):
        print('Train',i,'====================')
        # セルフプレイ部
        self_play()

        # パラメータ更新部
        train_network()

        # 新パラメータ評価部
        # evaluate_network()

if __name__ == '__main__':
    train_cycle()