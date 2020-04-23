import numpy as np
from config import *

all_standing_bit = (1 << CELLS_COUNT) - 1

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
    return format(bit,"b").zfill(CELLS_COUNT)
# [0,0,0,0,0,0,1,0 ...] のようなビットの配列に変換
def convert_to_array(bit):
    return [int(i) for i in convert_to_binary_str(bit)]
def convert_to_np_array(bit):
    return np.array(convert_to_array(bit)[::-1],dtype=int).reshape(BOARD_Y_SIZE,BOARD_X_SIZE)
