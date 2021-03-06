"""Various utilities functions."""

import os
import argparse
import numpy as np

from .acceleration import lhs

MODEL_NAME = "model_weights"


def pack_layers(i, hiddens, o):
    """Create the full NN topology from input size, hidden layers, and output."""
    layers = []
    layers.append(i)
    for h in hiddens:
        layers.append(h)
    layers.append(o)
    return layers


def scarcify(X, u, N):
    """Randomly split a dataset into train-val subsets."""
    idx = np.random.choice(X.shape[0], N, replace=False)
    mask = np.ones(X.shape[0], bool)
    mask[idx] = False
    return X[idx, :], u[idx, :], X[mask, :], u[mask, :]


def split_dataset(X_v, v, test_size, idx_only=False):
    """Randomly splitting the dataset (X_v, v)."""
    indices = np.random.permutation(X_v.shape[0])
    limit = np.floor(X_v.shape[0] * (1. - test_size)).astype(int)
    if idx_only:
        return indices[:limit].tolist(), indices[limit:].tolist()
    train_idx, tst_idx = indices[:limit], indices[limit:]
    return X_v[train_idx], X_v[tst_idx], v[train_idx], v[tst_idx]


def sample_mu(n_s, mu_min, mu_max, indices=None):
    """Return a LHS sampling between mu_min and mu_max of size n_s."""
    if indices is not None:
        mu = np.linspace(mu_min, mu_max, n_s)[indices]
        return mu
    X_lhs = lhs(n_s, mu_min.shape[0]).T
    mu_lhs = mu_min + (mu_max - mu_min)*X_lhs
    return mu_lhs


def check_distributed_args():
    pa = argparse.ArgumentParser()
    pa.add_argument("--distributed", action="store_true", default=False)
    args = pa.parse_args()
    return args.distributed


def clean_dir(dirname):
    for root, dirs, files in os.walk(dirname):
        for name in files:
            if name.startswith(MODEL_NAME):
                os.remove(os.path.join(root, name))


def clean_models(dirname):
    for root, dirs, files in os.walk(dirname):
        for name in files:
            if name.startswith("model-"):
                os.remove(os.path.join(root, name))
