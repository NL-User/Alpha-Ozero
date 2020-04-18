import numpy as np
from config import *
from bit_function import *

is_background_black = True
black_piece = '○' if is_background_black else '●'
white_piece = '●' if is_background_black else '○'


# black_defalt_board = 0x0000000810000000
black_defalt_board = (1 << board_y_size // 2 * board_x_size + (board_x_size // 2 - 1)) | (1 << (board_y_size // 2 - 1) * board_x_size + board_x_size // 2)
# white_board_defalt_value = 0x0000001008000000
white_defalt_board = (1 << board_y_size // 2 * board_x_size + board_x_size // 2) | (1 << (board_y_size // 2 - 1) * board_x_size + board_x_size // 2 - 1)

board_min_size = min(board_x_size,board_y_size)
horizontal_mask_bit = all_standing_bit
for i in range(0,cells_count,board_x_size):
    horizontal_mask_bit ^= 1 << i
    horizontal_mask_bit ^= 1 << i + board_x_size - 1
vertical_mask_bit = (1 << (cells_count - board_x_size)) - 1 ^ ((1 << board_x_size) - 1)
diagonal_mask_bit = (horizontal_mask_bit & vertical_mask_bit)

# 1ビット（左右）
legal_horizontal = [1, board_y_size]
# 8ビット（上下）
legal_vertical = [board_x_size, board_x_size]
# 7ビット（左右）
legal_diagonal_minus = [board_x_size - 1, board_min_size]
# 9ビット（左右）
legal_diagonal_plus = [board_x_size + 1, board_min_size]



class State:
    def __init__(self, black_board = None, white_board = None, turn = False):
        # 連続パスによる終了
        self.pass_end = False
        # ターンの保存(Falseが黒)
        self.turn = turn
        if black_board == None or white_board == None:
            # 石の初期配置
            self.black_board = black_defalt_board
            self.white_board = white_defalt_board
            # self.white_board = white_board_defalt_value
        else:
            # 石の配置
            self.black_board = black_board
            self.white_board = white_board
    # 盤面のコマの数
    def piece_count(self):
        return count_bit(self.black_board) + count_bit(self.white_board)
    # 負けかどうか
    def is_lose(self):
        return self.is_done() and count_bit(self.black_board) < count_bit(self.white_board)

    # 引き分けかどうか
    def is_draw(self):
        return self.is_done() and count_bit(self.black_board) == count_bit(self.white_board)

    # ゲーム終了かどうか
    def is_done(self):
        return self.piece_count() == cells_count or self.pass_end
    # 次の状態の取得
    def next(self, action):
        # print_board(state.legal_actions())
        # state = State(self.black_board, self.white_board, self.turn)
        if action != 0:
            self.is_legal_action_site(action, True)
        self.turn = not self.turn

        # 2回連続パス判定
        if action == 0 and self.legal_actions() == 0:
            self.pass_end = True
    def swap(self):
        if not self.turn:
            return self.black_board, self.white_board
        else:
            return self.white_board, self.black_board

    # 下、右方向の合法手
    def legal_r(self, board, blank, masked, direction, count):
        """Direction >> dir exploring."""
        tmp = masked & (board >> direction)
        # すでに一回やっている、最初と最後の二つはひっくり返せないので-3
        for i in range(count - 3):
            tmp |= masked & (tmp >> direction)
        return blank & (tmp >> direction)
    # 上、左方向の合法手
    def legal_l(self, board, blank, masked, direction, count):
        """Direction << dir exploring."""
        tmp = masked & (board << direction)
        # すでに一回やっている、最初と最後の二つはひっくり返せないので-3
        for i in range(count - 3):
            tmp |= masked & (tmp << direction)
        return blank & (tmp << direction)
    # 合法手が立ったビットを取得
    def legal_actions(self):
        player, opponent = self.swap()
        blank = ~(player | opponent)

        horizontal = opponent & horizontal_mask_bit
        vertical = opponent & vertical_mask_bit
        diagonal = opponent & diagonal_mask_bit 

        legal = self.legal_l(player, blank, vertical, *legal_vertical)
        legal |= self.legal_l(player, blank, horizontal, *legal_horizontal)
        legal |= self.legal_l(player, blank, diagonal, *legal_diagonal_minus)
        legal |= self.legal_l(player, blank, diagonal, *legal_diagonal_plus)
        legal |= self.legal_r(player, blank, vertical, *legal_vertical)
        legal |= self.legal_r(player, blank, horizontal, *legal_horizontal)
        legal |= self.legal_r(player, blank, diagonal, *legal_diagonal_minus)
        legal |= self.legal_r(player, blank, diagonal, *legal_diagonal_plus)
        return legal
    # 左シフト方向
    def reversed_l(self, player, blank_masked, site, direction, count):
        """Direction << for self.reversed()."""
        reverse = 0
        tmp = ~(player | blank_masked) & (site << direction)
        if tmp:
            for i in range(count - 2):
                tmp <<= direction
                if tmp & blank_masked:
                    break
                elif tmp & player:
                    reverse |= tmp >> direction
                    break
                else:
                    tmp |= tmp >> direction
        return reverse
    # 右シフト方向
    def reversed_r(self, player, blank_masked, site, direction, count):
        """Direction >> for self.reversed()."""
        reverse = 0
        tmp = ~(player | blank_masked) & (site >> direction)
        if tmp:
            for i in range(count - 2):
                tmp >>= direction
                if tmp & blank_masked:
                    break
                elif tmp & player:
                    reverse |= tmp << direction
                    break
                else:
                    tmp |= tmp << direction
        return reverse
    # 従来通りの合法手の配列
    def legal_actions_array(self):
        return convert_to_array(self.legal_actions())

    def is_legal_action_site(self, site, flip=False):
        """Return reversed site board."""
        player, opponent = self.swap()
        blank_horizontal = ~(player | opponent & horizontal_mask_bit)
        blank_vertical = ~(player | opponent & vertical_mask_bit)
        blank_diagonal = ~(player | opponent & diagonal_mask_bit)
        rev = self.reversed_l(player, blank_horizontal, site, *legal_horizontal)
        rev |= self.reversed_l(player, blank_vertical, site, *legal_vertical)
        rev |= self.reversed_l(player, blank_diagonal, site, *legal_diagonal_minus)
        rev |= self.reversed_l(player, blank_diagonal, site, *legal_diagonal_plus)
        rev |= self.reversed_r(player, blank_horizontal, site, *legal_horizontal)
        rev |= self.reversed_r(player, blank_vertical, site, *legal_vertical)
        rev |= self.reversed_r(player, blank_diagonal, site, *legal_diagonal_minus)
        rev |= self.reversed_r(player, blank_diagonal, site, *legal_diagonal_plus)
        
        if flip:
            if not self.turn:
                self.black_board ^= (rev ^ site)
                self.white_board ^= rev
            else:
                self.white_board ^= (rev ^ site)
                self.black_board ^= rev
        else:
            # 任意のマスに置くと裏返るマスのフラグが立ったビットを取得
            return rev# 文字列表示
    def __str__(self):
        black = convert_to_np_array(self.black_board)
        white = convert_to_np_array(self.white_board)
        board = black + (white * 2)
        result = ''
        for column in board:
            for v in column:
                if v == 1:
                    result += black_piece
                            
                elif v == 2:
                    result += white_piece
                else:
                    # result += 'ー'
                    result += '-'
                result += '  '
            else:
                result += '\n'
        return result + '\n'

    
# ランダムで行動選択
def random_action(legal_actions):
    legal_actions = np.array(legal_actions, dtype=float)
    action = 0
    # 合法手の数を取得
    legal_action_num = np.sum(legal_actions)
    # 合法手が一つ以上あったら
    if legal_action_num != 0:
        legal_actions[legal_actions == 1] = 1 / legal_action_num
        # print(len(legal_actions))
        # 合法手の中からランダムで一つ選択
        # bit→文字列→listでindexが逆順なので逆順のrangeを取得
        action = int(np.random.choice(range(cells_count - 1,-1,-1),1,p=legal_actions)[0])
        # 何番目の合法手か数える
        action = 1 << action
    return action

   
    
# 動作確認
if __name__ == '__main__':

    # 状態の生成
    state = State()
    print()
    # ゲーム終了までのループ
    while True:
        # ゲーム終了時
        if state.is_done():
            break
        # 文字列表示
        print("{0}ターン目".format(state.piece_count() - 3))
        print(('白' if state.turn else '黒') + 'のターン')
        print(state)
        # 次の状態の取得
        state.next(random_action(state.legal_actions_array()))

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
