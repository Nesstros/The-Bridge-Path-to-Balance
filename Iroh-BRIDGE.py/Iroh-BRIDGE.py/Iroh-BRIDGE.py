#!/usr/bin/env python3
"""
iroh_rooted_flame_v2_7_self_protecting.py
Wrapper installer/protection layer for the existing v2_6 integrated script.
- Keeps the original v2_6 file as source of truth.
- Adds commands: install, verify, lock, unlock, run
- install: copies v2_6 into ./iroh_rooted_flame_install/, writes SHA and HMAC (passphrase-derived), sets original read-only
- verify: verifies current v2_6 against stored signature
- run: executes the v2_6 script in the current environment
Note: This wrapper does NOT modify the content of the v2_6 script.
"""
from __future__ import annotations
import sys, os, shutil, hashlib, hmac, subprocess
from pathlib import Path
from getpass import getpass

MAIN_SRC = Path("./iroh_rooted_flame_v2_6_integrated.py")
INSTALL_DIR = Path("./iroh_rooted_flame_install")
SHA_FILE = "file.sha256"
HMAC_FILE = "signature.hmac"

def compute_sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def derive_key(passphrase: str, salt: bytes, iterations: int = 200_000, dklen: int = 32) -> bytes:
    # Use hashlib.pbkdf2_hmac for compatibility
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations, dklen)

def compute_hmac_hex(key: bytes, message: bytes) -> str:
    return hmac.new(key, message, hashlib.sha256).hexdigest()

def set_readonly(path: Path) -> None:
    try:
        if os.name == "nt":
            os.system(f'attrib +R "{str(path)}"')
        else:
            path.chmod(0o444)
    except Exception as e:
        print(f"[Warning] Could not set read-only: {e}")

def set_writable(path: Path) -> None:
    try:
        if os.name == "nt":
            os.system(f'attrib -R "{str(path)}"')
        else:
            path.chmod(0o644)
    except Exception as e:
        print(f"[Warning] Could not set writable: {e}")

def cmd_install():
    if not MAIN_SRC.exists():
        print("[v2.7] Source v2_6 file not found in current directory. Place 'iroh_rooted_flame_v2_6_integrated.py' here and retry.")
        return
    INSTALL_DIR.mkdir(exist_ok=True)
    dst = INSTALL_DIR / MAIN_SRC.name
    try:
        shutil.copy2(MAIN_SRC, dst)
    except Exception as e:
        print(f"[v2.7] Copy failed: {e}")
        return
    sha = compute_sha256_hex(MAIN_SRC)
    # prompt for passphrase to derive HMAC
    pw = getpass("Enter a local passphrase to protect installation (input hidden): ").strip()
    if not pw:
        print("[v2.7] Empty passphrase — aborting HMAC creation.")
        return
    salt = bytes.fromhex(sha)[:16]
    key = derive_key(pw, salt)
    signature = compute_hmac_hex(key, bytes.fromhex(sha))
    try:
        (INSTALL_DIR / SHA_FILE).write_text(sha + "\n", encoding="utf-8")
        (INSTALL_DIR / HMAC_FILE).write_text(signature + "\n", encoding="utf-8")
    except Exception as e:
        print(f"[v2.7] Failed to write signature files: {e}")
        return
    # set original to read-only
    set_readonly(MAIN_SRC)
    print("[v2.7] Installation complete. Portable copy and signatures written to:", INSTALL_DIR.resolve())

def cmd_verify():
    if not MAIN_SRC.exists():
        print("[v2.7] Source v2_6 not found.")
        return
    if not INSTALL_DIR.exists():
        print("[v2.7] Install directory missing.")
        return
    sig_path = INSTALL_DIR / HMAC_FILE
    sha_path = INSTALL_DIR / SHA_FILE
    if not sig_path.exists() or not sha_path.exists():
        print("[v2.7] Signature files missing in install dir.")
        return
    stored_sig = sig_path.read_text(encoding="utf-8").splitlines()[0].strip()
    stored_sha = sha_path.read_text(encoding="utf-8").splitlines()[0].strip()
    current_sha = compute_sha256_hex(MAIN_SRC)
    if current_sha != stored_sha:
        print("[v2.7] SHA mismatch: source file differs from stored SHA. Verification failed.")
        return
    pw = getpass("Enter your local passphrase to verify installation: ").strip()
    if not pw:
        print("[v2.7] Empty passphrase — aborting.")
        return
    salt = bytes.fromhex(current_sha)[:16]
    key = derive_key(pw, salt)
    signature = compute_hmac_hex(key, bytes.fromhex(current_sha))
    if hmac.compare_digest(signature, stored_sig):
        print("[v2.7] Integrity verified. The flame is steady.")
    else:
        print("[v2.7] Integrity verification failed: signature mismatch. Wrong passphrase or file modified.")

def cmd_lock():
    if not MAIN_SRC.exists():
        print("[v2.7] Source v2_6 not found.")
        return
    set_readonly(MAIN_SRC)
    print("[v2.7] Source file set to read-only. To edit, run 'unlock'.")

def cmd_unlock():
    if not MAIN_SRC.exists():
        print("[v2.7] Source v2_6 not found.")
        return
    set_writable(MAIN_SRC)
    print("[v2.7] Source file set to writable. Remember to re-lock after edits.")

def cmd_run():
    if not MAIN_SRC.exists():
        print("[v2.7] Source v2_6 not found.")
        return
    # Run the integrated v2_6 script in a subprocess so this wrapper doesn't need to import it
    try:
        subprocess.run([sys.executable, str(MAIN_SRC)])
    except Exception as e:
        print(f"[v2.7] Failed to run v2_6: {e}")

def usage():
    print("Iroh V2.7 Self-Protecting Wrapper")
    print("Commands: install | verify | lock | unlock | run | help")
    print("  install - create portable copy, compute HMAC (passphrase required), and set original read-only")
    print("  verify  - verify source against stored signature (passphrase required)")
    print("  lock    - set source file to read-only")
    print("  unlock  - restore write permission to source file")
    print("  run     - execute the integrated v2_6 script")
    print("  help    - show this message")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "install":
        cmd_install()
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "lock":
        cmd_lock()
    elif cmd == "unlock":
        cmd_unlock()
    elif cmd == "run":
        cmd_run()
    else:
        usage()
