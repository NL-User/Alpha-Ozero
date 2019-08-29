import random
import math

class State:
    def __init__(self, black_board=None, white_board=None, depth = 0, turn = False):
        # 連続パスによる終了
        self.pass_end = False
        # ターン数の保存
        self.depth = depth
        # ターン（Falseが黒、Trueが白）の保存
        self.turn = turn
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
        return bin(board).count("1")
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
        state = State(self.black_board, self.white_board, self.depth + 1, not self.turn)
        # print_board(state.legal_actions())
        if action != 0x0000000000000000:
            state.is_legal_action_site(action, True)
            if state.depth != 59 and state.turn:
                state = State(state.white_board, state.black_board, state.depth, not self.turn)
        else:
            state = State(state.white_board, state.black_board, state.depth - 1)

        # 2回連続パス判定
        if action == 0x0000000000000000 and state.legal_actions() == 0x0000000000000000:
            state.pass_end = True
        return state
    # 合法手が立ったビットを取得
    def legal_actions(self):
        blank = ~(self.white_board | self.black_board)
        h = self.black_board & 0x7e7e7e7e7e7e7e7e
        v = self.black_board & 0x00ffffffffffff00
        a = self.black_board & 0x007e7e7e7e7e7e00

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

        legal = legal_l(self.white_board, h, blank, 1)
        legal |= legal_l(self.white_board, v, blank, 8)
        legal |= legal_l(self.white_board, a, blank, 7)
        legal |= legal_l(self.white_board, a, blank, 9)
        legal |= legal_r(self.white_board, h, blank, 1)
        legal |= legal_r(self.white_board, v, blank, 8)
        legal |= legal_r(self.white_board, a, blank, 7)
        legal |= legal_r(self.white_board, a, blank, 9)
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
            blank_h = ~(self.white_board | self.black_board & 0x7e7e7e7e7e7e7e7e)
            blank_v = ~(self.white_board | self.black_board & 0x00ffffffffffff00)
            blank_a = ~(self.white_board | self.black_board & 0x007e7e7e7e7e7e00)
            rev = self.reversed_l(self.white_board, blank_h, site, 1)
            rev |= self.reversed_l(self.white_board, blank_v, site, 8)
            rev |= self.reversed_l(self.white_board, blank_a, site, 7)
            rev |= self.reversed_l(self.white_board, blank_a, site, 9)
            rev |= self.reversed_r(self.white_board, blank_h, site, 1)
            rev |= self.reversed_r(self.white_board, blank_v, site, 8)
            rev |= self.reversed_r(self.white_board, blank_a, site, 7)
            rev |= self.reversed_r(self.white_board, blank_a, site, 9)
            
            if flip:
                self.white_board ^= (rev ^ site)
                self.black_board ^= rev
            else:
                # 任意のマスに置くと裏返るマスのフラグが立ったビットを取得
                return rev
    # 先手かどうか
    def is_first_player(self):
        return self.depth%2 == 0
    # 文字列表示
    def __str__(self):
        ox = ('●', '○') if self.is_first_player() else ('○', '●')
        
        blank = self.white_board | self.black_board
        board = str(int(convert_to_binary(blank)) + int(convert_to_binary(self.white_board))).zfill(64)
        board = split_board(board)
        result = ''
        for st in board:
            for s in st:
                if s == '1':
                    result += ox[1]
                            
                elif s == '2':
                    result += ox[0]
                else:
                    result += 'ー'
                result += '  '
            else:
                result += '\n'
        return result

# 文字列を8文字ずつに区切る
def split_board(text):
    return [ text[i*8:i*8+8] for i in range(int(len(text)/8)) ]
def convert_to_binary(board):
    if board < 0:
        board = format(board & 0xffffffffffffffff, '#066b')
    else:
        board = format(board, '#066b')
    return board[2:]   

def split_board(text):
    return [ text[i*8:i*8+8] for i in range(int(len(text)/8)) ]

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
    
# ランダムで行動選択
def random_action(state):
    legal_actions = state.legal_actions()
    # 合法手の数を取得
    legal_action_num = bin(legal_actions).count("1")
    # 合法手が一つ以上あったら
    if legal_action_num != 0:
        # 合法手の中からランダムで一つ選択
        action = random.randint(1,legal_action_num)
        # 何番目の合法手か数える
        flag_count = 0
        for i in range(1,65):
            # ビットが立っていたら数える
            if (legal_actions & (1 << i)):
                flag_count += 1
                # 選択したビット以外は
                if flag_count != action:
                    # ビットを降ろす
                    legal_actions &= ~(1 << i)
    return legal_actions

   
    
# 動作確認
if __name__ == '__main__':
    # 状態の生成
    state = State()
    print(state)
    # ゲーム終了までのループ
    while True:
        # ゲーム終了時
        if state.is_done():
            break

        # 次の状態の取得
        state = state.next(random_action(state))

        # 文字列表示
        print(state)
        print()
    print("黒:{0} 白:{1}".format(state.piece_count(state.black_board), state.piece_count(state.white_board)))
    result = ''
    if state.is_draw():
        result = "引き分け"
    elif state.is_lose():
        result = "白の勝ち"
    else:
        result = "黒の勝ち"
        
    print(result)
