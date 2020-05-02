# coding: utf-8

# ====================
# デュアルネットワークの作成
# ====================

# パッケージのインポート
from config import *
from tensorflow.keras.layers import Activation, Add, BatchNormalization, Conv2D, Dense, GlobalAveragePooling2D, Input, Reshape
from tensorflow.keras.models import Model
from tensorflow.keras.regularizers import l2
from tensorflow.keras import backend as K
import os
from config import BOARD_X_SIZE, BOARD_Y_SIZE

# パラメータの準備
DN_INPUT_SHAPE = (BOARD_Y_SIZE, BOARD_X_SIZE, 2)
DN_FILTERS  = 128 # 畳み込み層のカーネル数（本家は256）
DN_RESIDUAL_NUM =  max(BOARD_X_SIZE, BOARD_Y_SIZE) # 残差ブロックの数（本家は19）
L2_NORM = 0.001

# 畳み込み層の作成
def conv(filters):
    return Conv2D(filters, 3, padding='same', use_bias=False,
        kernel_initializer='zeros', kernel_regularizer=l2(L2_NORM))

# 残差ブロックの作成
def residual_block():
    def f(x):
        sc = x
        x = conv(DN_FILTERS)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = conv(DN_FILTERS)(x)
        x = BatchNormalization()(x)
        x = Add()([x, sc])
        x = Activation('relu')(x)
        return x
    return f

# デュアルネットワークの作成
def dual_network():
    # # モデル作成済みの場合は無処理
    # if os.path.exists('./model/best.h5'):
    #     return

    # 入力層
    board = Input(shape=DN_INPUT_SHAPE)
    # convが3次元じゃないといけないので変換
    # board = Reshape((BOARD_Y_SIZE, BOARD_X_SIZE, 1, 1), input_shape = (BOARD_Y_SIZE, BOARD_X_SIZE))(board)
    turn = Input(shape=(1))
    inputs = [board,turn]
    # 畳み込み層
    x = conv(DN_FILTERS)(board)
    # x = conv(DN_FILTERS)(inputs)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    # 残差ブロック x 16
    for _ in range(DN_RESIDUAL_NUM):
        x = residual_block()(x)

    # プーリング層
    x = GlobalAveragePooling2D()(x)

    # 追加
    x = Add()([x, turn])

    # ポリシー出力
    p = Dense(CELLS_COUNT + 1, kernel_regularizer=l2(L2_NORM),
                activation='softmax', name='pi')(x)

    # バリュー出力
    v = Dense(1, kernel_regularizer=l2(L2_NORM))(x)
    v = Activation('tanh', name='v')(v)

    # モデルの作成
    model = Model(inputs=inputs, outputs=[p,v])

    # モデルの保存
    os.makedirs('./model/', exist_ok=True) # フォルダがない時は生成
    model.save('./model/init.h5') # ベストプレイヤーのモデル

    # モデルの破棄
    K.clear_session()
    del model

# 動作確認
if __name__ == '__main__':
    dual_network()
