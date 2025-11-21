"""
Code to help find the 'C' field in your HDF5 MATLAB files.
Run this in your Jupyter notebook where h5py is already available.
"""

# Add this cell to your notebook:

import h5py
from pathlib import Path

# Use the same source location
source_dataset_location = Path(r"C:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\data\dataset_objects_24-Nov-2024_hour_19")
test_file = list(source_dataset_location.glob("*_dataset_object.mat"))[0]

print(f"Exploring: {test_file.name}\n")
print("="*70)

with h5py.File(test_file, 'r') as f:
    # Check top-level keys
    print("Top-level keys:", list(f.keys()))

    # Explore #refs# group
    if '#refs#' in f:
        refs = f['#refs#']
        print(f"\nAll keys in #refs# group ({len(refs.keys())} total):")
        print("-"*70)

        # List all datasets with their shapes
        for key in sorted(refs.keys()):
            if isinstance(refs[key], h5py.Dataset):
                print(f"  '{key}': shape={refs[key].shape}, dtype={refs[key].dtype}")
            elif isinstance(refs[key], h5py.Group):
                print(f"  '{key}': [GROUP]")

        # Check for 'C' field (uppercase)
        print("\n" + "="*70)
        if 'C' in refs:
            print(f"✓ Found 'C' field (uppercase)!")
            c_data = refs['C']
            print(f"  Shape: {c_data.shape}")
            print(f"  Dtype: {c_data.dtype}")

            # Compare with raster
            if 'i' in refs:
                raster = refs['i']
                print(f"\n  Raster ('i') shape: {raster.shape}")
                print(f"  C shape: {c_data.shape}")
                print(f"  Match? {c_data.shape == raster.shape or c_data.shape == raster.T.shape}")

        # Check for 'c' field (lowercase)
        elif 'c' in refs:
            print(f"✓ Found 'c' field (lowercase)!")
            c_data = refs['c']
            print(f"  Shape: {c_data.shape}")
            print(f"  Dtype: {c_data.dtype}")

            # Compare with raster
            if 'i' in refs:
                raster = refs['i']
                print(f"\n  Raster ('i') shape: {raster.shape}")
                print(f"  c shape: {c_data.shape}")
                print(f"  Match? {c_data.shape == raster.shape or c_data.shape == raster.T.shape}")
        else:
            print("✗ Neither 'C' nor 'c' found in #refs# group")
            print("\nSearching for fields with similar shape to raster...")

            if 'i' in refs:
                raster_shape = refs['i'].shape
                print(f"  Raster shape: {raster_shape}")
                print(f"  Raster transposed: ({raster_shape[1]}, {raster_shape[0]})")

                print("\n  Fields with matching dimensions:")
                for key in sorted(refs.keys()):
                    if isinstance(refs[key], h5py.Dataset):
                        if (refs[key].shape == raster_shape or
                            refs[key].shape == (raster_shape[1], raster_shape[0])):
                            print(f"    '{key}': shape={refs[key].shape}")
