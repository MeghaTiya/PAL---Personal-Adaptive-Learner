// PAL Enhanced Algorithm Module: Time-, Streak-, and Confidence-aware selection
// Exposes window.PALAlgorithm with:
// - getNextDifficulty({ state })
// - updateProfileAfterAnswer(state, correct, difficulty, responseTime)
// Epsilon Greedy Bandit {Easy, Medium, Hard}
// Q-values for each difficulty level
// 6D state (skill, recent accuracy, time, streak, velocity, confidence)

(function () {
    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    // IRT (2-PL) base difficulty distribution
    function irtBaseProbabilities(theta, params) {
        const beta = (params && params.beta) || { Easy: 20, Medium: 50, Hard: 80 };
        const slope = (params && params.slope) || { Easy: 0.15, Medium: 0.10, Hard: 0.07 };
        const p = {};
        ['Easy','Medium','Hard'].forEach(d => {
            const a = slope[d], b = beta[d];
            p[d] = 1 / (1 + Math.exp(-a * (theta - b)));
        });
        const total = p.Easy + p.Medium + p.Hard;
        return { Easy: p.Easy/total, Medium: p.Medium/total, Hard: p.Hard/total };
    }

    function safeAcc(arr) {
        if (!arr || arr.length === 0) return 0.5;
        const s = arr.reduce((a, b) => a + (b ? 1 : 0), 0);
        return s / arr.length;
    }

    function weightedAccuracy(history, difficulty, decay) {
        if (!history || history.length === 0) return 0.5;
        let num = 0, den = 0;
        let w = 1.0;
        for (let i = history.length - 1; i >= 0; i--) {
            const h = history[i];
            if (!difficulty || h.difficulty === difficulty) {
                num += w * (h.correct ? 1 : 0);
                den += w;
            }
            w *= decay;
        }
        if (den === 0) return 0.5;
        return num / den;
    }

    function applySmoothing(probs, recentHistory) {
        if (!recentHistory || recentHistory.length < 3) return probs;
        const last = recentHistory.slice(-5);
        const dist = { Easy: 0, Medium: 0, Hard: 0 };
        last.forEach(q => { dist[q.difficulty] = (dist[q.difficulty] || 0) + 1; });
        const n = last.length;
        const recent = {
            Easy: dist.Easy / n,
            Medium: dist.Medium / n,
            Hard: dist.Hard / n
        };
        const smoothingFactor = 0.6;
        const out = {
            Easy: (probs.Easy * (1 - smoothingFactor)) + (recent.Easy * smoothingFactor),
            Medium: (probs.Medium * (1 - smoothingFactor)) + (recent.Medium * smoothingFactor),
            Hard: (probs.Hard * (1 - smoothingFactor)) + (recent.Hard * smoothingFactor)
        };
        out.Easy = clamp(out.Easy, 0.05, 0.8);
        out.Medium = clamp(out.Medium, 0.1, 0.6);
        out.Hard = clamp(out.Hard, 0.05, 0.7);
        return out;
    }

    function normalize(p) {
        const t = p.Easy + p.Medium + p.Hard;
        return { Easy: p.Easy / t, Medium: p.Medium / t, Hard: p.Hard / t };
    }

    function sample(probs) {
        const r = Math.random();
        let c = 0;
        for (const [k, v] of Object.entries(probs)) {
            c += v;
            if (r <= c) return k;
        }
        return "Easy";
    }

    function ensureProfileStructures(profile) {
        if (!profile.timeStats) {
            profile.timeStats = {
                Easy: { ema: null, var: 0, n: 0 },
                Medium: { ema: null, var: 0, n: 0 },
                Hard: { ema: null, var: 0, n: 0 }
            };
        }
        if (!profile.betaAcc) {
            profile.betaAcc = {
                Easy: { a: 1, b: 1 },
                Medium: { a: 1, b: 1 },
                Hard: { a: 1, b: 1 }
            };
        }
        if (typeof profile.cooldownRemaining !== 'number') {
            profile.cooldownRemaining = 0;
        }
        if (typeof profile.repromotionHoldRemaining !== 'number') {
            profile.repromotionHoldRemaining = 0; // hold promotions for a few interactions after demotion
        }
        if (!profile.irtParams) {
            profile.irtParams = { beta: { Easy: 20, Medium: 50, Hard: 80 }, slope: { Easy: 0.15, Medium: 0.10, Hard: 0.07 } };
        }
    }

    function updateTimeEma(stats, x, alpha) {
        if (stats.n === 0 || stats.ema === null) {
            stats.ema = x;
            stats.var = 0;
            stats.n = 1;
            return;
        }
        const prevEma = stats.ema;
        stats.ema = alpha * x + (1 - alpha) * stats.ema;
        // Exponential moving variance approximation (West et al.)
        const diff = x - prevEma;
        stats.var = alpha * diff * diff + (1 - alpha) * stats.var;
        stats.n += 1;
    }

    function zFromStats(stats, x) {
        if (!stats || stats.n < 5) return 0; // not enough info
        const sd = Math.sqrt(Math.max(stats.var, 1e-6));
        if (sd === 0) return 0;
        return (x - stats.ema) / sd;
    }

    function confidenceFromBeta(beta) {
        // Use normalized precision as confidence proxy: higher (a+b) => higher confidence
        const a = beta.a, b = beta.b;
        const n = a + b;
        if (n <= 2) return 0.3; // low evidence
        // Variance of Beta: ab / ((a+b)^2 (a+b+1)) -> smaller variance => higher confidence
        const variance = (a * b) / ((n * n) * (n + 1));
        const conf = 1 - Math.min(1, Math.sqrt(variance) * 4); // scale into [0,1]
        return clamp(conf, 0, 1);
    }

    function getNextDifficulty(ctx) {
        const state = ctx.state;
        const profile = state.learnerProfile;
        ensureProfileStructures(profile);

        // IRT-driven base difficulty distribution from skillScore as theta
        let probs = irtBaseProbabilities(state.skillScore, profile.irtParams);

        // Recency-weighted accuracies
        const accEasy = weightedAccuracy(profile.difficultyHistory, 'Easy', 0.85);
        const accMed = weightedAccuracy(profile.difficultyHistory, 'Medium', 0.85);
        const accHard = weightedAccuracy(profile.difficultyHistory, 'Hard', 0.85);

        // Confidence from per-difficulty Beta posteriors, combined with stability-based confidence
        const confEasy = confidenceFromBeta(profile.betaAcc.Easy);
        const confMed = confidenceFromBeta(profile.betaAcc.Medium);
        const confHard = confidenceFromBeta(profile.betaAcc.Hard);
        const globalConfidence = clamp((profile.confidenceLevel * 0.5) + ((confEasy + confMed + confHard) / 3) * 0.5, 0, 1);

        // Response time z-scores (fast => negative z, slow => positive z)
        const zE = profile.timeStats.Easy.ema == null ? 0 : zFromStats(profile.timeStats.Easy, lastResponseTime(profile, 'Easy'));
        const zM = profile.timeStats.Medium.ema == null ? 0 : zFromStats(profile.timeStats.Medium, lastResponseTime(profile, 'Medium'));
        const zH = profile.timeStats.Hard.ema == null ? 0 : zFromStats(profile.timeStats.Hard, lastResponseTime(profile, 'Hard'));

        // Difficulty tendency with asymmetric thresholds and wider evidence window
        // Promote at ≥0.75; demote only at ≤0.35
        probs.Easy *= (accEasy <= 0.35 ? 1.15 : accEasy >= 0.75 ? 0.9 : 1.0);
        probs.Medium *= (accMed <= 0.35 ? 0.85 : accMed >= 0.75 ? 1.05 : 1.0);
        probs.Hard *= (accHard >= 0.75 ? 1.15 : accHard <= 0.35 ? 0.7 : 1.0);

        // Time-sensitivity: If very fast on current/last difficulty, nudge harder; very slow, nudge easier.
        const lastDiff = state.lastDifficulty;
        if (lastDiff === 'Easy' && zE < -0.8) { probs.Hard *= 1.15; probs.Easy *= 0.9; }
        if (lastDiff === 'Medium' && zM < -0.8) { probs.Hard *= 1.08; }
        if (lastDiff === 'Hard' && zH > 0.8) { probs.Hard *= 0.8; probs.Medium *= 1.15; }

        // Streak logic with cooldown to prevent oscillations
        const streak = state.streak;
        if (streak >= 5) {
            const bonus = Math.min(1.35, 1 + (streak - 4) * 0.06);
            probs.Hard *= bonus;
            probs.Easy *= (2 - bonus);
        } else if (streak >= 3) {
            probs.Hard *= 1.08;
            probs.Easy *= 0.95;
        }

        const cw = profile.consecutiveWrong || 0;
        if (cw >= 3) { probs.Easy *= 1.5; probs.Hard *= 0.45; }
        else if (cw === 2) { probs.Easy *= 1.2; probs.Hard *= 0.85; }

        // Rescue step (smoothed): use last up to 5 attempts to decide demotion
        const last5 = profile.difficultyHistory.slice(-5);
        const recentHard = last5.filter(q => q.difficulty === 'Hard');
        if (recentHard.length >= 4) {
            const hardFail = recentHard.filter(q => !q.correct).length / recentHard.length;
            if (hardFail >= 0.65) { probs.Hard *= 0.5; probs.Medium *= 1.2; }
        }

        // Risk budget from confidence: higher confidence allows bolder exploration
        const risk = 0.9 + (globalConfidence * 0.3); // 0.9..1.2
        probs.Hard *= risk;
        probs.Easy *= (2 - risk);

        // Cooldown to avoid immediate re-escalation
        if (profile.cooldownRemaining > 0) {
            probs.Hard *= 0.9;
            probs.Easy *= 1.05;
        }

        // Additional hold after a demotion: temporarily resist re-promotion for a couple of interactions
        if (profile.repromotionHoldRemaining > 0) {
            probs.Hard *= 0.8;
            probs.Medium *= 0.95;
            probs.Easy *= 1.05;
        }

        // Smoothing
        probs = applySmoothing(probs, profile.difficultyHistory);
        probs = normalize(probs);

        // Store last decision for diagnostics
        profile.lastDecision = {
            probs: probs,
            globalConfidence: globalConfidence,
            streak: streak,
            consecutiveWrong: cw
        };

        // Choose difficulty and manage re-promotion hold
        const selected = sample(probs);
        try {
            const order = { 'Easy': 0, 'Medium': 1, 'Hard': 2 };
            const prev = typeof state.lastDifficulty === 'string' ? order[state.lastDifficulty] : null;
            const curr = order[selected];
            if (prev != null && curr != null) {
                if (curr < prev) {
                    // Demotion occurred
                    profile.repromotionHoldRemaining = Math.max(profile.repromotionHoldRemaining, 2);
                } else if (profile.repromotionHoldRemaining > 0) {
                    profile.repromotionHoldRemaining -= 1;
                }
            }
        } catch (e) { /* no-op */ }

        return selected;
    }

    function lastResponseTime(profile, difficulty) {
        if (!profile.difficultyHistory || profile.difficultyHistory.length === 0) return 0;
        for (let i = profile.difficultyHistory.length - 1; i >= 0; i--) {
            const q = profile.difficultyHistory[i];
            if (!difficulty || q.difficulty === difficulty) return q.responseTime || 0;
        }
        return 0;
    }

    function updateProfileAfterAnswer(state, correct, difficulty, responseTime) {
        const p = state.learnerProfile;
        ensureProfileStructures(p);

        // Update EMA time stats per difficulty
        const alpha = 0.2; // EMA smoothing factor
        updateTimeEma(p.timeStats[difficulty], responseTime, alpha);

        // Update Beta accuracy per difficulty
        if (correct) p.betaAcc[difficulty].a += 1; else p.betaAcc[difficulty].b += 1;

        // Update cooldown: extend on wrong answers at Medium/Hard to avoid immediate re-escalation
        if (!correct && (difficulty === 'Hard' || difficulty === 'Medium')) {
            p.cooldownRemaining = Math.min(2, (p.cooldownRemaining || 0) + 1);
        } else if (p.cooldownRemaining > 0) {
            p.cooldownRemaining -= 1;
        }

        // Recompute confidence blending (keep existing app confidence as well)
        const confEasy = confidenceFromBeta(p.betaAcc.Easy);
        const confMed = confidenceFromBeta(p.betaAcc.Medium);
        const confHard = confidenceFromBeta(p.betaAcc.Hard);
        const betaConf = (confEasy + confMed + confHard) / 3;
        p.confidenceLevel = clamp((p.confidenceLevel * 0.6) + (betaConf * 0.4), 0, 1);

        // Lightweight IRT-style theta update to keep base aligned with outcomes
        try {
            const base = irtBaseProbabilities(state.skillScore, p.irtParams);
            const a = (p.irtParams && p.irtParams.slope && p.irtParams.slope[difficulty]) || ({ Easy: 0.15, Medium: 0.10, Hard: 0.07 }[difficulty]);
            const pDiff = base[difficulty];
            const eta = 0.6; // small learning rate
            state.skillScore = clamp(state.skillScore + eta * (((correct ? 1 : 0) - pDiff) * a * 100), 0, 100);
        } catch (e) {
            // no-op
        }
    }

    window.PALAlgorithm = {
        getNextDifficulty,
        updateProfileAfterAnswer
    };
})();


