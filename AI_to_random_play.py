# -*- coding: utf-8 -*-
from pv_mcts import pv_mcts_action
from tensorflow.keras.models import load_model
from game import State, random_action
from bit_function import count_bit
from evaluate_network import get_filename_from_file_path
import random
from glob import glob


def play_with_random(next_action, view_mode=False):
    # 状態の生成
    state = State()

    AI_color = bool(random.randint(0, 1))
    random_color = not AI_color

    if view_mode:
        print("黒: {0}".format("AI" if AI_color else "Random"))
        print("白: {0}".format("AI" if not AI_color else "Random"))
        print('\n')

    # ゲーム終了までのループ
    while True:
        # ゲーム終了時
        if state.is_done():
            break
        if view_mode:
            print("{0}ターン目".format(state.piece_count() - 3))
            print(('白' if state.is_black_turn else '黒') + 'のターン')
            print(state)

        if state.is_black_turn == random_color:
            # 次の状態の取得
            state.next(random_action(state))
        else:
            state.next(next_action(state))

    if view_mode:
        print('終了\n')
        print(state)
        print("黒:{0} 白:{1}".format(count_bit(state.black_board), count_bit(state.white_board)))

    if state.is_draw():
        result_str = "引き分け"
        result = 0

    elif state.get_reward(AI_color) == 1:
        result_str = "AI（{0}）の勝利".format("黒" if AI_color else "白")
        result = 1
    else:
        result_str = "Random（{0}）の勝利".format("黒" if random_color else "白")
        result = -1
    if view_mode:
        print(result_str)
    return result


def evaluation_with_random(model_path_list=sorted(glob('model/*h5')), game_num=32):
    for model_path in model_path_list:
        win = draw = lose = 0
        next_action = pv_mcts_action(load_model(model_path, compile=False))
        for _ in range(game_num):
            result = play_with_random(next_action)

            # 試合結果を保持
            if result == 1:
                win += 1
            elif result == 0:
                draw += 1
            else:
                lose += 1
        # ファイル名からインデックスを取り出す
        print("{} win: {} draw: {} lose: {}".format(get_filename_from_file_path(model_path), win, draw, lose))


if __name__ == '__main__':
    play_with_random(view_mode=True)
