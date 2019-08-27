# -*- coding: utf-8 -*-
from pv_mcts import pv_mcts_action
from tensorflow.keras.models import load_model
from game import *
import random
if __name__ == '__main__':
    # 状態の生成
    state = State()
    model = load_model('./model/best.h5')
    next_action = pv_mcts_action(model, 0.0)

    AI_color = random.randint(0,1)
    random_color = None
    if AI_color == 0:
        random_color = 1
    else:
        random_color = 0

    count = 0
        
    # ゲーム終了までのループ
    while True:
        # ゲーム終了時
        if state.is_done():
            break
        if (count % 2) == random_color:
            # 次の状態の取得
            state = state.next(random_action(state))
        else:
            state = state.next(next_action(state))
    print("黒:{0} 白:{1}".format(state.piece_count(state.pieces), state.piece_count(state.enemy_pieces)))
