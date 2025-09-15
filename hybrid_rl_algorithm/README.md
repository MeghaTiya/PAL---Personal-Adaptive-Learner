# PAL — Hybrid RL Personal Adaptive Learner

PAL selects question difficulty per interaction by blending a robust Statistical policy with a lightweight RL bandit. It adapts quickly, explains each decision, and gracefully falls back if a component is unavailable.

## What’s inside

- **Hybrid RL selector** (Statistical + RL with adaptive blending)
- **Pure RL bandit** (epsilon‑greedy, Q‑learning over {Easy, Medium, Hard})
- **Enhanced Statistical policy** (IRT base + time/streak/confidence buffers)
- **Browser demo** (vanilla) and **React integration**
- **Logging & analysis** (JSONL logs, scorecards, adaptiveness plots)

## Directory structure

```
PAL---Personal-Adaptive-Learner/
├── index.html                      # Vanilla demo UI
├── app.py                          # Static server + /pal_logs JSONL collector
├── src/
│   ├── app.js                      # Vanilla demo controller
│   └── algorithms/
│       ├── hybrid_adaptive_learning.js
│       ├── rl_adaptive_learning.js
│       └── time_streak_confidence.js
│   └── utils/
│       ├── dataset_loader.js       # Convert datasets → PAL segments
│       └── session_logger.js       # Post metrics to /pal_logs
├── react-learning-app/             # React UI integrated with PAL
│   ├── public/pal/                 # Copied PAL browser scripts
│   └── src/pal/usePAL.js           # React hook adapter for PAL
├── data/
│   ├── PAL AAAI 26 Demo Questions Aug 29 2025.json
│   └── pal_results.jsonl           # Session logs (app.py collector)
├── results/
│   ├── pal_compare.png             # Baseline vs Enhanced scorecard
│   ├── hybrid_adaptiveness.png     # Adaptiveness over interactions
│   └── hybrid_adaptiveness_26.png  # First 26 interactions
├── utils/
│   └── adaptiveness_eval.py        # Builds adaptiveness plot + metrics
├── notebooks/                      # Analysis notebooks
├── docs/                           # Reports
└── requirements_analysis.txt       # Python analysis deps
```

## How Hybrid works

The Hybrid policy blends Statistical and RL predictions using a weight that grows with evidence (confidence, progress). Every decision includes an explanation (weights, predictions), improving transparency.

## Quick start

### A) Vanilla demo

1) Start server and collector:

```bash
cd /PAL---Personal-Adaptive-Learner
python3 app.py --port 8080
```

2) Open:

```bash
open http://localhost:8080/index.html
```

3) Click “Load Attached Dataset”, then “Start Learning!”. Session logs append to `data/pal_results.jsonl`.

### B) React app

1) Install Node (nvm/Homebrew), then:

```bash
cd /PAL---Personal-Adaptive-Learner/react-learning-app
npm install
npm start
```

2) Optional: enable logging while dev‑serving

```json
// react-learning-app/package.json
"proxy": "http://localhost:8080"
```

Run in another terminal:

```bash
cd /PAL---Personal-Adaptive-Learner
python3 app.py --port 8080
```

## Headless evaluation & plots

1) Install deps:

```bash
python3 -m pip install -r requirements_analysis.txt
python3 -m pip install playwright
python3 -m playwright install --with-deps chromium
```

2) Run sessions & scorecard:

```bash
python3 auto_run.py --port 8080 --runs 6 --modes enhanced --results data/pal_results.jsonl --plot results/pal_compare.png
```

3) Adaptiveness plots:

```bash
python3 utils/adaptiveness_eval.py --results data/pal_results.jsonl --out results/hybrid_adaptiveness.png
python3 utils/adaptiveness_eval.py --results data/pal_results.jsonl --out results/hybrid_adaptiveness_26.png --limit 26
```

## Results (from `results/`)

![Baseline vs Enhanced scorecard](results/pal_compare.png)

- **Hybrid (enhanced) vs baseline**: Higher mean overall accuracy and final score across runs. Response times show wider variance due to exploration; median latency remains low for both.
- **Difficulty-wise**: Gains are most visible on Easy/Medium; Hard remains challenging, and the policy backs off when confidence drops.

![Adaptiveness across interactions](results/hybrid_adaptiveness.png)

- **How to read**: Top track shows the chosen difficulty per interaction. Bottom traces are recent correctness means by difficulty. The policy escalates when recent performance is high and backs off after errors, reflecting the blend of Statistical thresholds and RL value updates.
- **Takeaway**: The selector adapts quickly, oscillating early while it learns and stabilising as evidence accumulates.

Reproduce these figures using the commands in "Headless evaluation & plots" above; artifacts are saved under `results/`.

## Getting the user’s response history

PAL records each interaction and persists it after a session.

- Live during session: `state.learnerProfile.difficultyHistory`
  - `{ difficulty, correct, responseTime, scoreChange, questionText, selectedOption, correctAnswer }`
- Persisted per session: `data/pal_results.jsonl`
  - Each line includes `answeredQuestions` mirroring the above fields.

Export to CSV:

```python
import json, csv
rows=[]
with open('data/pal_results.jsonl') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        r=json.loads(line)
        for a in (r.get('answeredQuestions') or []):
            a['variant']=r.get('variant')
            a['finalScore']=r.get('finalScore')
            rows.append(a)
with open('results/answered_questions.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=['variant','difficulty','correct','rt','q','selected','answer','finalScore'])
    w.writeheader()
    for x in rows:
        w.writerow({
          'variant':x.get('variant'),
          'difficulty':x.get('difficulty'),
          'correct':x.get('correct'),
          'rt':x.get('rt'),
          'q':x.get('q'),
          'selected':x.get('selected'),
          'answer':x.get('answer'),
          'finalScore':x.get('finalScore')
        })
print('Wrote results/answered_questions.csv', len(rows))
```

## Tuning adaptiveness (where to edit)

- Statistical thresholds, cooldowns, smoothing: `src/algorithms/time_streak_confidence.js`
- Hybrid blending & explanations: `src/algorithms/hybrid_adaptive_learning.js`
- RL learning rates, epsilon schedule: `src/algorithms/rl_adaptive_learning.js`

Notes:

- Opening `index.html` without the server works for UI, but dataset fetches and `/pal_logs` need `app.py`.
- React + PAL: integration lives in `react-learning-app/src/pal/usePAL.js` and `src/pages/Video.js`.
