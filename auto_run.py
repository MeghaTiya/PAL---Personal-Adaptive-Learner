#!/usr/bin/env python3
import argparse
import json
import time
import subprocess
import os
import urllib.request
import urllib.error

from playwright.sync_api import sync_playwright

import eval_pal as ep


def run_sessions(base_url: str, variant: str, runs: int, correct_prob: float = 0.8):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        for i in range(runs):
            page = context.new_page()
            url = f"{base_url}?mode={variant}"
            page.goto(url, wait_until="load")

            # Wait for app to render selector and initialize gameState
            page.wait_for_selector('#lessonSelector', timeout=10001)
            # Wait for top-level global binding (declared via 'let gameState' in app.js)
            page.wait_for_function(
                "() => typeof gameState !== 'undefined'",
                timeout=10001,
            )

            # Load provided dataset
            try:
                page.get_by_text("Load Attached Dataset", exact=True).click()
                page.wait_for_function(
                    "() => gameState && gameState.currentLessonData && Array.isArray(gameState.currentLessonData.questions) && gameState.currentLessonData.questions.length > 0",
                    timeout=10001,
                )
            except Exception:
                # Ensure default lesson exists
                page.wait_for_function(
                    "() => gameState && gameState.currentLessonData && Array.isArray(gameState.currentLessonData.questions)",
                    timeout=10001,
                )

            # Start lesson
            page.get_by_text("Start Learning!", exact=False).click()

            # Stub player API used by the app
            page.evaluate(
                """
                try { player = player || {}; } catch(e) { /* global let exists in app.js */ }
                player.pauseVideo = () => {};
                player.playVideo = () => {};
                player.getCurrentTime = () => 9999;
                """
            )

            # Determine number of questions
            q_count = page.evaluate("() => gameState.currentLessonData.questions.length")

            # Trigger first question if not yet shown
            page.evaluate("() => { if (!gameState.showingQuestion) showQuestion(); }")

            for qi in range(q_count):
                # Wait for overlay visible
                page.wait_for_selector("#questionOverlay", state="visible", timeout=5000)
                page.wait_for_selector(".option-button", timeout=5000)

                # Decide selection (correct with probability correct_prob)
                sel_index = page.evaluate(
                    "(cp) => {\n"
                    "  const q = gameState.currentQuestion;\n"
                    "  const options = q.options;\n"
                    "  const answer = q.answer;\n"
                    "  const correct = Math.random() < cp;\n"
                    "  if (correct) {\n"
                    "    return options.findIndex(o => o === answer);\n"
                    "  } else {\n"
                    "    const idx = options.findIndex(o => o !== answer);\n"
                    "    return idx >= 0 ? idx : 0;\n"
                    "  }\n"
                    "}",
                    correct_prob,
                )

                # Click selected option
                page.locator(".option-button").nth(sel_index).click()
                # Submit
                page.locator("#submitBtn").click()
                page.wait_for_selector("#continueBtn", state="visible", timeout=3000)
                # Continue
                page.locator("#continueBtn").click()

                # Wait overlay hidden
                page.wait_for_selector("#questionOverlay", state="hidden", timeout=5000)

                # Trigger next question, unless finished
                page.evaluate(
                    "() => { if (!gameState.finished && !gameState.showingQuestion) showQuestion(); }"
                )

            # Ensure completion appeared
            try:
                page.wait_for_selector("#completion", state="visible", timeout=3000)
            except Exception:
                pass

            # Small delay to allow log POST
            page.wait_for_timeout(300)
            page.close()
        context.close()
        browser.close()
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--modes", nargs="+", default=["baseline", "enhanced"], choices=["baseline", "enhanced"])
    ap.add_argument("--correct-prob", type=float, default=0.8)
    ap.add_argument("--results", default="data/pal_results.jsonl")
    ap.add_argument("--plot", default="results/pal_compare.png")
    args = ap.parse_args()

    base_url = f"http://localhost:{args.port}/index.html"

    # Ensure server is running; if not, start it
    def is_up():
        try:
            with urllib.request.urlopen(base_url, timeout=1) as r:
                return r.status == 200
        except Exception:
            return False

    server_proc = None
    if not is_up():
        app_py = os.path.join(os.path.dirname(__file__), 'app.py')
        server_proc = subprocess.Popen(['python3', app_py, '--port', str(args.port)], cwd=os.path.dirname(app_py))
        # Wait for server to come up
        for _ in range(50):
            if is_up():
                break;
            time.sleep(0.1)

    for m in args.modes:
        print(f"Running {args.runs} sessions for mode={m} ...")
        run_sessions(base_url, m, args.runs, correct_prob=args.correct_prob)

    # Evaluate
    rows = ep.load_results(args.results)
    if not rows:
        print("No results found; ensure the server is running and sessions completed.")
        return
    summary = ep.summarize(rows)
    print(json.dumps(summary, indent=2))
    ep.plot_compare(rows, args.plot)

    # Stop server we started
    if server_proc is not None:
        try:
            server_proc.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    main()


