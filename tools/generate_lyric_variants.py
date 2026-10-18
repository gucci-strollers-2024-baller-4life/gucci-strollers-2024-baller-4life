#!/usr/bin/env python3
"""
generate_lyric_variants.py
Produce compact/underscore/hyphen/suffix variants for the official lyric lines.
Usage:
  python generate_lyric_variants.py > lyric_variants.txt
"""
import re

lyrics = [
    "I'll Still Be Loving You",
    "High tide will bring her back to the coast",
    "On this ship I will wait for the day that she knocks on my door",
    "Until the stars burn out",
    "We'll paint our names across the silver sky",
    "When the final stars explode"
]

suffixes = ["", "2022", "2023", "2077", "77", "69", "1949"]

def clean(s):
    return re.sub(r"[^A-Za-z0-9 ]+", "", s).strip()

def make_variants(line):
    base = clean(line).lower()
    words = base.split()
    variants = set()
    variants.add("".join(words))
    variants.add("_".join(words))
    variants.add("-".join(words))
    # substrings of length >=2 (to catch condensed forms)
    for L in range(2, len(words)+1):
        for i in range(len(words)-L+1):
            variants.add("".join(words[i:i+L]))
            variants.add("_".join(words[i:i+L]))
    # with suffixes
    for s in suffixes:
        if s:
            variants.add("".join(words) + s)
            variants.add("_".join(words) + s)
            variants.add("-".join(words) + s)
    return variants

if __name__ == "__main__":
    allvars = set()
    for l in lyrics:
        allvars |= make_variants(l)
    for v in sorted(allvars):
        print(v)
