"""POD-NN modeling for 1D, unsteady Burger Equation."""
#%% Imports
import sys
import os
import pickle
import numpy as np

sys.path.append(os.path.join("..", ".."))
from podnn.podnnmodel import PodnnModel
from podnn.mesh import read_multi_space_sol_input_mesh
from podnn.handling import clean_dir, split_dataset

from hyperparams import HP as hp

resdir = "cache"
clean_dir(resdir)

# Getting data from the files
fake_x = np.zeros(hp["n_s"] + hp["n_s_tst"])
test_size = hp["n_s_tst"] / (hp["n_s"] + hp["n_s_tst"])
train_tst_idx = split_dataset(fake_x, fake_x, test_size, idx_only=True)
with open(os.path.join("cache", "train_tst_idx.pkl"), "wb") as f:
     pickle.dump(train_tst_idx, f)

datadir = "data"
mu_path = os.path.join(datadir, "INPUT_MONTE_CARLO.dat")
x_mesh, connectivity, X_v, U = \
        read_multi_space_sol_input_mesh(hp["n_s"], 1, 1, train_tst_idx[0],
                                        hp["mesh_idx"], datadir, mu_path,
                                        hp["mu_idx"])

np.save(os.path.join("cache", "x_mesh.npy"), x_mesh)
# x_mesh = np.load(os.path.join("cache", "x_mesh.npy"))
# u_mesh = None
# X_v = None

#%% Init the model
model = PodnnModel(resdir, hp["n_v"], x_mesh, hp["n_t"])

#%% Generate the dataset from the mesh and params
X_v_train, v_train, \
    X_v_val, v_val, \
    U_val = model.convert_multigpu_data(U, X_v, hp["train_val"], hp["eps"])


model.initVNNs(hp["n_M"], hp["h_layers"],
                hp["lr"], hp["lambda"], hp["adv_eps"], hp["norm"])