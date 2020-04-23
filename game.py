import numpy as np
import copy
from config import BOARD_X_SIZE, BOARD_Y_SIZE, CELLS_COUNT
from bit_function import all_standing_bit, count_bit, convert_to_array, convert_to_np_array

is_background_black = True
black_piece = '○' if is_background_black else '●'
white_piece = '●' if is_background_black else '○'


# black_defalt_board = 0x0000000810000000
black_defalt_board = (1 << BOARD_Y_SIZE // 2 * BOARD_X_SIZE + (BOARD_X_SIZE // 2 - 1)) | (1 << (BOARD_Y_SIZE // 2 - 1) * BOARD_X_SIZE + BOARD_X_SIZE // 2)
# white_board_defalt_value = 0x0000001008000000
white_defalt_board = (1 << BOARD_Y_SIZE // 2 * BOARD_X_SIZE + BOARD_X_SIZE // 2) | (1 << (BOARD_Y_SIZE // 2 - 1) * BOARD_X_SIZE + BOARD_X_SIZE // 2 - 1)

board_min_size = min(BOARD_X_SIZE,BOARD_Y_SIZE)
horizontal_mask_bit = all_standing_bit
for i in range(0,CELLS_COUNT,BOARD_X_SIZE):
    horizontal_mask_bit ^= 1 << i
    horizontal_mask_bit ^= 1 << i + BOARD_X_SIZE - 1
vertical_mask_bit = (1 << (CELLS_COUNT - BOARD_X_SIZE)) - 1 ^ ((1 << BOARD_X_SIZE) - 1)
diagonal_mask_bit = (horizontal_mask_bit & vertical_mask_bit)

# 1ビットシフト（左右）
legal_horizontal = (1, BOARD_Y_SIZE)
# 8ビットシフト（上下）
legal_vertical = (BOARD_X_SIZE, BOARD_X_SIZE)
# 7ビットシフト（左右）
legal_diagonal_minus = (BOARD_X_SIZE - 1, board_min_size)
# 9ビットシフト（左右）
legal_diagonal_plus = (BOARD_X_SIZE + 1, board_min_size)



class State:
    def __init__(self, black_board = None, white_board = None, is_black_turn = False):
        # 連続パスによる終了
        self.pass_end = False
        # ターンの保存(Falseが黒)
        self.is_black_turn = is_black_turn
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
    # 黒ならTrueを入力すると報酬を得られる
    def get_reward(self, is_black_flag):
        # 引き分けは0、勝てば1、負ければ-1
        if self.is_draw():
            return 0
        elif (not is_black_flag and self.is_lose()) or (is_black_flag and not self.is_lose()):
            return 1
        else:
            return -1

    # 負けかどうか
    def is_lose(self):
        return count_bit(self.black_board) < count_bit(self.white_board)

    # 引き分けかどうか
    def is_draw(self):
        return count_bit(self.black_board) == count_bit(self.white_board)

    # ゲーム終了かどうか
    def is_done(self):
        return self.pass_end or self.piece_count() == CELLS_COUNT
    # 次の状態の取得
    def next(self, action):
        # print_board(state.legal_actions())
        # state = State(self.black_board, self.white_board, self.turn)
        if action != 0:
            self.is_legal_action_site(action, True)
        self.is_black_turn = not self.is_black_turn

        # 2回連続パス判定
        if action == 0 and self.legal_actions() == 0:
            self.pass_end = True
    def get_next(self,action):
        state = copy.deepcopy(self)
        # state = State(self.black_board, self.white_board, self.is_black_turn)
        state.next(action)
        return state
    # ターンによる並び替え
    def swap(self):
        if not self.is_black_turn:
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

    # 従来通りの合法手の配列
    def legal_actions_array(self):
        return convert_to_array(self.legal_actions())

    def legal_actions_index(self):
        index = [i for i, v in zip(range(CELLS_COUNT - 1, -1, -1), self.legal_actions_array()) if v == 1]
        if not index:
            index = [-1]
        return index

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
            if not self.is_black_turn:
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

    
def action_convert_to_bitboard(action):
        if action == -1:
            return 0
        else:
            return 1 << action

# ランダムで行動選択
def random_action(legal_actions):
    # 合法手の数を取得
    legal_action_num = int(np.sum(legal_actions))
    # 合法手が一つ以上あったら
    if legal_action_num != 0:
        legal_actions = np.array(legal_actions,dtype=float)
        # legal_actions /= legal_action_num
        legal_actions[legal_actions == 1] = 1 / legal_action_num
        # print(len(legal_actions))
        # 合法手の中からランダムで一つ選択
        # bit→文字列→listでindexが逆順なので逆順のrangeを取得
        action = int(np.random.choice(range(CELLS_COUNT - 1,-1,-1),1,p=legal_actions)[0])
        # ビットに変換
        return 1 << action
    else:
        return 0

   
    
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
        print(('白' if state.is_black_turn else '黒') + 'のターン')
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
