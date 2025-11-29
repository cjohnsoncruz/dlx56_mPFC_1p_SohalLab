"""
Test Script: Configuration and Manifest System

Run this script to verify that your configuration and manifest tracking
system is set up correctly.

Usage:
    python test_config_and_manifest.py
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

def test_imports():
    """Test that all required modules can be imported."""
    print("="*70)
    print("TEST 1: Importing Modules")
    print("="*70)

    try:
        from config_preprocessing import load_config
        print("[OK] config_preprocessing imported successfully")
    except Exception as e:
        print(f"[ERROR] Failed to import config_preprocessing: {e}")
        return False

    try:
        from run_manifest import create_run_manifest
        print("[OK] run_manifest imported successfully")
    except Exception as e:
        print(f"[ERROR] Failed to import run_manifest: {e}")
        return False

    return True


def test_config_loading():
    """Test loading and validating configuration."""
    print("\n" + "="*70)
    print("TEST 2: Loading Configuration")
    print("="*70)

    try:
        from config_preprocessing import load_config, print_config_summary

        config = load_config('config.yaml')
        print("[OK] Configuration loaded successfully")

        # Verify key sections
        required_sections = ['data', 'preprocessing', 'shuffles', 'timeseries', 'subjects']
        for section in required_sections:
            if section not in config:
                print(f"[ERROR] Missing required section: {section}")
                return False
            print(f"[OK] Section '{section}' found")

        # Verify subject count
        if len(config['subjects']) != 35:
            print(f"[WARNING] Expected 35 subjects, found {len(config['subjects'])}")
        else:
            print(f"[OK] All 35 subjects found")

        # Print summary
        print("\n" + "-"*70)
        print_config_summary(config)
        print("-"*70)

        return True

    except Exception as e:
        print(f"[ERROR] Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_helpers():
    """Test configuration helper functions."""
    print("\n" + "="*70)
    print("TEST 3: Configuration Helper Functions")
    print("="*70)

    try:
        from config_preprocessing import (
            get_subject_list,
            get_genotype,
            get_session_type,
            get_subject_metadata,
            get_n_cores,
            load_config
        )

        config = load_config('config.yaml')

        # Test get_subject_list
        subjects = get_subject_list(config)
        print(f"[OK] get_subject_list() returned {len(subjects)} subjects")

        # Test get_genotype
        test_subject = subjects[0]
        genotype = get_genotype(test_subject)
        print(f"[OK] get_genotype('{test_subject}') = '{genotype}'")

        # Test get_session_type
        session = get_session_type(test_subject)
        print(f"[OK] get_session_type('{test_subject}') = '{session}'")

        # Test get_subject_metadata
        metadata = get_subject_metadata(test_subject)
        print(f"[OK] get_subject_metadata() returned {len(metadata)} fields")

        # Test get_n_cores
        n_cores = get_n_cores(config)
        print(f"[OK] get_n_cores() = {n_cores}")

        return True

    except Exception as e:
        print(f"[ERROR] Helper function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manifest_functions():
    """Test manifest creation functions."""
    print("\n" + "="*70)
    print("TEST 4: Manifest Functions")
    print("="*70)

    try:
        from run_manifest import (
            get_git_info,
            get_package_versions,
            compute_file_checksum,
        )

        # Test git info
        git_info = get_git_info()
        print(f"[OK] get_git_info() returned {len(git_info)} fields")
        print(f"     Git commit: {git_info['git_commit']}")
        print(f"     Git branch: {git_info['git_branch']}")
        print(f"     Git dirty: {git_info['git_dirty']}")

        # Test package versions
        versions = get_package_versions(['pyyaml', 'psutil'])
        print(f"[OK] get_package_versions() checked {len(versions)} packages")
        for pkg, ver in versions.items():
            print(f"     {pkg}: {ver}")

        # Test checksum
        test_file = Path('config.yaml')
        if test_file.exists():
            checksum = compute_file_checksum(test_file)
            print(f"[OK] compute_file_checksum('config.yaml') = {checksum[:20]}...")
        else:
            print(f"[WARNING] config.yaml not found for checksum test")

        return True

    except Exception as e:
        print(f"[ERROR] Manifest function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manifest_creation():
    """Test creating a complete manifest."""
    print("\n" + "="*70)
    print("TEST 5: Creating Test Manifest")
    print("="*70)

    try:
        from run_manifest import create_run_manifest, print_manifest_summary
        from config_preprocessing import load_config
        import tempfile

        # Load config
        config = load_config('config.yaml')

        # Create temporary output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create manifest
            manifest = create_run_manifest(
                config=config,
                output_dir=output_dir,
                run_id='test_run',
                inputs={
                    'source_data': 'test_data',
                    'n_subjects': 35,
                },
                outputs={
                    'test_output': 'test.parquet',
                },
                performance={
                    'runtime_seconds': 123,
                },
                status={
                    'success': True,
                },
                save=False  # Don't save to disk
            )

            print(f"[OK] Manifest created successfully")
            print(f"     Run ID: {manifest['run_info']['run_id']}")
            print(f"     Timestamp: {manifest['run_info']['timestamp']}")
            print(f"     User: {manifest['run_info']['user']}")

            # Print summary
            print("\n" + "-"*70)
            print_manifest_summary(manifest)
            print("-"*70)

        return True

    except Exception as e:
        print(f"[ERROR] Manifest creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("CONFIGURATION AND MANIFEST SYSTEM - TEST SUITE")
    print("="*70)
    print()

    tests = [
        ("Import Modules", test_imports),
        ("Load Configuration", test_config_loading),
        ("Configuration Helpers", test_config_helpers),
        ("Manifest Functions", test_manifest_functions),
        ("Create Manifest", test_manifest_creation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n" + "="*70)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Your system is ready to use.")
        print("\nNext steps:")
        print("  1. Review the configuration in config.yaml")
        print("  2. See run_manifest_usage_example.py for usage examples")
        print("  3. Add manifest tracking to your notebooks")
    else:
        print("\n[FAILED] Some tests failed. Please fix the errors above.")
        print("\nCommon issues:")
        print("  - Make sure config.yaml exists in the current directory")
        print("  - Install required packages: pip install pyyaml psutil pandas")
        print("  - Check that you're in a git repository for git info")

    print("="*70)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
