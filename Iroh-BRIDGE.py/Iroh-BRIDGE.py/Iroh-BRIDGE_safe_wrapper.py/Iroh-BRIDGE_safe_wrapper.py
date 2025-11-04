"""
Iroh Safe Wrapper
Windows-friendly version

This script simply makes a backup of Iroh.py and checks that the copy matches.
It does not modify, lock, or execute the protected file.
"""

import shutil
import filecmp
import os
import sys

def main():
    print("Step one: locating Iroh.py ...")
    source = "Iroh.py"
    backup = "Iroh_backup.py"

    if not os.path.exists(source):
        print("Error: Iroh.py not found in this folder.")
        sys.exit(1)

    print("Step two: creating backup copy ...")
    shutil.copy2(source, backup)

    print("Step three: verifying integrity ...")
    if filecmp.cmp(source, backup, shallow=False):
        print("Verification complete. Iroh is safe.")
    else:
        print("Warning: backup does not match the original. Please check manually.")

    print("Process complete. You may now close this window.")

if __name__ == "__main__":
    main()
