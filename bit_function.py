import numpy as np
from config import *

# 石の数の取得
def count_bit(bit):
    return bin(bit).count("1")

# 2進数文字列に変換
def convert_to_int(bit):
    if bit < 0:
        bit &= all_standing_bit
    return bit
def convert_to_binary_str(bit):
    bit = convert_to_int(bit)
    return format(bit,"b").zfill(cells_count)
# [0,0,0,0,0,0,1,0 ...] のようなビットの配列に変換
def convert_to_array(bit):
    return list(convert_to_binary_str(bit))
def convert_to_np_array(bit):
    return np.array(convert_to_array(bit)[::-1],dtype=int).reshape(board_y_size,board_x_size)
    
def action_convert_to_hex(action):
    if action == 64:
        return 0
    else:
        return 1 << action
def split_board(text):
    return [ text[i*board_x_size:i*board_x_size+board_x_size] for i in range(int(len(text)/board_y_size)) ]

def print_board(board):
    board = convert_to_binary_str(board)
    board = split_board(board)
    for st in board:
        result = ""
        for s in st.format('08'):
            result += s + ' '
        print(result)
    print()