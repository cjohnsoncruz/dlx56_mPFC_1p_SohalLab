import os
from pathlib import Path

# Corrupted file names
corrupted_files = [
    "13_8_HET_RS3_dataset_object.mat",
    "9_3_HET_RS2_dataset_object.mat", 
    "9_3_HET_RS3_dataset_object.mat"
]

source_dataset_location = Path(r"C:\Users\13car\Dropbox\UCSF\vikaas\Ruleshifting task notes\dlx mice notes\All datasets- Padded Labels, raster, EXTRACT outputs\dataset_objects")

print("="*70)
print("INVESTIGATING CORRUPTED FILES")
print("="*70)

for fname in corrupted_files:
    filepath = source_dataset_location / fname
    
    print(f"\n📁 {fname}")
    print("-" * 70)
    
    if not filepath.exists():
        print("  ❌ File does not exist!")
        continue
    
    # Check file size
    size_bytes = filepath.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024
    
    print(f"  Size: {size_bytes:,} bytes ({size_mb:.2f} MB)")
    
    # Read first bytes to check file signature
    with open(filepath, 'rb') as f:
        header = f.read(100)
        
    # Check for MATLAB file signatures
    print(f"  First 20 bytes (hex): {header[:20].hex()}")
    print(f"  First 20 bytes (text): {header[:20]}")
    
    # HDF5 files should start with \x89HDF\r\n\x1a\n
    if header[:4] == b'\x89HDF':
        print("  ✓ Valid HDF5 signature")
    elif header[:4] == b'MATL':
        print("  ⚠️ Old MATLAB format (v5/v6) - needs scipy.io")
    else:
        print("  ❌ Unknown file signature - file may be corrupted")
    
    # Try to detect if file is truncated
    if size_mb < 1:
        print(f"  ⚠️ WARNING: File is unusually small ({size_mb:.2f} MB)")

# Compare with a working file
print("\n" + "="*70)
print("COMPARISON WITH A WORKING FILE")
print("="*70)

working_file = source_dataset_location / "10_3_HET_RS1_dataset_object.mat"
if working_file.exists():
    size_bytes = working_file.stat().st_size
    size_mb = size_bytes / 1024 / 1024
    print(f"\n📁 10_3_HET_RS1_dataset_object.mat (working)")
    print(f"  Size: {size_mb:.2f} MB")
    
    with open(working_file, 'rb') as f:
        header = f.read(20)
    print(f"  First 20 bytes (hex): {header.hex()}")
    print(f"  Signature: {'HDF5' if header[:4] == b'\\x89HDF' else 'Other'}")
