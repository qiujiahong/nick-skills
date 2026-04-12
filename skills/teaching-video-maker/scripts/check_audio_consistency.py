#!/usr/bin/env python3
"""Check whether scene audio clips keep a consistent narrator voice."""

import argparse
import sys
from pathlib import Path

try:
    import librosa
    import numpy as np
except ImportError as exc:
    raise SystemExit(
        "check_audio_consistency.py requires librosa and numpy. "
        "Run it with the VibeVoice venv, for example: "
        "$VIBEVOICE_VENV/bin/python scripts/check_audio_consistency.py audio"
    ) from exc


def clip_metrics(path: Path) -> dict:
    y, sr = librosa.load(path, sr=16000, mono=True)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    energy_floor = max(float(np.percentile(rms, 35)), 1e-4)
    voiced_mask = rms > energy_floor

    f0 = librosa.yin(y, fmin=50, fmax=450, sr=sr, frame_length=2048, hop_length=512)
    f0_mask = voiced_mask[: len(f0)]
    voiced_f0 = f0[: len(f0_mask)][f0_mask]

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)
    mfcc_mask = voiced_mask[: mfcc.shape[1]]
    voiced_mfcc = mfcc[:, mfcc_mask]

    if len(voiced_f0) == 0 or voiced_mfcc.shape[1] == 0:
        raise RuntimeError(f"Could not measure voiced audio in {path}")

    return {
        "path": path,
        "median_f0": float(np.median(voiced_f0)),
        "rms_db": float(20 * np.log10(np.sqrt(np.mean(y * y)) + 1e-12)),
        "mfcc": np.mean(voiced_mfcc, axis=1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect pitch/timbre outliers across scene wav files.")
    parser.add_argument("audio_dir", nargs="?", default="audio")
    parser.add_argument("--pattern", default="scene-*.wav")
    parser.add_argument("--max-pitch-cents", type=float, default=300.0)
    parser.add_argument("--max-rms-diff-db", type=float, default=4.0)
    parser.add_argument("--max-mfcc-distance", type=float, default=6.0)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    audio_dir = Path(args.audio_dir)
    paths = sorted(audio_dir.glob(args.pattern))
    if len(paths) < 2:
        raise SystemExit(f"Need at least two audio files matching {audio_dir / args.pattern}")

    rows = [clip_metrics(path) for path in paths]
    base_f0 = float(np.median([row["median_f0"] for row in rows]))
    base_rms = float(np.median([row["rms_db"] for row in rows]))
    mfcc_matrix = np.stack([row["mfcc"] for row in rows])
    base_mfcc = np.median(mfcc_matrix, axis=0)
    mfcc_scale = np.std(mfcc_matrix, axis=0) + 1e-6

    outliers = []
    print("file,median_f0,pitch_cents,rms_db,mfcc_distance,status")
    for row in rows:
        pitch_cents = float(1200 * np.log2(row["median_f0"] / base_f0))
        rms_diff = float(row["rms_db"] - base_rms)
        mfcc_distance = float(np.linalg.norm((row["mfcc"] - base_mfcc) / mfcc_scale))
        reasons = []
        if abs(pitch_cents) > args.max_pitch_cents:
            reasons.append(f"pitch {pitch_cents:+.0f} cents")
        if abs(rms_diff) > args.max_rms_diff_db:
            reasons.append(f"rms {rms_diff:+.1f} dB")
        if mfcc_distance > args.max_mfcc_distance:
            reasons.append(f"mfcc {mfcc_distance:.2f}")
        status = "ok" if not reasons else "outlier: " + "; ".join(reasons)
        print(
            f"{row['path'].name},{row['median_f0']:.1f},{pitch_cents:+.0f},"
            f"{row['rms_db']:.1f},{mfcc_distance:.2f},{status}"
        )
        if reasons:
            outliers.append(row["path"].name)

    if outliers and not args.warn_only:
        print("Voice consistency check failed for: " + ", ".join(outliers), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
