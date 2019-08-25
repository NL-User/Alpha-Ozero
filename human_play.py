# ====================
# 人とAIの対戦
# ====================

# パッケージのインポート
from game import State
from pv_mcts import pv_mcts_action
from tensorflow.keras.models import load_model
from pathlib import Path
from threading import Thread
import tkinter as tk

# ベストプレイヤーのモデルの読み込み
model = load_model('./model/best.h5')

# ゲームUIの定義
class GameUI(tk.Frame):
    # 初期化
    def __init__(self, master=None, model=None):
        tk.Frame.__init__(self, master)
        self.master.title('リバーシ')

        # ゲーム状態の生成
        self.state = State()

        # PV MCTSで行動選択を行う関数の生成
        self.next_action = pv_mcts_action(model, 0.0)

        # キャンバスの生成
        self.c = tk.Canvas(self, width = 320, height = 320, highlightthickness = 0)
        self.c.bind('<Button-1>', self.turn_of_human)
        self.c.pack()

        # 描画の更新
        self.on_draw()

    # 人間のターン
    def turn_of_human(self, event):
        # ゲーム終了時
        if self.state.is_done():
            self.state = State()
            self.on_draw()
            return

        # 先手でない時
        if not self.state.is_first_player():
            return

        # クリック位置を行動に変換
        x = int(event.x/40)
        y = int(event.y/40)
        if x < 0 or 7 < x or y < 0 or 7 < y: # 範囲外
            return
        action = x + y * 8

        # 合法手でない時
        legal_actions = self.state.legal_actions()
        if legal_actions == [64]:
            action = 64 # パス
        if action != 64 and not (action in legal_actions):
            return

        # 次の状態の取得
        self.state = self.state.next(action)
        self.on_draw()

        # AIのターン
        self.master.after(1, self.turn_of_ai)

    # AIのターン
    def turn_of_ai(self):
        # ゲーム終了時
        if self.state.is_done():
            return

        # 行動の取得
        action = self.next_action(self.state)

        # 次の状態の取得
        self.state = self.state.next(action)
        self.on_draw()

    # 石の描画
    def draw_piece(self, index, first_player):
        x = (index%8)*40+5
        y = int(index/8)*40+5
        if first_player:
            self.c.create_oval(x, y, x+30, y+30, width = 1.0, outline = '#000000', fill = '#C2272D')
        else:
            self.c.create_oval(x, y, x+30, y+30, width = 1.0, outline = '#000000', fill = '#FFFFFF')

    # 描画の更新
    def on_draw(self):
        self.c.delete('all')
        self.c.create_rectangle(0, 0, 320, 320, width = 0.0, fill = '#C69C6C')
        for i in range(1, 9):
            self.c.create_line(0, i*40, 320, i*40, width = 1.0, fill = '#000000')
            self.c.create_line(i*40, 0, i*40, 320, width = 1.0, fill = '#000000')
        for i in range(64):
            if self.state.pieces[i] == 1:
                self.draw_piece(i, self.state.is_first_player())
            if self.state.enemy_pieces[i] == 1:
                self.draw_piece(i, not self.state.is_first_player())

# ゲームUIの実行
f = GameUI(model=model)
f.pack()
f.mainloop()