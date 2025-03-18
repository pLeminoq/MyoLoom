import os

import matplotlib as mlp
import numpy as np
import pandas as pd

_dir = os.path.dirname(__file__)
dir_res = os.path.join(_dir, "res")

colormaps = {}

mpl_colormap_names = ['viridis', 'plasma', 'inferno', 'magma', 'cividis']
for name in mpl_colormap_names:
    cm = mlp.colormaps[name]
    cm = np.array(cm.colors) * 255
    cm = cm.astype(np.uint8)
    colormaps[name] = cm

colormap_files = [os.path.join(dir_res, f) for f in os.listdir(dir_res) if f.endswith(".cm")]
for f in os.listdir(dir_res):
    cm = pd.read_csv(os.path.join(dir_res, f))
    cm = cm[["r", "g", "b"]]
    cm = cm.values.astype(np.uint8)

    name = os.path.basename(f).split(".")[0]
    colormaps[name] = cm


__all__ = ["colormaps"]
