#!/usr/bin/env python3
"""
bip39_multiword_sweep.py
Chunked, checkpointed BIP39 passphrase sweep for multi-word candidate passphrases.

Intentionally limited to local/offline derivation checks. This script will not move
funds or access private accounts. It only does local file I/O and deterministic
seed derivation for candidates provided by the operator.
"""
import argparse
import json
import os
import time
from itertools import product

try:
    from bip_utils import Bip39SeedGenerator, Bip39MnemonicValidator
    HAS_BIP = True
except Exception:
    HAS_BIP = False


def load_lines(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return [line.strip() for line in fh if line.strip()]


def derive_seed_hex(mnemonic, passphrase):
    if not HAS_BIP:
        return "MISSING_BIP_UTILS"
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase)
    return seed_bytes.hex()


def save_progress(outdir, payload):
    with open(os.path.join(outdir, 'progress.json'), 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2)


def load_progress(outdir):
    p = os.path.join(outdir, 'progress.json')
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mnemonic-file', required=True)
    p.add_argument('--candidate-file', required=True)
    p.add_argument('--outdir', required=True)
    p.add_argument('--chunk-size', type=int, default=5000)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--arrangements', type=int, default=2)
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    mnemonic = load_lines(args.mnemonic_file)[0]
    if HAS_BIP:
        try:
            Bip39MnemonicValidator(mnemonic)
        except Exception as exc:
            print(f"Mnemonic validation warning: {exc}")

    candidates = load_lines(args.candidate_file)
    print(f"Loaded {len(candidates)} candidate terms.")

    progress = load_progress(args.outdir) if args.resume else None
    start_idx = progress.get('last_index', 0) if progress else 0
    stats = {'checked': progress.get('checked', 0) if progress else 0}

    with open(os.path.join(args.outdir, 'results.jsonl'), 'a', encoding='utf-8') as fh:
        for idx in range(start_idx, len(candidates)):
            cand = candidates[idx]
            seed_hex = derive_seed_hex(mnemonic, cand)
            rec = {
                'index': idx,
                'candidate': cand,
                'seed_hex_prefix': seed_hex[:64] if seed_hex != 'MISSING_BIP_UTILS' else seed_hex,
                'ts': int(time.time())
            }
            fh.write(json.dumps(rec) + '\n')
            fh.flush()
            stats['checked'] += 1
            if stats['checked'] % args.chunk_size == 0:
                save_progress(args.outdir, {'last_index': idx + 1, 'checked': stats['checked'], 'ts': int(time.time())})
                print(f"Checkpoint: {idx + 1}/{len(candidates)}")

    save_progress(args.outdir, {'last_index': len(candidates), 'checked': stats['checked'], 'ts': int(time.time())})
    print(f"Done. Checked {stats['checked']} candidates.")

if __name__ == '__main__':
    main()
