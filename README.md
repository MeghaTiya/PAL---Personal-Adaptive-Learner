# PAL — Personal Adaptive Learner

A modular research/production toolkit for building adaptive video learning experiences.

This repository brings together three pieces:

- Adaptive delivery and UI: a React demo app that plays a lesson video and injects questions at timestamps while adapting difficulty per learner.
- Hybrid RL algorithm: Transparent, blendable policy (Statistical + RL bandit) with live analytics and logging.
- Agentic question generation and personalised summarisation: Flask apps that turn a lecture video+transcript into multi‑difficulty questions and generate student‑aware review summaries.

## Repository layout

```
PAL---Personal-Adaptive-Learner/
├── demo_application/            # React demo app (UI + player + adaptive flow)
├── hybrid_rl_algorithm/         # Core RL/statistical algorithms
├── question_generator/          # Flask app: agentic video→questions pipeline
├── personalised_summariser/     # Flask app: transcript‑aware summary generator
└── LICENSE                      # MIT
```

## What’s inside (high level)

- Adaptive difficulty selection
  - Enhanced statistical policy: time, streak, confidence, and IRT‑style smoothing
  - Pure RL bandit: epsilon‑greedy Q‑learning over {Easy, Medium, Hard}
  - Hybrid policy: interpretable blending of Statistical and RL with live explanations
- End‑to‑end demo paths
  - React SPA: login → select lesson → watch video → answer adaptive questions → summary
  - Vanilla browser demo in `hybrid_rl_algorithm/` with YouTube player and analytics
- Content tooling
  - Agentic question generator: “3+1” pipeline with transcript analysis, VLM‑assisted context validation, question generation, LLM judging, and difficulty tagging
  - Personalised summariser: concept‑aware, transcript‑grounded explanations
- Logging and analysis
  - Session metrics collector (`/pal_logs`) and JSONL output
  - Utilities to convert datasets and visualise adaptiveness

## Prerequisites

- Node.js 18+ and npm (for the React demo)
- Python 3.9+ (for Flask apps and analysis utilities)
- macOS/Linux/WSL recommended
- Optional (for heavy models): a machine with GPU and access to Hugging Face models if you intend to run the personalised summariser locally (Llama‑3.2‑1B‑Instruct)

## Quickstart guide

### 1) Run the React demo app (adaptive learning UI)

- Install and start:

```
cd /Users/aryamanbahl/IIITH/PAL---Personal-Adaptive-Learner/demo_application
npm install
npm start
```

- App opens at http://localhost:3000
- The app auto‑loads a prepared dataset from `public/data/D2-S1_Corln.v.Causn_questions_20250829_081747.json` via `src/data_saver/DataLoader.js` and displays lessons from it.

Key files:

- `src/pages/Video.js`: plays lesson video, pauses at timestamps, shows `QuestionCard`
- `src/model/HybridLearner.js`: tracks state and forwards to the hybrid algorithm
- `src/model/HybridPALAlgorithm.js`: in‑app hybrid blending client

Notes:

- Correctness in `QuestionCard` currently checks selected option vs the first option in the list; the JSON produced by the generator sets the correct answer as the first entry.

### 2) Explore the Hybrid RL algorithm (browser demo + logs)

- Start the static server and session log collector:

```
cd /PAL---Personal-Adaptive-Learner/hybrid_rl_algorithm
python3 app.py --port 8080
```

- Open the demo:

```
open http://localhost:8080/index.html
```

- Features:
  - Dataset loader converts a MCQ JSON to a 5‑segment lesson
  - Live analytics panel shows probabilities, RL Q‑values, explanations
  - Logging to `data/pal_results.jsonl` via POST `/pal_logs`

Key algorithm modules:

- `src/algorithms/time_streak_confidence.js` → Enhanced Statistical policy
- `src/algorithms/rl_adaptive_learning.js` → Pure RL bandit with interpretable decisions
- `src/algorithms/hybrid_adaptive_learning.js` → Interpretable blending + stats

Utilities:

- `src/utils/dataset_loader.js` → transforms generic questions JSON into lesson segments
- `src/utils/session_logger.js` → sends session metrics to `/pal_logs`

### 3) Generate questions from videos (Flask)

- Install dependencies:

```
cd /PAL---Personal-Adaptive-Learner/question_generator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- Open the UI at `http://127.0.0.1:5000/`
- Upload a video and either upload a transcript (JSON/SRT/VTT/TXT) or check “Generate transcript automatically”
- Click Generate Questions; validated questions are saved under `uploads/` with a timestamped filename and downloadable from the UI

Pipeline overview (TriPlusOne):

- Transcript Analyzer → candidate timestamps
- Context Validator (VLM‑assisted) → frame/transcript alignment and concepts
- Question Generator → MCQ/MSQ/NAT across easy/medium/hard
- LLM Judge → quality score, tags, difficulty

Outputs format (per question):

- `question.text`, `question.options[]`, `question.answer`, `question.difficulty`, `timestamp`, `segment_context` metadata

### 4) Personalised summariser (Flask)

- This app loads `meta-llama/Llama-3.2-1B-Instruct` and `all-MiniLM-L6-v2`. It may require GPU and model access.

Run:

```
cd /PAL---Personal-Adaptive-Learner/personalised_summariser
python3 app.py -p 5100
```

- Open `http://127.0.0.1:5100/`
- API: POST `/generate-summaries-batch` with an array of items `{ topic, category, status }` to receive concise, transcript‑grounded explanations. The app uses semantic search over `transcript.txt` to ground the responses.

## Data flow and artifacts

- Question generation
  - Inputs: video file, transcript (optional if auto‑generated)
  - Outputs: JSON file with multi‑difficulty questions, timestamped
- React demo
  - Consumes the JSON; `DataLoader.js` groups questions by timestamp into `Question` objects with per‑difficulty entries
  - Plays video from `public/assets/vid/...`; pauses at timestamps; renders `QuestionCard`
- Hybrid RL demo
  - Client emits session metrics at lesson completion to `/pal_logs`
  - Collector appends to `hybrid_rl_algorithm/data/pal_results.jsonl`
  - Use `utils/adaptiveness_eval.py` to build plots

## Troubleshooting

- Port conflicts: change `--port` for Flask/HTTP servers
- CORS/proxy for React → Hybrid logs: add `"proxy": "http://localhost:8080"` in React `package.json` if posting to the collector while `npm start` is running
- Large model loading (summariser): ensure Hugging Face auth and sufficient VRAM; otherwise run on CPU (slow) or swap to a lighter model

## License

This project is licensed under the MIT License — see `LICENSE`.
