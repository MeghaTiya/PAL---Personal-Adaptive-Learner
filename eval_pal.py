#!/usr/bin/env python3
import json
import argparse
from collections import defaultdict
import math
import statistics as stats
import matplotlib.pyplot as plt

def load_results(path):
    rows = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows

def summarize(rows):
    by_variant = defaultdict(list)
    for r in rows:
        v = r.get('variant', 'unknown')
        by_variant[v].append(r)

    summary = {}
    for v, lst in by_variant.items():
        n = len(lst)
        acc = [r.get('overallAccuracy', 0.0) for r in lst]
        score = [r.get('finalScore', 0.0) for r in lst]
        streak = [r.get('bestStreak', 0.0) for r in lst]
        rt = [r.get('avgResponseTimeMs', 0.0) for r in lst]
        def safe_mean(a):
            return sum(a)/len(a) if a else 0
        summary[v] = {
            'runs': n,
            'mean_accuracy': safe_mean(acc),
            'mean_finalScore': safe_mean(score),
            'mean_bestStreak': safe_mean(streak),
            'mean_avgResponseTimeMs': safe_mean(rt),
        }
    return summary

def plot_compare(rows, out='results/pal_compare.png'):
    # Prepare per-variant data
    by_variant = defaultdict(list)
    for r in rows:
        by_variant[r.get('variant', 'unknown')].append(r)

    variants = [v for v in ['baseline', 'enhanced'] if v in by_variant] or list(by_variant.keys())
    colors = {'baseline':'#ef4444', 'enhanced':'#10b981', 'unknown':'#9ca3af'}

    # Compute aggregates
    def arr(v, key):
        return [x.get(key, 0.0) for x in by_variant.get(v, [])]
    def mean(a):
        return sum(a)/len(a) if a else 0.0
    def std(a):
        m = mean(a); return math.sqrt(sum((x-m)**2 for x in a)/len(a)) if a else 0.0
    def mean_acc_by_diff(v, diff):
        lst = []
        for x in by_variant.get(v, []):
            abd = x.get('accuracyByDifficulty', {}) or {}
            val = abd.get(diff, None)
            if isinstance(val, (int, float)):
                lst.append(val)
        return mean(lst)

    # Build figure with 2x2 dashboard
    fig = plt.figure(figsize=(12, 7))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.25)

    # 1) Scatter: accuracy vs avg response time
    ax1 = fig.add_subplot(gs[0, 0])
    for v in variants:
        xs = [r.get('avgResponseTimeMs', 0)/1000.0 for r in by_variant.get(v, [])]
        ys = [r.get('overallAccuracy', 0) for r in by_variant.get(v, [])]
        ax1.scatter(xs, ys, c=colors.get(v, '#9ca3af'), alpha=0.7, label=v)
    ax1.set_xlabel('Avg Response Time (s)')
    ax1.set_ylabel('Overall Accuracy')
    ax1.set_title('Accuracy vs Time')
    ax1.grid(True, alpha=0.2)
    ax1.legend(title='Variant')

    # 2) Bars: mean overall accuracy with error bars (std)
    ax2 = fig.add_subplot(gs[0, 1])
    means = [mean(arr(v, 'overallAccuracy')) for v in variants]
    stds = [std(arr(v, 'overallAccuracy')) for v in variants]
    ax2.bar(variants, means, yerr=stds, color=[colors.get(v, '#9ca3af') for v in variants], alpha=0.9, capsize=6)
    ax2.set_ylim(0, 1)
    ax2.set_ylabel('Mean Accuracy')
    ax2.set_title('Mean Overall Accuracy (± SD)')
    for i, m in enumerate(means):
        ax2.text(i, m + 0.02, f"{m:.2f}", ha='center', va='bottom', fontsize=9)

    # 3) Grouped bars: per-difficulty mean accuracy
    ax3 = fig.add_subplot(gs[1, 0])
    diffs = ['Easy', 'Medium', 'Hard']
    width = 0.35
    x = range(len(diffs))
    for i, v in enumerate(variants):
        vals = [mean_acc_by_diff(v, d) for d in diffs]
        ax3.bar([xi + (i - (len(variants)-1)/2)*width for xi in x], vals, width=width,
                label=v, color=colors.get(v, '#9ca3af'))
    ax3.set_xticks(list(x))
    ax3.set_xticklabels(diffs)
    ax3.set_ylim(0, 1)
    ax3.set_ylabel('Accuracy')
    ax3.set_title('Per-Difficulty Accuracy')
    ax3.legend(title='Variant')

    # 4) Bars: mean response time (s)
    ax4 = fig.add_subplot(gs[1, 1])
    rt_means = [mean([r.get('avgResponseTimeMs', 0)/1000.0 for r in by_variant.get(v, [])]) for v in variants]
    rt_stds = [std([r.get('avgResponseTimeMs', 0)/1000.0 for r in by_variant.get(v, [])]) for v in variants]
    ax4.bar(variants, rt_means, yerr=rt_stds, color=[colors.get(v, '#9ca3af') for v in variants], alpha=0.9, capsize=6)
    ax4.set_ylabel('Mean Avg Response Time (s)')
    ax4.set_title('Mean Response Time (± SD)')
    for i, m in enumerate(rt_means):
        ax4.text(i, m + (0.03 if m >= 0 else 0.003), f"{m:.2f}s", ha='center', va='bottom', fontsize=9)

    fig.suptitle('PAL Baseline vs Enhanced — Evaluation Dashboard', fontsize=14)
    plt.savefig(out, dpi=150, bbox_inches='tight')
    print(f"Saved plot to {out}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default='data/pal_results.jsonl')
    ap.add_argument('--plot', default='results/pal_compare.png')
    args = ap.parse_args()

    rows = load_results(args.results)
    if not rows:
        print('No results found. Run the app and finish sessions first.')
        return
    summary = summarize(rows)
    print(json.dumps(summary, indent=2))
    plot_compare(rows, args.plot)

if __name__ == '__main__':
    main()


