# -*- coding: utf-8 -*-
from pv_mcts import pv_mcts_action
from tensorflow.keras.models import load_model
from game import State, random_action
from bit_function import count_bit
import random
from glob import glob
if __name__ == '__main__':
    # 状態の生成
    state = State()
    model = load_model(sorted(glob('model/*h5'))[-1])
    next_action = pv_mcts_action(model, 0.0)

    AI_color = bool(random.randint(0,1))
    random_color = not AI_color

    print("黒: {0}".format("AI" if AI_color else "Random"))
    print("白: {0}".format("AI" if not AI_color else "Random"))
    print('\n')
        
    # ゲーム終了までのループ
    while True:
        # ゲーム終了時
        if state.is_done():
            break

        print("{0}ターン目".format(state.piece_count() - 3))
        print(('白' if state.is_black_turn else '黒') + 'のターン')
        print(state)

        if state.is_black_turn == random_color:
            # 次の状態の取得
            state.next(random_action(state))
        else:
            state.next(next_action(state))
    print('終了\n')
    print(state)
    print("黒:{0} 白:{1}".format(count_bit(state.black_board), count_bit(state.white_board)))

    if state.is_draw():
        result = "引き分け"
    elif state.get_reward(AI_color) == 1:
        result = "AI（{0}）の勝利".format("黒" if AI_color else "白")
    else:
        result = "Random（{0}）の勝利".format("黒" if random_color else "白")
        
    print(result)
