
import importlib, sys
pkgs = [
    "numpy","pandas","matplotlib","seaborn","scipy","statsmodels","pingouin",
    "openpyxl","h5py","mat73","scikit_learn","joblib","tqdm","optuna",
    "torch","torchvision","jupyter","nbclient","nbformat","ipykernel","tornado","zmq",
]
for name in pkgs:
    try:
        mod = importlib.import_module(name if name != "scikit_learn" else "sklearn")
        ver = getattr(mod, "__version__", "unknown")
        print(f"{name}=={ver}")
    except Exception as e:
        print(f"{name} (not installed) - {e.__class__.__name__}: {e}")