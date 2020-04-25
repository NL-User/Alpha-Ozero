# ====================
# パラメータ更新部
# ====================

# パッケージのインポート
from dual_network import DN_INPUT_SHAPE
from tensorflow.keras.callbacks import LearningRateScheduler, LambdaCallback
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
import numpy as np
import pickle
from glob import glob
import platform

# パラメータの準備
RN_EPOCHS = 100 # 学習回数

# 学習データの読み込み
def load_data():
    history_path = sorted(glob('./data/*.history'))[-1]
    with open(history_path, mode='rb') as f:
        return pickle.load(f)

# デュアルネットワークの学習
def train_network():
    # 学習データの読み込み
    history = load_data()
    xs, turn_nums, y_policies, y_values = zip(*history)

    # 学習のための入力データのシェイプの変換
    a, b, c = DN_INPUT_SHAPE
    xs = np.array(xs)
    xs = xs.reshape(len(xs), c, a, b).transpose(0, 2, 3, 1)
    turn_nums = np.array(turn_nums)
    y_policies = np.array(y_policies)
    y_values = np.array(y_values)

    # 最新モデルの読み込み
    model = load_model(sorted(glob('./model/*.h5'))[-1])

    # モデルのコンパイル
    model.compile(loss=['categorical_crossentropy', 'huber_loss'], optimizer='adam')

    # 学習率
    def step_decay(epoch):
        x = 0.001
        if epoch >= 50: x = 0.0005
        if epoch >= 80: x = 0.00025
        return x
    lr_decay = LearningRateScheduler(step_decay)

    # 出力
    print_callback = LambdaCallback(
        on_epoch_begin=lambda epoch,logs:
                print('\rTrain {}/{}'.format(epoch + 1,RN_EPOCHS), end=''))

    # 学習の実行
    model.fit([xs, turn_nums], [y_policies, y_values], batch_size=128, epochs=RN_EPOCHS,
            verbose=0, callbacks=[lr_decay, print_callback])
    print('')

    save_path = './model/latest' + str(len(glob('./model/latest*.h5')) + 1) + '.h5'
    # 最新プレイヤーのモデルの保存
    model.save(save_path)

    # モデルの破棄
    K.clear_session()
    del model

# 動作確認
if __name__ == '__main__':
    train_network()
