# README_RUN_STEPS.md

Local-safe usage guide for the repo's offline passphrase-sweep workflow.

Scope
- This workflow is intended for local/offline candidate generation and derivation checks only.
- It does not access private mail/social accounts, will not send funds, and will not interact with wallets.
- If a strong match is found, stop and move the match artifacts to an air-gapped environment before taking any further action.

Getting started
1. Create a masked mnemonic file named `MNEMONIC.txt` with a known-good BIP39 seed pattern.
   - Example format: `sail ...` or one known mnemonic prefix if you are testing.
   - Never paste a real mnemonic or private key into chat or into a cloud-hosted repo.
2. Create a candidate list named `WORDLIST.txt` or `PASSLIST.txt` with high-probability terms.
3. Run the generator:
   `python tools/generate_lyric_variants.py > PASSLIST.txt`
4. Run the local sweep:
   `python tools/bip39_multiword_sweep.py --mnemonic-file MNEMONIC.txt --candidate-file PASSLIST.txt --outdir out/sweep --chunk-size 5000 --resume`

Notes
- Use low chunk sizes to reduce CPU spikes.
- Progress and partial results are written to `out/sweep/progress.json` and `out/sweep/results.jsonl`.
- If a candidate appears promising, stop the run, isolate the output, and review it by hand.

Safety
- No wallets, no transfers, no secrets in online chat.
- Do not upload private data to public cloud storage.
