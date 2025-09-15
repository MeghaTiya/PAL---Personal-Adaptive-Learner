document.addEventListener('DOMContentLoaded', () => {

    // Global Constants
    const BACKEND_URL = '/generate-summaries-batch';
    const debriefView = document.getElementById('debrief-view');
    const debriefTitle = document.getElementById('debrief-title');
    const compassContainer = document.getElementById('compass-container');

    async function initializeApp() {
        try {
            // Load all necessary data from the server's JSON files
            const [allConcepts, studentPerformanceData] = await loadAllData();

            // Directly render the single student's debrief view
            renderDebriefView(studentPerformanceData, allConcepts);

        } catch (error) {
            console.error("Critical Initialization Error:", error);
            // If anything fails, show a clear error message in the main view
            debriefView.innerHTML = `
                <header style="text-align: center;">
                    <h1>Error</h1>
                    <p style="color: #ff5555;">Could not load classroom data. Please ensure concepts.json and studentperformance.json are valid and present.</p>
                </header>`;
        }
    }

    async function loadAllData() {
        const [conceptsRes, studentsRes] = await Promise.all([
            fetch('/concepts.json'),
            fetch('/studentperformance.json')
        ]);
        if (!conceptsRes.ok || !studentsRes.ok) {
            throw new Error(`Failed to fetch data files: Concepts status ${conceptsRes.status}, Students status ${studentsRes.status}`);
        }

        const concepts = await conceptsRes.json();
        const studentPerformance = await studentsRes.json();

        // The data model now assumes a single student object, not an array
        return [concepts, studentPerformance];
    }

    function renderDebriefView(student, allConcepts) {
        debriefTitle.textContent = `Debrief for ${student.studentId}`;

        const performanceMap = new Map(student.performance.map(p => [p.conceptId, p.status]));
        const studentConcepts = allConcepts.map(c => ({ ...c, status: performanceMap.get(c.id) || 'unknown' }));

        const strengths = studentConcepts.filter(c => c.status === 'correct');
        const areasForReview = studentConcepts.filter(c => c.status !== 'correct');

        compassContainer.innerHTML = `
            <div id="compass">
                <div class="compass-label-top">Mastery</div>
                <div class="compass-label-bottom">Review</div>
            </div>
            <div id="compass-stats">
                <div class="stat"><div id="stat-strengths" class="stat-value">${strengths.length}</div><div class="stat-label">Territory Mastered</div></div>
                <div class="stat"><div id="stat-review" class="stat-value">${areasForReview.length}</div><div class="stat-label">Discovery Zone</div></div>
            </div>`;

        buildAccordionStructure(areasForReview, 'review-accordion');
        buildAccordionStructure(strengths, 'strengths-accordion');

        const mastery = studentConcepts.length > 0 ? (strengths.length / studentConcepts.length) : 0;
        const angle = -90 + (mastery * 180);
        setTimeout(() => { document.getElementById('compass').style.setProperty('--angle', `${angle}deg`); }, 100);

        fetchBatchSummaries(studentConcepts);
    }

    function buildAccordionStructure(data, containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = data.length ? data.map(item => `
            <div class="summary-card ${item.status}" id="card-${item.id}">
                <div class="summary-header">
                    <div class="status-icon"><div class="spinner"></div></div>
                    <div class="topic-title">${item.topic}</div>
                    <div class="chevron"><i class="fa-solid fa-chevron-right"></i></div>
                </div>
                <div class="summary-content"><div class="summary-content-inner">Requesting summary...</div></div>
            </div>`).join('') : `<p class="placeholder-text">All concepts mastered. Great work!</p>`;
    }

    async function fetchBatchSummaries(studentConcepts) {
        const conceptsToFetch = studentConcepts.map(c => ({ topic: c.topic, status: c.status }));
        try {
            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(conceptsToFetch)
            });
            if (!response.ok) throw new Error(`Server responded with ${response.status}`);

            const result = await response.json();
            const summaries = result.summaries;

            studentConcepts.forEach((concept, index) => {
                const card = document.getElementById(`card-${concept.id}`);
                if (card) {
                    card.querySelector('.summary-content-inner').textContent = summaries[index];
                    const icon = concept.status === 'correct' ? '<i class="fa-solid fa-check-circle"></i>' : '<i class="fa-solid fa-compass-drafting"></i>';
                    card.querySelector('.status-icon').innerHTML = icon;
                }
            });
        } catch (error) {
            console.error("Failed to fetch batch summaries:", error);
            studentConcepts.forEach(concept => {
                const card = document.getElementById(`card-${concept.id}`);
                if (card) {
                    card.querySelector('.summary-content-inner').textContent = "Could not generate summary.";
                    card.querySelector('.status-icon').innerHTML = '<i class="fa-solid fa-times-circle"></i>';
                }
            });
        }
    }

    // Simplified Event Listener for the single view
    debriefView.addEventListener('click', (event) => {
        const header = event.target.closest('.summary-header');
        if (header) {
            header.parentElement.classList.toggle('active');
        }
    });

    // Start the application
    initializeApp();
});