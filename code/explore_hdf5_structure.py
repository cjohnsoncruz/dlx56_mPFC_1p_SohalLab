import h5py
from pathlib import Path

# Path to one of your dataset files
source_dataset_location = Path(r"C:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\data\dataset_objects_24-Nov-2024_hour_19")
test_file = list(source_dataset_location.glob("*_dataset_object.mat"))[0]

print(f"Exploring: {test_file.name}\n")

def explore_hdf5_structure(obj, prefix=""):
    """Recursively explore HDF5 structure"""
    if isinstance(obj, h5py.Group):
        print(f"{prefix}GROUP: {obj.name}")
        for key in obj.keys():
            print(f"{prefix}  - {key}")
            explore_hdf5_structure(obj[key], prefix + "    ")
    elif isinstance(obj, h5py.Dataset):
        print(f"{prefix}DATASET: {obj.name}, shape: {obj.shape}, dtype: {obj.dtype}")

with h5py.File(test_file, 'r') as f:
    print("Top-level keys:", list(f.keys()))
    print("\n" + "="*60)

    # Explore #refs# group
    if '#refs#' in f:
        print("\nExploring #refs# group:")
        print("-" * 60)
        refs = f['#refs#']
        for key in refs.keys():
            if isinstance(refs[key], h5py.Dataset):
                print(f"  {key}: shape={refs[key].shape}, dtype={refs[key].dtype}")
            else:
                print(f"  {key}: {type(refs[key])}")

        # Check specifically for 'C' field
        print("\n" + "="*60)
        if 'C' in refs:
            print(f"\n✓ Found 'C' field!")
            c_data = refs['C']
            print(f"  Shape: {c_data.shape}")
            print(f"  Dtype: {c_data.dtype}")
            print(f"  First few values: {c_data[:5] if len(c_data) > 5 else c_data[:]}")
        else:
            print("\n✗ 'C' field not found in #refs# group")
            print("\nAll available keys in #refs#:")
            for key in sorted(refs.keys()):
                if isinstance(refs[key], h5py.Dataset):
                    print(f"  {key}: shape={refs[key].shape}")

        # Also check for lowercase 'c'
        if 'c' in refs:
            print(f"\n✓ Found lowercase 'c' field!")
            c_data = refs['c']
            print(f"  Shape: {c_data.shape}")
            print(f"  Dtype: {c_data.dtype}")

        # Compare with raster shape
        if 'i' in refs:
            raster = refs['i']
            print(f"\nRaster ('i') shape: {raster.shape}")
            print(f"Raster transposed would be: ({raster.shape[1]}, {raster.shape[0]})")
