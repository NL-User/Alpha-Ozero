import random
import math
import gmpy2

class State:
    def __init__(self, black_board=None, white_board=None, depth=0):
        # 連続パスによる終了
        self.pass_end = False
        # ターン数の保存
        self.depth = depth
        if black_board == None or white_board == None:
            # 石の初期配置
            self.black_board = 0x0000001008000000
            self.white_board = 0x0000000810000000
        else:
            # 石の配置
            self.black_board = black_board
            self.white_board = white_board
            
    # 石の数の取得
    def piece_count(self, board):
        return gmpy2.popcount(black_board)
    # 負けかどうか
    def is_lose(self):
        return self.is_done() and self.piece_count(self.black_board) < self.piece_count(self.white_board)

    # 引き分けかどうか
    def is_draw(self):
        return self.is_done() and self.piece_count(self.black_board) == self.piece_count(self.white_board)

    # ゲーム終了かどうか
    def is_done(self):
        return self.piece_count(self.black_board) + self.piece_count(self.white_board) == 64 or self.pass_end
    # 次の状態の取得
    def next(self, action):
        state = State(self.black_board.copy(), self.white_board.copy(), self.depth+1)
        if action != 64:
            state.is_legal_action_site(action, True)
        w = state.black_board
        state.black_board = state.white_board
        state.white_board = w

        # 2回連続パス判定
        if action == 0x0000000000000000 and state.legal_actions() == 0x0000000000000000:
            state.pass_end = True
        return state
    # 合法手が立ったビットを取得
    def legal_actions(self):
        blank = ~(self.black_board | self.white_board)
        h = self.white_board & 0x7e7e7e7e7e7e7e7e
        v = self.white_board & 0x00ffffffffffff00
        a = self.white_board & 0x007e7e7e7e7e7e00

        def legal_r(board, masked, blank, dir):
            """Direction >> dir exploring."""
            tmp = masked & (board >> dir)
            tmp |= masked & (tmp >> dir)
            tmp |= masked & (tmp >> dir)
            tmp |= masked & (tmp >> dir)
            tmp |= masked & (tmp >> dir)
            tmp |= masked & (tmp >> dir)
            legal = blank & (tmp >> dir)
            return legal
        def legal_l(board, masked, blank, dir):
            """Direction << dir exploring."""
            tmp = masked & (board << dir)
            tmp |= masked & (tmp << dir)
            tmp |= masked & (tmp << dir)
            tmp |= masked & (tmp << dir)
            tmp |= masked & (tmp << dir)
            tmp |= masked & (tmp << dir)
            legal = blank & (tmp << dir)
            return legal

        legal = legal_l(self.black_board, h, blank, 1)
        legal |= legal_l(self.black_board, v, blank, 8)
        legal |= legal_l(self.black_board, a, blank, 7)
        legal |= legal_l(self.black_board, a, blank, 9)
        legal |= legal_r(self.black_board, h, blank, 1)
        legal |= legal_r(self.black_board, v, blank, 8)
        legal |= legal_r(self.black_board, a, blank, 7)
        legal |= legal_r(self.black_board, a, blank, 9)
        return legal
    # 左シフト方向
    def reversed_l(self, player, blank_masked, site, dir):
        """Direction << for self.reversed()."""
        rev = 0
        tmp = ~(player | blank_masked) & (site << dir)
        if tmp:
            for i in range(6):
                tmp <<= dir
                if tmp & blank_masked:
                    break
                elif tmp & player:
                    rev |= tmp >> dir
                    break
                else:
                    tmp |= tmp >> dir
        return rev
    # 右シフト方向
    def reversed_r(self, player, blank_masked, site, dir):
        """Direction >> for self.reversed()."""
        rev = 0
        tmp = ~(player | blank_masked) & (site >> dir)
        if tmp:
            for i in range(6):
                tmp >>= dir
                if tmp & blank_masked:
                    break
                elif tmp & player:
                    rev |= tmp << dir
                    break
                else:
                    tmp |= tmp << dir
        return rev
    def is_legal_action_site(self, site, flip=False):
            """Return reversed site board."""
            blank_h = ~(self.black_board | self.white_board & 0x7e7e7e7e7e7e7e7e)
            blank_v = ~(self.black_board | self.white_board & 0x00ffffffffffff00)
            blank_a = ~(self.black_board | self.white_board & 0x007e7e7e7e7e7e00)
            rev = self.reversed_l(self.black_board, blank_h, site, 1)
            rev |= self.reversed_l(self.black_board, blank_v, site, 8)
            rev |= self.reversed_l(self.black_board, blank_a, site, 7)
            rev |= self.reversed_l(self.black_board, blank_a, site, 9)
            rev |= self.reversed_r(self.black_board, blank_h, site, 1)
            rev |= self.reversed_r(self.black_board, blank_v, site, 8)
            rev |= self.reversed_r(self.black_board, blank_a, site, 7)
            rev |= self.reversed_r(self.black_board, blank_a, site, 9)
            
            if flip:
                # 黒と白のボード情報を返す
                return black ^ (rev ^ site), white ^ rev
            else:
                # 任意のマスに置くと裏返るマスのフラグが立ったビットを取得
                return rev
    # 先手かどうか
    def is_first_player(self):
        return self.depth%2 == 0
    # 文字列を8文字ずつに区切る
    def split_board(self, text):
        return [ text[i*8:i*8+8] for i in range(int(len(text)/8)) ]
    def convert_to_binary(board):
        if board < 0:
            board = format(board & 0xffffffffffffffff, '#066b')[2:]
        else:
            board = format(board, '#066b')[2:]
    return board
    # 文字列表示
    def __str__(self):
        ox = ('●', '○') if self.is_first_player() else ('○', '●')
        
        blank = white_board | black_board
        board = str(int(convert_to_binary(blank)) + int(convert_to_binary(self.white_board))).zfill(64)
        board = split_board(board)
        for str in board:
            result = ''
            for s in str:
                if s == '1':
                    result += ox[0] + '  '
                elif s == '2':
                    result += ox[1] + '  '
                else:
                    result += 'ー'
            else:
                result += '\n'
        return result

# ランダムで行動選択
def random_action(state):
    legal_actions =state.legal_actions()
    # action = '1'.ljust(random.randint(0,64), '0').zfill(64)
    for i,str in enumerate(legal_actions):
        
def print_board(board):
    if board < 0:
        board = format(board & 0xffffffffffffffff, '#066b')[2:]
    else:
        board = format(board, '#066b')[2:]
    board = split_board(board)
    for str in board:
        result = ""
        for s in str.format('08'):
            result += s + ' '
        print(result)
    print()


state = State()
print_board(state.legal_actions())