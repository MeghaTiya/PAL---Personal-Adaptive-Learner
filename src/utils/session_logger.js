// Minimal client-side session logger: posts session metrics to a local collector
// Configure endpoint via window.PAL_LOG_ENDPOINT or default '/pal_logs'
(function(){
    function postJSON(url, data) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).catch(()=>{});
    }

    function collectMetrics(state, variant, extras) {
        const hist = state.learnerProfile.difficultyHistory;
        const acc = hist.length ? (hist.reduce((s, h) => s + (h.correct ? 1 : 0), 0) / hist.length) : 0;
        const avgRt = state.learnerProfile.responseTime.length ?
            (state.learnerProfile.responseTime.reduce((a,b)=>a+b,0)/state.learnerProfile.responseTime.length) : 0;
        const byDiff = { Easy: {n:0,c:0}, Medium:{n:0,c:0}, Hard:{n:0,c:0} };
        hist.forEach(h => { byDiff[h.difficulty].n += 1; byDiff[h.difficulty].c += (h.correct?1:0); });
        const accByDiff = {
            Easy: byDiff.Easy.n ? byDiff.Easy.c / byDiff.Easy.n : 0,
            Medium: byDiff.Medium.n ? byDiff.Medium.c / byDiff.Medium.n : 0,
            Hard: byDiff.Hard.n ? byDiff.Hard.c / byDiff.Hard.n : 0
        };
        // Build answered questions summary (correct and incorrect lists with minimal fields)
        const answeredSummary = (hist || []).map(h => ({
            difficulty: h.difficulty,
            correct: !!h.correct,
            q: h.questionText || null,
            selected: h.selectedOption || null,
            answer: h.correctAnswer || null,
            rt: h.responseTime || 0
        }));

        return Object.assign({
            timestamp: new Date().toISOString(),
            variant,
            finalScore: state.skillScore,
            bestStreak: state.bestStreak,
            overallAccuracy: acc,
            accuracyByDifficulty: accByDiff,
            avgResponseTimeMs: avgRt,
            questions: hist.length,
            answeredQuestions: answeredSummary
        }, extras || {});
    }

    window.PALSessionLogger = {
        post: function(state, variant, extras){
            const payload = collectMetrics(state, variant, extras);
            const url = window.PAL_LOG_ENDPOINT || '/pal_logs';
            return postJSON(url, payload);
        },
        collect: collectMetrics
    };
})();


