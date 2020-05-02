# coding: utf-8

# ====================
# モンテカルロ木探索の作成
# ====================

# パッケージのインポート
from config import CELLS_COUNT
from game import State, action_convert_to_bit, convert_to_np_array, count_bit
from dual_network import DN_INPUT_SHAPE
from math import sqrt
from tensorflow.keras.models import load_model
from glob import glob
import numpy as np
# パラメータの準備
PV_EVALUATE_COUNT = 50 # 1推論あたりのシミュレーション回数（本家は1600）
# 勝率と手の予測確率のバランスを調整する定数
C_PUCT = 1.0

# 推論
def predict(model, state):
    # 16進数（int）から2進数の8×8の配列に変換（int）
    black_board = convert_to_np_array(state.black_board)
    white_board = convert_to_np_array(state.white_board)

    # 推論のための入力データのシェイプの変換
    board = np.array([black_board, white_board]).transpose(1, 2, 0).reshape(1,*DN_INPUT_SHAPE)
    turn = np.array([state.get_turn_num()])
    # 推論
    y = model.predict([board, turn], batch_size=1)

    # 方策の取得
    policies = np.array(y[0][0][np.array(state.legal_actions_index()) + 1]) # 合法手のみ
    # 合計1の確率分布に変換
    if np.sum(policies) == 0.0:
        policies.fill(1 / len(policies))
    else:
        policies /= np.sum(policies)

    # 価値の取得
    value = y[1][0][0]
    return policies, value

# ノードのリストを試行回数のリストに変換
def nodes_to_scores(nodes):
    scores = []
    for c in nodes:
        scores.append(c.n)
    return scores

# モンテカルロ木探索のスコアの取得
def pv_mcts_scores(model, state, temperature):
    # モンテカルロ木探索のノードの定義
    class Node:
        # ノードの初期化
        def __init__(self, state, p):
            self.state = state # 状態
            self.p = p # 方策の確率分布
            self.w = 0 # 累計価値
            self.n = 0 # 試行回数
            self.child_nodes = None  # 子ノード群
            self.is_black_flag = state.is_black_turn # 自分が白なのか黒なのかを保存

        # 局面の価値の計算
        def evaluate(self):
            # ゲーム終了時
            if self.state.is_done():
                # 勝敗結果で価値を取得
                value = self.state.get_reward(self.is_black_flag)

                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1
                return value

            # 子ノードが存在しない時
            if not self.child_nodes:
                # ニューラルネットワークの推論で方策と価値を取得
                policies, value = predict(model, self.state)

                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1

                # 子ノードの展開
                self.child_nodes = []
                # legal_array = state.legal_actions_array() + ([0] if 0 < count_bit(state.legal_actions()) else [1])
                
                for i, policie in zip(state.legal_actions_index(), policies):
                # for i,policie in zip([i for i, v in zip(range(CELLS_COUNT - 1,-2,-1), self.state.legal_actions_array()) if v == 1], policies):
                    # 
                    self.child_nodes.append(Node(self.state.get_next(action_convert_to_bit(i)),policie))
                return value
            
            # 子ノードが存在する時
            else:
                # アーク評価値が最大の子ノードの評価で価値を取得
                value = self.next_child_node().evaluate()

                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1
                return value

        # アーク評価値が最大の子ノードを取得
        def next_child_node(self):
            # アーク評価値の計算
            t = sum(nodes_to_scores(self.child_nodes))
            pucb_values = []
            for child_node in self.child_nodes:
                pucb_values.append((child_node.w / child_node.n if child_node.n else 0.0) +
                    C_PUCT * child_node.p * sqrt(t) / (1 + child_node.n))

            # アーク評価値が最大の子ノードを返す
            return self.child_nodes[np.argmax(pucb_values)]

    # 現在の局面のノードの作成
    root_node = Node(state,0)

    # 複数回の評価の実行
    for _ in range(PV_EVALUATE_COUNT):
        root_node.evaluate()

    # 合法手の確率分布
    scores = nodes_to_scores(root_node.child_nodes)
    if temperature == 0: # 最大値のみ1
        action = np.argmax(scores)
        scores = np.zeros(len(scores))
        scores[action] = 1
    else: # ボルツマン分布でバラつき付加
        scores = boltzman(scores, temperature)
    return scores

# モンテカルロ木探索で行動選択
def pv_mcts_action(model, temperature=0):
    def pv_mcts_action(state):
        scores = pv_mcts_scores(model, state, temperature)
        action = int(np.random.choice(state.legal_actions_index(), p=scores))
        # print(action)
        # print(int(action/8),':',action%8)
        return action_convert_to_bit(action)
    return pv_mcts_action

# ボルツマン分布
def boltzman(xs, temperature):
    xs = [x ** (1 / temperature) for x in xs]
    return [x / sum(xs) for x in xs]

# 動作確認
if __name__ == '__main__':
    # モデルの読み込み
    path = sorted(glob('./model/*.h5'))[-1]
    model = load_model(str(path))

    # 状態の生成
    state = State()
    print()

    # モンテカルロ木探索で行動取得を行う関数の生成
    next_action = pv_mcts_action(model, 1.0)

    # ゲーム終了までループ
    while True:
        # ゲーム終了時
        if state.is_done():
            break

        print("{0}ターン目".format(state.piece_count() - 3))
        print(('白' if state.is_black_turn else '黒') + 'のターン')
        print(state)

        # 次の状態の取得
        state.next(next_action(state))
    
    print('終了\n')
    print(state)
    print("黒:{0} 白:{1}".format(count_bit(state.black_board), count_bit(state.white_board)))
    result = ''
    if state.is_draw():
        result = "引き分け"
    elif state.is_lose():
        result = "白の勝ち"
    else:
        result = "黒の勝ち"
        
    print(result)
