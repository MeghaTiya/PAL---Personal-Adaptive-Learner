#!/usr/bin/env python3
import json
import argparse
from typing import List, Dict, Any
import math
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_rows(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return rows
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def to_series_from_answered(answered: List[Dict[str, Any]]):
    # Map difficulty to numeric for plotting (Easy=0, Medium=1, Hard=2)
    diff_to_idx = {'Easy': 0, 'Medium': 1, 'Hard': 2}
    chosen_d = [diff_to_idx.get(a.get('difficulty'), np.nan) for a in answered]
    correct = [1 if a.get('correct') else 0 for a in answered]
    # Moving accuracy per difficulty with small window
    recent_mean = {0: [], 1: [], 2: []}
    hist_by_d = {0: [], 1: [], 2: []}
    for a in answered:
        d = diff_to_idx.get(a.get('difficulty'))
        c = 1 if a.get('correct') else 0
        if d is not None:
            hist_by_d[d].append(c)
        for k in (0, 1, 2):
            arr = hist_by_d[k]
            if len(arr) == 0:
                recent_mean[k].append(0.5)
            else:
                # Use last up to 5 attempts for stability
                w = arr[-5:]
                recent_mean[k].append(sum(w) / len(w))
    return np.array(chosen_d, dtype=float), recent_mean


def plot_adaptiveness(chosen_d: np.ndarray, recent_mean: Dict[int, List[float]], out_path: str):
    n = len(chosen_d)
    x = np.arange(n)

    fig, axes = plt.subplots(2, 1, figsize=(10, 4.2), sharex=True)

    # Top: chosen difficulty trajectory
    axes[0].step(x, chosen_d, where='post', color='#1f77b4')
    axes[0].set_ylim(-0.2, 2.2)
    axes[0].set_yticks([0, 1, 2])
    axes[0].set_yticklabels(['Easy', 'Medium', 'Hard'])
    axes[0].set_ylabel('chosen_d')
    axes[0].set_title(f'Hybrid RL adaptiveness (n={n})')

    # Bottom: moving accuracies by difficulty
    axes[1].plot(x, recent_mean[0], 'o-', markersize=3, label='recent_mean_d0')
    axes[1].plot(x, recent_mean[1], 'o-', markersize=3, label='recent_mean_d1')
    axes[1].plot(x, recent_mean[2], 'o-', markersize=3, label='recent_mean_d2')
    axes[1].set_ylim(0.0, 1.05)
    axes[1].set_ylabel('recent_means')
    axes[1].set_xlabel('interaction index')
    axes[1].legend(loc='lower left')

    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=140, bbox_inches='tight')
    return out_path


def compute_metrics(chosen_d: np.ndarray, recent_mean: Dict[int, List[float]]):
    n = len(chosen_d)
    if n == 0:
        return {}
    # Difficulty volatility (number of switches / length)
    switches = int(np.nansum(chosen_d[1:] != chosen_d[:-1]))
    volatility = switches / max(1, n - 1)
    # Time-to-adapt: first index when recent_mean_d0 drops and d2 rises, crude proxy
    d0 = np.array(recent_mean[0])
    d2 = np.array(recent_mean[2])
    try:
        improve_idx = int(np.argmax(d2 > 0.6)) if np.any(d2 > 0.6) else -1
    except Exception:
        improve_idx = -1
    return {
        'n_interactions': n,
        'difficulty_switch_rate': round(float(volatility), 3),
        'stabilization_index_hard>0.6': improve_idx,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default='data/pal_results.jsonl')
    ap.add_argument('--out', default='results/hybrid_adaptiveness.png')
    ap.add_argument('--limit', type=int, default=0, help='Limit the number of interactions to plot (0 = all)')
    args = ap.parse_args()

    rows = load_rows(args.results)
    # Filter for enhanced/hybrid variant
    rows = [r for r in rows if (r.get('variant') == 'enhanced' and isinstance(r.get('answeredQuestions'), list))]
    if not rows:
        print('No enhanced rows with answeredQuestions found.')
        return

    # Concatenate answered events across sessions into a single sequence
    answered_all: List[Dict[str, Any]] = []
    for r in rows:
        answered_all.extend(r.get('answeredQuestions') or [])

    chosen_d, recent_mean = to_series_from_answered(answered_all)

    # Apply limit if set
    if args.limit and args.limit > 0:
        L = min(args.limit, len(chosen_d))
        chosen_d = chosen_d[:L]
        for k in list(recent_mean.keys()):
            recent_mean[k] = recent_mean[k][:L]
    out_path = plot_adaptiveness(chosen_d, recent_mean, args.out)
    metrics = compute_metrics(chosen_d, recent_mean)

    print(json.dumps({'plot': out_path, 'metrics': metrics}, indent=2))


if __name__ == '__main__':
    main()


