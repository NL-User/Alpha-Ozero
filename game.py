# ====================
# リバーシ
# ====================

# パッケージのインポート
import random
import math
import gmpy2

# ゲーム状態
class State:
    # 初期化
    def __init__(self, pieces=None, enemy_pieces=None, depth=0):
        # 方向定数
        self.dxy = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))

        # 連続パスによる終了
        self.pass_end = False

        # 石の配置
        self.black_board = pieces
        self.white_board = enemy_pieces
        self.depth = depth

        # 石の初期配置
        if pieces == None or enemy_pieces == None:
            self.black_board = 0x0000001008000000
            self.white_board = 0x0000000810000000

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
            state.is_legal_action_xy(action%8, int(action/8), True)
        w = state.black_board
        state.black_board = state.white_board
        state.white_board = w

        # 2回連続パス判定
        if action == 64 and state.legal_actions() == [64]:
            state.pass_end = True
        return state

    # 合法手のリストの取得
    def legal_actions(self):
        actions = []
        for j in range(0,8):
            for i in range(0,8):
                if self.is_legal_action_xy(i, j):
                    actions.append(i+j*8)
        if len(actions) == 0:
            actions.append(64) # パス
        return actions

    # 任意のマスが合法手かどうか
    def is_legal_action_xy(self, x, y, flip=False):
        # 任意のマスの任意の方向が合法手かどうか
        def is_legal_action_xy_dxy(x, y, dx, dy):
            # １つ目 相手の石
            x, y = x+dx, y+dy
            if y < 0 or 7 < y or x < 0 or 7 < x or \
                self.white_board[x+y*8] != 1:
                return False

            # 2つ目以降
            for j in range(8):
                # 空
                if y < 0 or 7 < y or x < 0 or 7 < x or \
                    (self.white_board[x+y*8] == 0 and self.black_board[x+y*8] == 0):
                    return False

                # 自分の石
                if self.black_board[x+y*8] == 1:
                    # 反転
                    if flip:
                        for i in range(8):
                            x, y = x-dx, y-dy
                            if self.black_board[x+y*8] == 1:
                                return True
                            self.black_board[x+y*8] = 1
                            self.white_board[x+y*8] = 0
                    return True
                # 相手の石
                x, y = x+dx, y+dy
            return False

        # 空きなし
        if self.white_board[x+y*8] == 1 or self.black_board[x+y*8] == 1:
            return False

        # 石を置く
        if flip:
            self.black_board[x+y*8] = 1

        # 任意の位置が合法手かどうか
        flag = False
        for dx, dy in self.dxy:
            if is_legal_action_xy_dxy(x, y, dx, dy):
                flag = True
        return flag

    # 先手かどうか
    def is_first_player(self):
        return self.depth%2 == 0

    # 文字列表示
    def __str__(self):
        ox = ('●', '○') if self.is_first_player() else ('○', '●')
        str = ''
        for i in range(64):
            str += '  '
            if self.black_board[i] == 1:
                str += ox[0]
            elif self.white_board[i] == 1:
                str += ox[1]
            else:
                str += 'ー'
            if i % 8 == 7:
                str += '\n'
        return str

# ランダムで行動選択
def random_action(state):
    legal_actions = state.legal_actions()
    return legal_actions[random.randint(0, len(legal_actions)-1)]

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