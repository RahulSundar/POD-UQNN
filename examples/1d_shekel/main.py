"""POD-NN modeling for 1D Shekel Equation."""

import sys
import os
import yaml
import numpy as np

sys.path.append(os.path.join("..", ".."))
from podnn.podnnmodel import PodnnModel
from podnn.metrics import error_podnn_rel
from podnn.mesh import create_linear_mesh

from datagen import u, generate_test_dataset
from plots import plot_results


def main(hp, gen_test=False, use_cached_dataset=False,
         no_plot=False):
    """Full example to run POD-NN on 1d_shekel."""

    if gen_test:
        generate_test_dataset()

    if not use_cached_dataset:
        # Create linear space mesh
        x_mesh = create_linear_mesh(hp["x_min"], hp["x_max"], hp["n_x"])
        np.save(os.path.join("cache", "x_mesh.npy"), x_mesh)
    else:
        x_mesh = np.load(os.path.join("cache", "x_mesh.npy"))

    # Init the model
    model = PodnnModel("cache", hp["n_v"], x_mesh, hp["n_t"])

    # Generate the dataset from the mesh and params
    X_v_train, v_train, \
        X_v_test, _, \
        U_test = model.generate_dataset(u, hp["mu_min"], hp["mu_max"],
                                       hp["n_s"],
                                       hp["train_val_test"],
                                       hp["eps"],
                                       use_cache=use_cached_dataset)

    train_res = model.train(X_v_train, v_train, hp["h_layers"],
                            hp["epochs"], hp["lr"], hp["lambda"],
                            frequency=hp["log_frequency"])

    # Predict and restruct
    U_pred = model.predict(X_v_test)

    # Compute relative error
    error_test_mean, error_test_std = error_podnn_rel(U_test, U_pred)
    print(f"Test relative error: mean {error_test_mean:4f}, std {error_test_std:4f}")

    # Sample the new model to generate a HiFi prediction
    print("Sampling {n_s_hifi} parameters...")
    X_v_test_hifi = model.generate_hifi_inputs(hp["n_s_hifi"], hp["mu_min"], hp["mu_max"])
    print("Predicting the {n_s_hifi} corresponding solutions...")
    U_pred_hifi_mean, U_pred_hifi_std = model.predict_heavy(X_v_test_hifi)
    U_pred_hifi_mean = U_pred_hifi_mean.reshape((hp["n_x"],))
    U_pred_hifi_std = U_pred_hifi_std.reshape((hp["n_x"],))

    # Plot against test and save
    return plot_results(U_test, U_pred, U_pred_hifi_mean, U_pred_hifi_std,
                        train_res, hp, no_plot)


if __name__ == "__main__":
    # Custom hyperparameters as command-line arg
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as HPFile:
            HP = yaml.load(HPFile)
    # Default ones
    else:
        from hyperparams import HP

    main(HP, gen_test=False, use_cached_dataset=False)
    # main(HP, gen_test=False, use_cached_dataset=True)
