#!/usr/bin/env python3
"""
anagram_engine.py

Simple anagram finder to test whether a target phrase (e.g., a band name) can be composed
from words in WORDLIST.txt or PASSLIST.txt. Designed for puzzle work: finds candidate
combinations of 2-3 words whose combined letters form an anagram of the target.

Usage:
  python tools/anagram_engine.py "smith lyle moore" --wordlists WORDLIST.txt,PASSLIST.txt --max-words 3 --max-results 200

Notes:
- This is a heuristic helper: it matches letter multisets (ignoring spaces/punctuation/case).
- For performance it pre-filters candidate words to those whose letters are subset of the target.
- Increase --max-words cautiously (combinatorial explosion).

"""
import argparse
import re
import itertools
from collections import Counter


def clean(s):
    return re.sub(r"[^A-Za-z]", "", s).lower()


def load_wordlists(paths):
    words = set()
    for p in paths.split(','):
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                for l in fh:
                    w = l.strip()
                    if not w: continue
                    words.add(re.sub(r'[^A-Za-z]', '', w).lower())
        except FileNotFoundError:
            print(f"Warning: wordlist {p} not found")
    return sorted(words)


def is_subset(counter_small, counter_big):
    for k, v in counter_small.items():
        if counter_big.get(k, 0) < v:
            return False
    return True


def counter_from_word(w):
    return Counter(w)


def find_combinations(target, words, max_words=3, max_results=200):
    target_clean = clean(target)
    target_counter = Counter(target_clean)
    # prefilter words that can fit
    cand = [w for w in words if is_subset(Counter(w), target_counter) and 1 < len(w)]
    results = []
    # try combinations from 1..max_words
    for r in range(1, max_words+1):
        # to avoid blowup, only iterate combinations up to a limit
        for combo in itertools.combinations(cand, r):
            combined = ''.join(combo)
            if Counter(combined) == target_counter:
                results.append(combo)
                if len(results) >= max_results:
                    return results
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument('target', help='Target phrase to anagram (quoted)')
    p.add_argument('--wordlists', default='WORDLIST.txt,PASSLIST.txt', help='Comma-separated wordlist files')
    p.add_argument('--max-words', type=int, default=3)
    p.add_argument('--max-results', type=int, default=200)
    args = p.parse_args()

    words = load_wordlists(args.wordlists)
    print(f"Loaded {len(words)} words from {args.wordlists}")
    results = find_combinations(args.target, words, max_words=args.max_words, max_results=args.max_results)
    if not results:
        print("No exact anagram combinations found with current wordlists and max_words")
    else:
        print(f"Found {len(results)} combinations:")
        for combo in results:
            print(' + '.join(combo))

if __name__ == '__main__':
    main()
