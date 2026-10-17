"""montage_decode.py

Tool to extract and decode rapid montage windows from a video file.

Usage:
  python tools/montage_decode.py --input path/to/video.mp4 --outdir out/ --min_cuts 80 --frame_rate 120

What it does (overview):
- Extracts frames from the input video at the given capture frame rate.
- Uses a sliding-window detector to find hyper-rapid montage regions by counting scene cuts (frame-to-frame difference).
- For each detected rapid window, clusters frames and attempts a brightness-threshold bit decode per-frame to recover binary ASCII strings (Hunt #1 style montage -> 15 groups of 8 bits -> ASCII).
- Writes per-window PNG strips, a best-effort decoded ASCII file, and a JSON manifest with frame timestamps.

Notes / safety:
- This tool performs only local file processing. It never fetches remote media or transmits data.
- The heuristic decode may require parameter tuning (thresholds and expected bits-per-window).

Dependencies:
- Python 3.9+
- opencv-python, pillow, numpy

"""

import argparse
import os
import json
import cv2
import numpy as np
from PIL import Image


def extract_frames(video_path, outdir, sample_fps=30):
    os.makedirs(outdir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or sample_fps
    step = max(1, int(round(fps / sample_fps)))
    frames = []
    idx = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            fname = os.path.join(outdir, f"frame_{saved:06d}.png")
            Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).save(fname)
            frames.append((saved, fname))
            saved += 1
        idx += 1
    cap.release()
    return frames


def detect_rapid_windows(frames_dir, diff_threshold=30, min_cuts=80):
    # frames_dir contains sequential frame_*.png
    files = sorted([f for f in os.listdir(frames_dir) if f.startswith("frame_")])
    diffs = []
    imgs = []
    for f in files:
        img = cv2.imread(os.path.join(frames_dir, f), cv2.IMREAD_GRAYSCALE)
        imgs.append(img)
    for i in range(1, len(imgs)):
        d = cv2.absdiff(imgs[i], imgs[i-1])
        diffs.append(int(np.mean(d)))
    # find windows with many successive cuts
    windows = []
    start = None
    cuts = 0
    for i, val in enumerate(diffs):
        if val > diff_threshold:
            if start is None:
                start = i-1
            cuts += 1
        else:
            if cuts >= min_cuts:
                windows.append((start, i))
            start = None
            cuts = 0
    if start is not None and cuts >= min_cuts:
        windows.append((start, len(diffs)))
    return windows, files


def decode_window_to_bits(frames_dir, files, start, end, bit_threshold=120):
    # Heuristic: sample each frame's mean brightness and threshold to 0/1
    bits = []
    for idx in range(start, end+1):
        fname = os.path.join(frames_dir, files[idx])
        img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
        m = int(np.mean(img))
        bit = 1 if m > bit_threshold else 0
        bits.append(bit)
    # try group into bytes
    if len(bits) % 8 != 0:
        # trim to nearest byte length
        bits = bits[:(len(bits)//8)*8]
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        val = 0
        for b in byte:
            val = (val << 1) | b
        if 32 <= val < 127:
            chars.append(chr(val))
        else:
            chars.append('?')
    return ''.join(chars), bits


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("--sample_fps", type=int, default=60)
    p.add_argument("--min_cuts", type=int, default=80)
    p.add_argument("--diff_threshold", type=int, default=30)
    p.add_argument("--bit_threshold", type=int, default=120)
    args = p.parse_args()

    frames_dir = os.path.join(args.outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    print(f"Extracting frames to {frames_dir} ...")
    extract_frames(args.input, frames_dir, sample_fps=args.sample_fps)
    print("Detecting rapid montage windows...")
    windows, files = detect_rapid_windows(frames_dir, diff_threshold=args.diff_threshold, min_cuts=args.min_cuts)
    manifest = {"video": args.input, "windows": []}
    for i, (s, e) in enumerate(windows):
        print(f"Decoding window {i}: frames {s}..{e}")
        decoded, bits = decode_window_to_bits(frames_dir, files, s, e, bit_threshold=args.bit_threshold)
        window_out = os.path.join(args.outdir, f"window_{i}")
        os.makedirs(window_out, exist_ok=True)
        # copy frames for reference
        for j in range(s, e+1):
            src = os.path.join(frames_dir, files[j])
            dst = os.path.join(window_out, files[j])
            if not os.path.exists(dst):
                Image.open(src).save(dst)
        with open(os.path.join(window_out, "decoded.txt"), "w") as fh:
            fh.write(decoded)
        manifest["windows"].append({"index": i, "start_frame": s, "end_frame": e, "decoded": decoded, "bits_count": len(bits)})
    with open(os.path.join(args.outdir, "montage_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    print("Done. Check the outdir for window folders and montage_manifest.json")

if __name__ == '__main__':
    main()
