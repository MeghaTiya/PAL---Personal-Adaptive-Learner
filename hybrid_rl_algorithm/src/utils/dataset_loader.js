// Dataset loader for PAL: converts external MCQ JSON into lessonData format
// Exposes window.PALDataset with:
// - loadFromUrl(url) -> Promise<datasetJSON>
// - buildLessonDataFromDataset(datasetJSON, options) -> lessonData

(function () {
    function letterToIndex(letter) {
        const s = String(letter || '').trim().toUpperCase();
        const idx = 'ABCD'.indexOf(s);
        return idx >= 0 ? idx : null;
    }

    function normalizeOptionText(opt) {
        if (typeof opt === 'string') return opt.trim();
        if (opt && typeof opt.text === 'string') return opt.text.trim();
        return String(opt);
    }

    function extractQ(item) {
        // Support both item.question.{text,options,answer,difficulty} and flat
        const q = item.question || item;
        const text = (q.text || q.prompt || '').trim();
        let options = Array.isArray(q.options) ? q.options.map(normalizeOptionText) : [];
        // Some entries might have only one option; ignore such malformed questions
        if (options.length < 2 && Array.isArray(item.options)) options = item.options.map(normalizeOptionText);

        let answerText = null;
        if (typeof q.answer === 'string' && options.length > 0) {
            const idx = letterToIndex(q.answer);
            if (idx != null && options[idx] !== undefined) answerText = options[idx];
            else answerText = q.answer; // assume already text
        } else if (typeof q.correct === 'string') {
            answerText = q.correct;
        }

        const difficulty = (q.difficulty || item.difficulty || '').toLowerCase();
        const diff = difficulty.startsWith('e') ? 'Easy'
            : difficulty.startsWith('m') ? 'Medium'
            : difficulty.startsWith('h') ? 'Hard'
            : null;

        return {
            text,
            options,
            answerText,
            difficulty: diff
        };
    }

    function buildLessonDataFromDataset(dataset, options) {
        const opts = Object.assign({ segmentCount: 5, videoId: 'ZSt9tm3RoUU' }, options || {});
        const raw = Array.isArray(dataset.questions) ? dataset.questions : [];
        const parsed = raw.map(extractQ).filter(q => q.text && q.options && q.options.length >= 2 && q.answerText);

        // Bucket by difficulty
        const buckets = { Easy: [], Medium: [], Hard: [] };
        parsed.forEach(q => {
            const d = q.difficulty || 'Medium';
            buckets[d].push(q);
        });

        // Build segments; for each timestamp segment, pick one per difficulty (round-robin)
        const segments = [];
        const counts = { Easy: 0, Medium: 0, Hard: 0 };
        for (let i = 0; i < opts.segmentCount; i++) {
            const ts = (i === 0 ? 10 : 10 + i * 15); // start at 10s, then every 15s
            const seg = { timestamp: ts };
            ['Easy', 'Medium', 'Hard'].forEach(d => {
                const list = buckets[d];
                const idx = counts[d] % Math.max(1, list.length);
                const q = list.length > 0 ? list[idx] : null;
                if (q) {
                    seg[d] = {
                        q: q.text,
                        options: q.options,
                        answer: q.answerText
                    };
                    counts[d]++;
                } else {
                    // fallback dummy when bucket empty
                    seg[d] = {
                        q: `Placeholder ${d} question ${i + 1}`,
                        options: ['A', 'B', 'C'],
                        answer: 'A'
                    };
                }
            });
            segments.push(seg);
        }

        return {
            video: opts.videoId,
            questions: segments
        };
    }

    function loadFromUrl(url) {
        return fetch(url).then(r => r.json());
    }

    window.PALDataset = {
        loadFromUrl,
        buildLessonDataFromDataset
    };
})();


