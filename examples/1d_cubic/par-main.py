"""POD-NN modeling for 1D Shekel Equation."""

import sys
import os
import yaml
import numpy as np
import tensorflow as tf
tf.get_logger().setLevel('WARNING')
tf.autograph.set_verbosity(1)

import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

sys.path.append(os.path.join("..", ".."))
from podnn.podnnmodel import PodnnModel
from podnn.mesh import create_linear_mesh
from podnn.plotting import genresultdir

from podnn.varneuralnetwork import VarNeuralNetwork
from podnn.metrics import re_mean_std, re_max
from podnn.mesh import create_linear_mesh
from podnn.logger import Logger
from podnn.advneuralnetwork import NORM_MEANSTD, NORM_NONE
from podnn.plotting import figsize

# Datagen
N_star = 100
# D = 1
x_star = np.linspace(-6, 6, N_star).reshape((N_star, 1))
# u_star = x_star**3
D = 2
u1_star = np.cos(x_star)
u2_star = np.sin(x_star)
u_star = np.column_stack((u1_star[:, 0], u2_star[:, 0]))

N = 20
lb = int(2/(2*6) * N_star)
ub = int((2+2*4)/(2*6) * N_star)
idx = np.random.choice(x_star[lb:ub].shape[0], N, replace=False)
x_train = x_star[lb + idx]
u_train = u_star[lb + idx]
noise_std = 0.01*u_train.std(0)
# noise_std = 3
u_train = u_train + noise_std*np.random.randn(u_train.shape[0], u_train.shape[1])

# Model creation
def gen_and_train_model():
    layers = [1, 50, 50, D]
    epochs = 20000
    lr = 0.0001
    model = VarNeuralNetwork(layers, lr, 1e-10,
                             norm=NORM_MEANSTD, norm_bounds=(x_train.mean(), x_train.std()))
    logger = Logger(epochs, 5000, silent=True)
    logger.set_val_err_fn(lambda _: {})

    # Training
    model.fit(x_train, u_train, epochs, logger)

    # Make the prediction on the meshed x-axis (ask for MSE as well)
    return model.predict(x_star)

tf.debugging.set_log_device_placement(True)
gpus = tf.config.experimental.list_logical_devices('GPU')
M = len(gpus)
print(M)
u_pred_samples = []
u_pred_var_samples = []

layers = [1, 50, 50, D]
epochs = 20000
lr = 0.0001
dtype = "float64"
tf.keras.backend.set_floatx(dtype)

for gpu in gpus:
    with tf.device(gpu.name):

        # Model
        inputs = tf.keras.Input(shape=(layers[0],), name="x", dtype=dtype)
        x = inputs
        for width in layers[1:-1]:
            x = tf.keras.layers.Dense(
                    width, activation=tf.nn.relu, dtype=dtype,
                    kernel_initializer="glorot_normal")(x)
        x = tf.keras.layers.Dense(
                2 * layers[-1], activation=None, dtype=dtype,
                kernel_initializer="glorot_normal")(x)
        def split_mean_var(data):
            mean, out_var = tf.split(data, num_or_size_splits=2, axis=1)
            var = tf.math.softplus(out_var) + 1e-6
            return [mean, var]
        outputs = tf.keras.layers.Lambda(split_mean_var)(x)
        model = tf.keras.Model(inputs=inputs, outputs=outputs, name="varnn")
        def loss(y, y_pred):
            """Return the Gaussian NLL loss function between the pred and val."""
            y_pred_mean, y_pred_var = y_pred
            return tf.reduce_mean(tf.math.log(y_pred_var) / 2) + \
                tf.reduce_mean(tf.divide(tf.square(y -  y_pred_mean), 2*y_pred_var))
        model.compile(optimizer=tf.keras.optimizers.Adam(lr), loss=loss)

        x = tf.convert_to_tensor(x_train, dtype=dtype) 
        y = tf.convert_to_tensor(u_train, dtype=dtype)
        model.fit(x, y, epochs=epochs, verbose=0)
        mean, var = model.predict(tf.convert_to_tensor(x_star))
        u_pred_samples.append(mean)
        u_pred_var_samples.append(var)

u_pred = u_pred_var_samples.mean(-1)
u_pred_var = (np.array(u_pred_var_samples) + np.array(u_pred_samples ** 2)).mean(-1) - u_pred ** 2
lower = u_pred - 3 * np.sqrt(u_pred_var)
upper = u_pred + 3 * np.sqrt(u_pred_var)
print(u_pred.shape, u_pred_var.shape)

fig = plt.figure(figsize=figsize(1, 1, scale=2.5))
plt.fill_between(x_star[:, 0], lower[:, 0], upper[:, 0], 
                    facecolor='C0', alpha=0.3, label=r"$3\sigma_{T}(x)$")
# plt.plot(x_star, u_pred_samples[:, :, 0].numpy().T, 'C0', linewidth=.5)
plt.scatter(x_train, u_train[:, 0], c="r", label=r"$u_T(x)$")
plt.plot(x_star, u_star[:, 0], "r--", label=r"$u_*(x)$")
plt.plot(x_star, u_pred[:, 0], label=r"$\hat{u}_*(x)$")
plt.legend()
plt.xlabel("$x$")
# plt.savefig("results/gp.pdf")
plt.savefig("results/cos.pdf")
fig = plt.figure(figsize=figsize(1, 1, scale=2.5))
plt.fill_between(x_star[:, 0], lower[:, 1], upper[:, 1], 
                    facecolor='orange', alpha=0.5, label=r"$2\sigma_{T,hf}(x)$")
plt.plot(x_star, u_star[:, 1])
plt.plot(x_star, u_pred[:, 1], "r--")
plt.scatter(x_train, u_train[:, 1],)
plt.savefig("results/sin.pdf")