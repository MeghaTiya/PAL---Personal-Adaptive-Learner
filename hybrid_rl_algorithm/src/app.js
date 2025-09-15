// Lesson data
const lessonData = {
    video: "ZSt9tm3RoUU",
    questions: [
        {
            timestamp: 10,
            Easy: { q: "What is 2+2?", options: ["3", "4", "5"], answer: "4" },
            Medium: { q: "What is 12*8?", options: ["96", "108", "112"], answer: "96" },
            Hard: { q: "What is 15²?", options: ["215", "225", "235"], answer: "225" }
        },
        {
            timestamp: 20,
            Easy: { q: "What color is the sky?", options: ["Blue", "Red", "Green"], answer: "Blue" },
            Medium: { q: "What is the capital of France?", options: ["Rome", "Paris", "Berlin"], answer: "Paris" },
            Hard: { q: "Solve for x: 2x+5=15", options: ["3", "4", "5"], answer: "5" }
        },
        {
            timestamp: 30,
            Easy: { q: "How many days in a week?", options: ["6", "7", "8"], answer: "7" },
            Medium: { q: "What is 144 ÷ 12?", options: ["11", "12", "13"], answer: "12" },
            Hard: { q: "What is the derivative of x²?", options: ["x", "2x", "x²"], answer: "2x" }
        },
        {
            timestamp: 45,
            Easy: { q: "Which is largest: 5, 8, or 3?", options: ["5", "8", "3"], answer: "8" },
            Medium: { q: "What is 25% of 200?", options: ["25", "50", "75"], answer: "50" },
            Hard: { q: "If f(x) = 3x + 2, what is f(4)?", options: ["12", "14", "16"], answer: "14" }
        },
        {
            timestamp: 60,
            Easy: { q: "How many sides does a triangle have?", options: ["2", "3", "4"], answer: "3" },
            Medium: { q: "What is the square root of 64?", options: ["6", "7", "8"], answer: "8" },
            Hard: { q: "Solve: 3x² - 12 = 0", options: ["x = 2", "x = 3", "x = 4"], answer: "x = 2" }
        }
    ]
};

// Alternative videos for different lessons
const alternativeVideos = [
    {
        id: "dQw4w9WgXcQ", // Rick Roll for testing
        title: "Advanced Mathematics",
        questions: [
            {
                timestamp: 5,
                Easy: { q: "What is 1+1?", options: ["1", "2", "3"], answer: "2" },
                Medium: { q: "What is 8*7?", options: ["54", "56", "58"], answer: "56" },
                Hard: { q: "What is log₂(16)?", options: ["3", "4", "5"], answer: "4" }
            },
            {
                timestamp: 15,
                Easy: { q: "What comes after 9?", options: ["8", "10", "11"], answer: "10" },
                Medium: { q: "What is 100 - 37?", options: ["63", "73", "83"], answer: "63" },
                Hard: { q: "What is ∫x dx?", options: ["x", "x²/2", "2x"], answer: "x²/2" }
            }
        ]
    },
    {
        id: "jNQXAC9IVRw", 
        title: "Science Basics",
        questions: [
            {
                timestamp: 8,
                Easy: { q: "What gas do we breathe?", options: ["Nitrogen", "Oxygen", "Carbon"], answer: "Oxygen" },
                Medium: { q: "What is H2O?", options: ["Salt", "Water", "Sugar"], answer: "Water" },
                Hard: { q: "What is the speed of light?", options: ["300,000 km/s", "150,000 km/s", "450,000 km/s"], answer: "300,000 km/s" }
            },
            {
                timestamp: 15,
                Easy: { q: "How many legs does a cat have?", options: ["2", "4", "6"], answer: "4" },
                Medium: { q: "What planet is closest to the Sun?", options: ["Venus", "Mercury", "Mars"], answer: "Mercury" },
                Hard: { q: "What is the chemical symbol for Gold?", options: ["Go", "Au", "Gd"], answer: "Au" }
            }
        ]
    }
];

// Enhanced Game state with personalization tracking
let gameState = {
    skillScore: 50,
    streak: 0,
    bestStreak: 0,
    lastDifficulty: "Easy",
    currentQuestionIndex: 0,
    showingQuestion: false,
    finished: false,
    selectedOption: null,
    currentQuestion: null,
    currentDifficulty: null,
    selectedLessonIndex: 0,
    currentLessonData: lessonData,
    
    // Enhanced personalization data
    learnerProfile: {
        responseTime: [], // Track how long user takes to answer
        difficultyHistory: [], // Track difficulty of last N questions
        accuracyByDifficulty: { Easy: [], Medium: [], Hard: [] }, // Track accuracy per difficulty
        consecutiveCorrect: 0,
        consecutiveWrong: 0,
        preferredDifficulty: null, // Learned preference
        adaptationRate: 0.5, // How quickly to adapt (0-1)
        confidenceLevel: 0.5, // Confidence in current skill assessment
        learningVelocity: 0, // Rate of improvement/decline
        sessionStartTime: Date.now(),
        questionStartTime: null
    }
};

// YouTube player
let player;
let checkInterval;

// Lesson selection functions
function selectLesson(index) {
    gameState.selectedLessonIndex = index;
    
    // Update lesson data based on selection
    if (index === 0) {
        gameState.currentLessonData = lessonData;
    } else {
        gameState.currentLessonData = {
            video: alternativeVideos[index - 1].id,
            questions: alternativeVideos[index - 1].questions
        };
    }
    
    // Update UI
    document.querySelectorAll('.lesson-btn').forEach((btn, i) => {
        btn.classList.toggle('active', i === index);
    });
}

function startLesson() {
    // Hide selector, show learning content
    document.getElementById('lessonSelector').style.display = 'none';
    document.getElementById('learningContent').style.display = 'block';
    
    // Reset game state
    gameState.skillScore = 50;
    gameState.streak = 0;
    gameState.bestStreak = 0;
    gameState.lastDifficulty = "Easy";
    gameState.currentQuestionIndex = 0;
    gameState.showingQuestion = false;
    gameState.finished = false;
    gameState.selectedOption = null;
    gameState.currentQuestion = null;
    gameState.currentDifficulty = null;
    
    // Update displays
    updateStatsDisplay();
    updateProgressDisplay();
    
    // Initialize YouTube player
    if (typeof YT !== 'undefined' && YT.Player) {
        initializePlayer();
    }
}

// Dataset integration helpers
async function loadProvidedDataset() {
    try {
        const url = 'data/PAL%20AAAI%2026%20Demo%20Questions%20Aug%2029%202025.json';
        const ds = await PALDataset.loadFromUrl(url);
        const lesson = PALDataset.buildLessonDataFromDataset(ds, { segmentCount: 5, videoId: gameState.currentLessonData.video });
        gameState.currentLessonData = lesson;
        document.getElementById('datasetStatus').textContent = 'Loaded: Provided JSON (' + (ds.total_questions || (ds.questions?.length || 0)) + ' items)';
        // Update lesson buttons to reflect custom dataset
        document.querySelectorAll('.lesson-btn').forEach((btn, i) => {
            btn.classList.toggle('active', i === 0);
        });
        gameState.selectedLessonIndex = 0;
    } catch (e) {
        console.error('Dataset load failed', e);
        document.getElementById('datasetStatus').textContent = 'Failed to load provided JSON';
    }
}

function handleDatasetFile(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function() {
        try {
            const ds = JSON.parse(reader.result);
            const lesson = PALDataset.buildLessonDataFromDataset(ds, { segmentCount: 5, videoId: gameState.currentLessonData.video });
            gameState.currentLessonData = lesson;
            document.getElementById('datasetStatus').textContent = 'Loaded local file: ' + file.name + ' (' + (ds.total_questions || (ds.questions?.length || 0)) + ' items)';
            document.querySelectorAll('.lesson-btn').forEach((btn, i) => {
                btn.classList.toggle('active', i === 0);
            });
            gameState.selectedLessonIndex = 0;
        } catch (e) {
            console.error('Invalid dataset JSON', e);
            document.getElementById('datasetStatus').textContent = 'Invalid JSON file';
        }
    };
    reader.readAsText(file);
}

function resetToSelector() {
    // Stop any running intervals
    stopTimeTracking();
    
    // Show selector, hide learning content
    document.getElementById('lessonSelector').style.display = 'block';
    document.getElementById('learningContent').style.display = 'none';
    document.getElementById('completion').style.display = 'none';
    document.querySelector('.video-container').style.display = 'block';
    
    // Hide question overlay
    document.getElementById('questionOverlay').style.display = 'none';
}

function initializePlayer() {
    if (player) {
        player.loadVideoById(gameState.currentLessonData.video);
    } else {
        player = new YT.Player('player', {
            height: '400',
            width: '100%',
            videoId: gameState.currentLessonData.video,
            playerVars: {
                'playsinline': 1,
                'rel': 0,
                'modestbranding': 1
            },
            events: {
                'onReady': onPlayerReady,
                'onStateChange': onPlayerStateChange
            }
        });
    }
}

// YouTube API ready callback
function onYouTubeIframeAPIReady() {
    console.log('YouTube API ready');
}

function onPlayerReady(event) {
    console.log('Player ready');
    startTimeTracking();
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        console.log('Video started playing');
        startTimeTracking();
    } else if (event.data == YT.PlayerState.PAUSED) {
        console.log('Video paused');
        stopTimeTracking();
    }
}

function startTimeTracking() {
    if (checkInterval) return;
    
    checkInterval = setInterval(() => {
        if (!player || !player.getCurrentTime) return;
        
        const currentTime = player.getCurrentTime();
        
        if (!gameState.finished && gameState.currentQuestionIndex < gameState.currentLessonData.questions.length && !gameState.showingQuestion) {
            const question = gameState.currentLessonData.questions[gameState.currentQuestionIndex];
            if (currentTime >= question.timestamp) {
                showQuestion();
            }
        }
    }, 500); // Check every 500ms
}

function stopTimeTracking() {
    if (checkInterval) {
        clearInterval(checkInterval);
        checkInterval = null;
    }
}

// Advanced Adaptive Algorithm
function getQuestionDifficulty(score, streak, lastDiff) {
    const profile = gameState.learnerProfile;
    
    // Base probabilities based on skill score
    let probs = calculateBaseProbabilities(score);
    
    // Adjust based on recent performance
    probs = adjustForRecentPerformance(probs, profile);
    
    // Adjust based on response time patterns
    probs = adjustForResponseTime(probs, profile);
    
    // Adjust based on accuracy patterns
    probs = adjustForAccuracyPatterns(probs, profile);
    
    // Adjust based on streak and momentum
    probs = adjustForStreakMomentum(probs, streak, lastDiff);
    
    // Adjust for learning velocity (improvement/decline trend)
    probs = adjustForLearningVelocity(probs, profile);
    
    // Apply confidence-based fine-tuning
    probs = adjustForConfidence(probs, profile);
    
    // STABILITY SYSTEM: Prevent wild difficulty swings
    probs = applySmoothingBuffer(probs, profile);
    
    // Ensure probabilities sum to 1
    const total = probs.Easy + probs.Medium + probs.Hard;
    probs.Easy /= total;
    probs.Medium /= total;
    probs.Hard /= total;
    
    // Log the algorithm's reasoning
    console.log('🤖 Algorithm Decision Process:', {
        finalProbabilities: {
            Easy: (probs.Easy * 100).toFixed(1) + '%',
            Medium: (probs.Medium * 100).toFixed(1) + '%', 
            Hard: (probs.Hard * 100).toFixed(1) + '%'
        },
        recentAccuracy: profile.difficultyHistory.length > 0 ? 
            `${((profile.difficultyHistory.slice(-3).reduce((sum, item) => sum + (item.correct ? 1 : 0), 0) / Math.min(3, profile.difficultyHistory.length)) * 100).toFixed(0)}%` : 'N/A',
        confidence: `${(profile.confidenceLevel * 100).toFixed(0)}%`,
        learningVelocity: profile.learningVelocity.toFixed(2)
    });
    
    // Weighted random selection
    // Priority: Hybrid RL > Pure RL > Enhanced Statistical > Fallback Statistical
    if (window.PALHybridAlgorithm && typeof window.PALHybridAlgorithm.getNextDifficulty === 'function') {
        try {
            return window.PALHybridAlgorithm.getNextDifficulty({ state: gameState });
        } catch (e) {
            console.warn('PALHybridAlgorithm.getNextDifficulty failed, falling back:', e);
        }
    }
    if (window.PALRLAlgorithm && typeof window.PALRLAlgorithm.getNextDifficulty === 'function') {
        try {
            return window.PALRLAlgorithm.getNextDifficulty({ state: gameState });
        } catch (e) {
            console.warn('PALRLAlgorithm.getNextDifficulty failed, falling back:', e);
        }
    }
    if (window.PALAlgorithm && typeof window.PALAlgorithm.getNextDifficulty === 'function') {
        try {
            return window.PALAlgorithm.getNextDifficulty({ state: gameState });
        } catch (e) {
            console.warn('PALAlgorithm.getNextDifficulty failed, falling back:', e);
        }
    }
    // Fallback: sample from computed probs
    const rand = Math.random();
    let cumulative = 0;
    for (const [difficulty, prob] of Object.entries(probs)) {
        cumulative += prob;
        if (rand <= cumulative) return difficulty;
    }
    return "Easy";
}

function calculateBaseProbabilities(score) {
    if (score <= 20) {
        return { Easy: 0.85, Medium: 0.12, Hard: 0.03 };
    } else if (score <= 35) {
        return { Easy: 0.75, Medium: 0.20, Hard: 0.05 };
    } else if (score <= 50) {
        return { Easy: 0.55, Medium: 0.35, Hard: 0.10 };
    } else if (score <= 65) {
        return { Easy: 0.35, Medium: 0.45, Hard: 0.20 };
    } else if (score <= 80) {
        return { Easy: 0.20, Medium: 0.45, Hard: 0.35 };
    } else if (score <= 90) {
        return { Easy: 0.10, Medium: 0.35, Hard: 0.55 };
    } else {
        return { Easy: 0.05, Medium: 0.25, Hard: 0.70 };
    }
}

function adjustForRecentPerformance(probs, profile) {
    const recentHistory = profile.difficultyHistory.slice(-4); // Look at last 4 instead of 3
    if (recentHistory.length === 0) return probs;
    
    const recentAccuracy = recentHistory.reduce((sum, item) => sum + (item.correct ? 1 : 0), 0) / recentHistory.length;
    
    // STABILITY BUFFER: More conservative thresholds
    if (recentAccuracy >= 0.75 && recentHistory.length >= 4) {
        // Very high recent performance - gradual difficulty increase
        const performanceBonus = 1 + (recentAccuracy - 0.75) * 0.8; // Less aggressive
        probs.Easy *= 0.85;
        probs.Medium *= 0.95;
        probs.Hard *= performanceBonus;
        console.log(`🎯 Strong recent performance (${(recentAccuracy*100).toFixed(0)}%) - gradual challenge increase`);
    } else if (recentAccuracy <= 0.25 && recentHistory.length >= 3) {
        // Very poor recent performance - provide support but not immediately drastic
        probs.Easy *= 1.3;
        probs.Medium *= 0.9;
        probs.Hard *= 0.7;
        console.log(`📉 Weak recent performance (${(recentAccuracy*100).toFixed(0)}%) - providing measured support`);
    } else if (recentAccuracy >= 0.25 && recentAccuracy < 0.75) {
        // LEARNING ZONE: 25-75% accuracy - maintain current difficulty for practice
        console.log(`⚖️ Learning zone (${(recentAccuracy*100).toFixed(0)}%) - maintaining current difficulty`);
        // Slight bias toward their current performance level
        if (recentAccuracy > 0.5) {
            probs.Medium *= 1.05; // Slight preference for medium
        }
    }
    
    return probs;
}

function adjustForResponseTime(probs, profile) {
    if (profile.responseTime.length < 2) return probs;
    
    const avgResponseTime = profile.responseTime.reduce((a, b) => a + b, 0) / profile.responseTime.length;
    const recentResponseTime = profile.responseTime.slice(-2).reduce((a, b) => a + b, 0) / 2;
    
    // If answering much faster than average, might be too easy
    if (recentResponseTime < avgResponseTime * 0.6) {
        probs.Easy *= 0.8;
        probs.Hard *= 1.2;
    }
    // If answering much slower, might be too hard
    else if (recentResponseTime > avgResponseTime * 1.5) {
        probs.Easy *= 1.2;
        probs.Hard *= 0.8;
    }
    
    return probs;
}

function adjustForAccuracyPatterns(probs, profile) {
    const easyAccuracy = calculateAccuracy(profile.accuracyByDifficulty.Easy);
    const mediumAccuracy = calculateAccuracy(profile.accuracyByDifficulty.Medium);
    const hardAccuracy = calculateAccuracy(profile.accuracyByDifficulty.Hard);
    
    const easyCount = profile.accuracyByDifficulty.Easy.length;
    const mediumCount = profile.accuracyByDifficulty.Medium.length;
    const hardCount = profile.accuracyByDifficulty.Hard.length;
    
    // BUFFER SYSTEM: Need more attempts before making major adjustments
    
    // Easy questions: Only reduce after mastery is clearly demonstrated
    if (easyAccuracy >= 0.85 && easyCount >= 4) {
        const masteryLevel = Math.min(1.5, 1 + (easyAccuracy - 0.85) * 2);
        probs.Easy *= (0.8 / masteryLevel);
        probs.Medium *= 1.1;
        console.log(`🎯 Easy mastery detected (${(easyAccuracy*100).toFixed(0)}% over ${easyCount} questions)`);
    }
    
    // Medium questions: More nuanced adjustment with buffer
    if (mediumCount >= 3) {
        if (mediumAccuracy <= 0.25) {
            // Very poor performance - provide significant support but not immediately
            probs.Easy *= 1.4;
            probs.Medium *= 0.7;
            probs.Hard *= 0.5;
            console.log(`📉 Medium struggling detected (${(mediumAccuracy*100).toFixed(0)}% over ${mediumCount} questions) - providing support`);
        } else if (mediumAccuracy >= 0.8 && mediumCount >= 4) {
            // Strong performance - gradually increase challenge
            probs.Medium *= 0.9;
            probs.Hard *= 1.2;
            console.log(`📈 Medium mastery detected (${(mediumAccuracy*100).toFixed(0)}% over ${mediumCount} questions) - increasing challenge`);
        }
        // BUFFER ZONE: 25%-80% accuracy = no major changes, let them practice
        else if (mediumAccuracy > 0.25 && mediumAccuracy < 0.8) {
            console.log(`⚖️ Medium practice zone (${(mediumAccuracy*100).toFixed(0)}% over ${mediumCount} questions) - maintaining difficulty`);
        }
    }
    
    // Hard questions: Conservative approach with larger buffer
    if (hardCount >= 3) {
        if (hardAccuracy >= 0.75) {
            // Excellent performance on hard - they're ready for more
            probs.Hard *= 1.25;
            probs.Easy *= 0.85;
            console.log(`🔥 Hard mastery detected (${(hardAccuracy*100).toFixed(0)}% over ${hardCount} questions)`);
        } else if (hardAccuracy <= 0.2 && hardCount >= 4) {
            // Really struggling with hard questions - step back gradually
            probs.Hard *= 0.6;
            probs.Medium *= 1.2;
            console.log(`🛡️ Hard difficulty too high (${(hardAccuracy*100).toFixed(0)}% over ${hardCount} questions) - reducing`);
        }
    }
    
    return probs;
}

function adjustForStreakMomentum(probs, streak, lastDiff) {
    // ENHANCED BUFFER SYSTEM FOR STREAKS
    
    // Positive momentum: Build up gradually
    if (streak >= 5) {
        const streakBonus = Math.min(1.4, 1 + (streak - 4) * 0.08); // More gradual increase
        probs.Hard *= streakBonus;
        probs.Easy *= (2 - streakBonus);
        console.log(`🔥 Hot streak (${streak}) - difficulty boost: ${streakBonus.toFixed(2)}x`);
    } else if (streak >= 3) {
        // Moderate streak - small boost
        probs.Hard *= 1.1;
        probs.Easy *= 0.95;
        console.log(`📈 Good streak (${streak}) - slight difficulty increase`);
    }
    
    // Negative momentum: Provide buffer before major changes
    const consecutiveWrong = gameState.learnerProfile.consecutiveWrong;
    if (consecutiveWrong >= 3) {
        // Significant struggle - provide substantial support
        probs.Easy *= 1.5;
        probs.Hard *= 0.4;
        console.log(`🆘 Major struggle (${consecutiveWrong} wrong) - providing strong support`);
    } else if (consecutiveWrong === 2) {
        // Minor struggle - gentle support
        probs.Easy *= 1.2;
        probs.Hard *= 0.8;
        console.log(`⚠️ Minor struggle (${consecutiveWrong} wrong) - gentle support`);
    }
    
    // Context-aware difficulty stepping
    if (lastDiff === "Hard") {
        const lastResult = gameState.learnerProfile.difficultyHistory.slice(-1)[0];
        if (!lastResult.correct) {
            // Failed hard question - but check if it's part of a pattern
            const recentHardAttempts = gameState.learnerProfile.difficultyHistory
                .slice(-4)
                .filter(q => q.difficulty === "Hard");
            
            if (recentHardAttempts.length >= 2) {
                const hardFailureRate = recentHardAttempts.filter(q => !q.correct).length / recentHardAttempts.length;
                if (hardFailureRate >= 0.5) {
                    probs.Hard *= 0.4;
                    probs.Medium *= 1.4;
                    console.log(`📉 Hard questions too difficult (${(hardFailureRate*100).toFixed(0)}% failure) - stepping down`);
                }
            }
        }
    } else if (lastDiff === "Medium") {
        const lastResult = gameState.learnerProfile.difficultyHistory.slice(-1)[0];
        if (!lastResult.correct) {
            // Failed medium - check for pattern before stepping down
            const recentMediumAttempts = gameState.learnerProfile.difficultyHistory
                .slice(-3)
                .filter(q => q.difficulty === "Medium");
            
            if (recentMediumAttempts.length >= 2) {
                const mediumFailureRate = recentMediumAttempts.filter(q => !q.correct).length / recentMediumAttempts.length;
                if (mediumFailureRate >= 0.67) { // 2/3 failure rate
                    probs.Easy *= 1.3;
                    probs.Medium *= 0.8;
                    console.log(`📉 Medium questions challenging (${(mediumFailureRate*100).toFixed(0)}% failure) - providing easier options`);
                }
            }
        }
    }
    
    return probs;
}

function adjustForLearningVelocity(probs, profile) {
    // If improving rapidly, challenge more
    if (profile.learningVelocity > 0.3) {
        probs.Hard *= 1.2;
        probs.Easy *= 0.8;
    }
    // If declining, support more
    else if (profile.learningVelocity < -0.3) {
        probs.Easy *= 1.2;
        probs.Hard *= 0.8;
    }
    
    return probs;
}

function adjustForConfidence(probs, profile) {
    // Low confidence - be more conservative
    if (profile.confidenceLevel < 0.3) {
        probs.Easy *= 1.1;
        probs.Hard *= 0.9;
    }
    // High confidence - can take more risks
    else if (profile.confidenceLevel > 0.8) {
        probs.Hard *= 1.1;
        probs.Easy *= 0.9;
    }
    
    return probs;
}

function calculateAccuracy(results) {
    if (results.length === 0) return 0.5;
    return results.reduce((sum, correct) => sum + (correct ? 1 : 0), 0) / results.length;
}

function updateScore(correct, difficulty) {
    const profile = gameState.learnerProfile;
    const responseTime = Date.now() - profile.questionStartTime;
    
    // Update basic score and streak
    const oldScore = gameState.skillScore;
    if (correct) {
        const increment = { Easy: 2, Medium: 5, Hard: 8 }[difficulty];
        gameState.skillScore += increment;
        gameState.streak += 1;
        gameState.bestStreak = Math.max(gameState.bestStreak, gameState.streak);
        profile.consecutiveCorrect += 1;
        profile.consecutiveWrong = 0;
    } else {
        const decrement = { Easy: 2, Medium: 4, Hard: 6 }[difficulty];
        gameState.skillScore -= decrement;
        gameState.streak = 0;
        profile.consecutiveWrong += 1;
        profile.consecutiveCorrect = 0;
    }
    
    gameState.skillScore = Math.max(0, Math.min(gameState.skillScore, 100));
    gameState.lastDifficulty = difficulty;
    
    // Update personalization data
    profile.responseTime.push(responseTime);
    if (profile.responseTime.length > 10) {
        profile.responseTime.shift(); // Keep only last 10 response times
    }
    
    // Track difficulty history
    profile.difficultyHistory.push({
        difficulty: difficulty,
        correct: correct,
        responseTime: responseTime,
        scoreChange: gameState.skillScore - oldScore,
        questionText: gameState.currentQuestion ? gameState.currentQuestion.q : null,
        selectedOption: gameState.selectedOption,
        correctAnswer: gameState.currentQuestion ? gameState.currentQuestion.answer : null
    });
    if (profile.difficultyHistory.length > 15) {
        profile.difficultyHistory.shift(); // Keep last 15 questions
    }
    
    // Track accuracy by difficulty
    profile.accuracyByDifficulty[difficulty].push(correct);
    if (profile.accuracyByDifficulty[difficulty].length > 8) {
        profile.accuracyByDifficulty[difficulty].shift(); // Keep last 8 per difficulty
    }
    
    // Update learning velocity (rate of score change)
    if (profile.difficultyHistory.length >= 5) {
        const recent5 = profile.difficultyHistory.slice(-5);
        const scoreChanges = recent5.map(q => q.scoreChange);
        profile.learningVelocity = scoreChanges.reduce((a, b) => a + b, 0) / 5;
    }
    
    // Update confidence level based on recent performance stability
    updateConfidenceLevel(profile);
    
    // Adapt the adaptation rate based on performance patterns
    updateAdaptationRate(profile);
    
    // Log personalization insights
    console.log('Learner Profile Update:', {
        difficulty: difficulty,
        correct: correct,
        responseTime: responseTime,
        learningVelocity: profile.learningVelocity.toFixed(3),
        confidenceLevel: profile.confidenceLevel.toFixed(3),
        easyAccuracy: calculateAccuracy(profile.accuracyByDifficulty.Easy).toFixed(2),
        mediumAccuracy: calculateAccuracy(profile.accuracyByDifficulty.Medium).toFixed(2),
        hardAccuracy: calculateAccuracy(profile.accuracyByDifficulty.Hard).toFixed(2)
    });

    // Notify enhanced modules for additional updates
    // Priority: Hybrid RL > Pure RL > Enhanced Statistical
    if (window.PALHybridAlgorithm && typeof window.PALHybridAlgorithm.updateProfileAfterAnswer === 'function') {
        try {
            window.PALHybridAlgorithm.updateProfileAfterAnswer(gameState, correct, difficulty, responseTime);
        } catch (e) {
            console.warn('PALHybridAlgorithm.updateProfileAfterAnswer failed:', e);
        }
    } else if (window.PALRLAlgorithm && typeof window.PALRLAlgorithm.updateProfileAfterAnswer === 'function') {
        try {
            window.PALRLAlgorithm.updateProfileAfterAnswer(gameState, correct, difficulty, responseTime);
        } catch (e) {
            console.warn('PALRLAlgorithm.updateProfileAfterAnswer failed:', e);
        }
    } else if (window.PALAlgorithm && typeof window.PALAlgorithm.updateProfileAfterAnswer === 'function') {
        try {
            window.PALAlgorithm.updateProfileAfterAnswer(gameState, correct, difficulty, responseTime);
        } catch (e) {
            console.warn('PALAlgorithm.updateProfileAfterAnswer failed:', e);
        }
    }
}

function updateConfidenceLevel(profile) {
    if (profile.difficultyHistory.length < 3) return;
    
    const recent = profile.difficultyHistory.slice(-5);
    const accuracyVariance = calculateVariance(recent.map(q => q.correct ? 1 : 0));
    const responseTimeVariance = calculateVariance(recent.map(q => q.responseTime));
    
    // Lower variance = higher confidence
    const accuracyConfidence = Math.max(0, 1 - accuracyVariance * 2);
    const timingConfidence = Math.max(0, 1 - responseTimeVariance / 10000); // Normalize
    
    profile.confidenceLevel = (accuracyConfidence + timingConfidence) / 2;
}

function updateAdaptationRate(profile) {
    // Faster adaptation for consistent performers, slower for inconsistent
    const consistency = profile.confidenceLevel;
    const sessionProgress = Math.min(1, profile.difficultyHistory.length / 10);
    
    profile.adaptationRate = 0.3 + (consistency * sessionProgress * 0.4);
}

function calculateVariance(values) {
    if (values.length < 2) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    return values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
}

function applySmoothingBuffer(probs, profile) {
    // Prevent dramatic difficulty jumps by comparing to recent difficulty distribution
    if (profile.difficultyHistory.length < 3) return probs;
    
    const recentDifficulties = profile.difficultyHistory.slice(-5);
    const recentDistribution = {
        Easy: recentDifficulties.filter(q => q.difficulty === 'Easy').length / recentDifficulties.length,
        Medium: recentDifficulties.filter(q => q.difficulty === 'Medium').length / recentDifficulties.length,
        Hard: recentDifficulties.filter(q => q.difficulty === 'Hard').length / recentDifficulties.length
    };
    
    // Limit how much probabilities can change from recent pattern
    const maxChange = 0.4; // Maximum 40% change in probability
    const smoothingFactor = 0.7; // How much to blend with recent pattern
    
    probs.Easy = (probs.Easy * (1 - smoothingFactor)) + (recentDistribution.Easy * smoothingFactor);
    probs.Medium = (probs.Medium * (1 - smoothingFactor)) + (recentDistribution.Medium * smoothingFactor);
    probs.Hard = (probs.Hard * (1 - smoothingFactor)) + (recentDistribution.Hard * smoothingFactor);
    
    // Ensure no probability goes negative or exceeds reasonable bounds
    probs.Easy = Math.max(0.05, Math.min(0.8, probs.Easy));
    probs.Medium = Math.max(0.1, Math.min(0.6, probs.Medium));
    probs.Hard = Math.max(0.05, Math.min(0.7, probs.Hard));
    
    console.log('🔧 Smoothing buffer applied - preventing dramatic difficulty swings');
    
    return probs;
}

function showQuestion() {
    if (gameState.showingQuestion) return;
    
    gameState.showingQuestion = true;
    player.pauseVideo();
    
    // Start timing the question
    gameState.learnerProfile.questionStartTime = Date.now();
    
    const questionData = gameState.currentLessonData.questions[gameState.currentQuestionIndex];
    const difficulty = getQuestionDifficulty(gameState.skillScore, gameState.streak, gameState.lastDifficulty);
    const question = questionData[difficulty];
    
    gameState.currentQuestion = question;
    gameState.currentDifficulty = difficulty;
    gameState.selectedOption = null;
    
    // Log algorithm decision
    console.log('Algorithm Decision:', {
        skillScore: gameState.skillScore,
        streak: gameState.streak,
        selectedDifficulty: difficulty,
        questionIndex: gameState.currentQuestionIndex + 1,
        learningVelocity: gameState.learnerProfile.learningVelocity.toFixed(3),
        confidenceLevel: gameState.learnerProfile.confidenceLevel.toFixed(3)
    });
    
    // Update UI
    document.getElementById('questionNum').textContent = gameState.currentQuestionIndex + 1;
    document.getElementById('difficultyBadge').textContent = difficulty;
    document.getElementById('difficultyBadge').className = `difficulty-badge difficulty-${difficulty.toLowerCase()}`;
    document.getElementById('questionText').textContent = question.q;
    
    // Create option buttons
    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = '';
    
    question.options.forEach((option, index) => {
        const button = document.createElement('button');
        button.className = 'option-button';
        button.textContent = option;
        button.onclick = () => selectOption(option, button);
        optionsContainer.appendChild(button);
    });
    
    // Reset UI state
    document.getElementById('feedback').innerHTML = '';
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('submitBtn').style.display = 'inline-block';
    document.getElementById('continueBtn').style.display = 'none';
    
    // Show overlay
    document.getElementById('questionOverlay').style.display = 'flex';
}

function selectOption(option, buttonElement) {
    gameState.selectedOption = option;
    
    // Update button states
    document.querySelectorAll('.option-button').forEach(btn => {
        btn.classList.remove('selected');
    });
    buttonElement.classList.add('selected');
    
    // Enable submit button
    document.getElementById('submitBtn').disabled = false;
}

function submitAnswer() {
    if (!gameState.selectedOption) return;
    
    const correct = gameState.selectedOption === gameState.currentQuestion.answer;
    updateScore(correct, gameState.currentDifficulty);
    
    // Show feedback
    const feedbackEl = document.getElementById('feedback');
    if (correct) {
        feedbackEl.innerHTML = '✅ Correct!';
        feedbackEl.className = 'feedback correct';
    } else {
        feedbackEl.innerHTML = `❌ Wrong! Correct answer: ${gameState.currentQuestion.answer}`;
        feedbackEl.className = 'feedback incorrect';
    }
    
    // Update stats display
    updateStatsDisplay();
    
    // Hide submit button, show continue button
    document.getElementById('submitBtn').style.display = 'none';
    document.getElementById('continueBtn').style.display = 'inline-block';
}

function continueVideo() {
    gameState.showingQuestion = false;
    gameState.currentQuestionIndex++;
    
    // Hide overlay
    document.getElementById('questionOverlay').style.display = 'none';
    
    // Check if finished
    if (gameState.currentQuestionIndex >= gameState.currentLessonData.questions.length) {
        finishLesson();
    } else {
        player.playVideo();
        updateProgressDisplay();
    }
}

function finishLesson() {
    gameState.finished = true;
    stopTimeTracking();
    
    // Show completion screen
    document.getElementById('completion').style.display = 'block';
    document.getElementById('finalScore').textContent = gameState.skillScore;
    document.getElementById('finalStreak').textContent = gameState.bestStreak;
    
    // Hide video container
    document.querySelector('.video-container').style.display = 'none';

    // Emit simple evaluation metrics for the session
    try {
        const hist = gameState.learnerProfile.difficultyHistory;
        const acc = hist.length ? (hist.reduce((s, h) => s + (h.correct ? 1 : 0), 0) / hist.length) : 0;
        const avgRt = gameState.learnerProfile.responseTime.length ?
            (gameState.learnerProfile.responseTime.reduce((a,b)=>a+b,0)/gameState.learnerProfile.responseTime.length) : 0;
        const byDiff = { Easy: {n:0,c:0}, Medium:{n:0,c:0}, Hard:{n:0,c:0} };
        hist.forEach(h => { byDiff[h.difficulty].n += 1; byDiff[h.difficulty].c += (h.correct?1:0); });
        const accByDiff = {
            Easy: byDiff.Easy.n ? byDiff.Easy.c / byDiff.Easy.n : 0,
            Medium: byDiff.Medium.n ? byDiff.Medium.c / byDiff.Medium.n : 0,
            Hard: byDiff.Hard.n ? byDiff.Hard.c / byDiff.Hard.n : 0
        };
        const useEnhanced = !!(window.PALAlgorithm && typeof window.PALAlgorithm.getNextDifficulty === 'function');
        const variant = useEnhanced ? 'enhanced' : 'baseline';
        console.log('PAL Evaluation Metrics', {
            variant,
            finalScore: gameState.skillScore,
            bestStreak: gameState.bestStreak,
            overallAccuracy: acc,
            accuracyByDifficulty: accByDiff,
            avgResponseTimeMs: avgRt
        });

        // Post metrics to local collector if available
        if (window.PALSessionLogger && typeof window.PALSessionLogger.post === 'function') {
            window.PALSessionLogger.post(gameState, variant, { userAgent: navigator.userAgent }).catch(()=>{});
        }
    } catch (e) {
        console.warn('Evaluation metrics failed', e);
    }
}

function updateStatsDisplay() {
    document.getElementById('skillScore').textContent = gameState.skillScore;
    document.getElementById('streak').textContent = gameState.streak;
    document.getElementById('questionCount').textContent = 
        `${gameState.currentQuestionIndex}/${gameState.currentLessonData.questions.length}`;
    
    // Update adaptation rate display
    const adaptationPercentage = Math.round(gameState.learnerProfile.adaptationRate * 100);
    document.getElementById('adaptationRate').textContent = `${adaptationPercentage}%`;
    
    // Update analytics panel
    updateAnalyticsDisplay();
}

function updateAnalyticsDisplay() {
    const profile = gameState.learnerProfile;
    
    // Learning velocity
    document.getElementById('learningVelocity').textContent = profile.learningVelocity.toFixed(1);
    
    // Confidence level
    const confidencePercentage = Math.round(profile.confidenceLevel * 100);
    document.getElementById('confidenceLevel').textContent = `${confidencePercentage}%`;
    
    // Average response time
    if (profile.responseTime.length > 0) {
        const avgTime = profile.responseTime.reduce((a, b) => a + b, 0) / profile.responseTime.length;
        document.getElementById('avgResponseTime').textContent = `${(avgTime / 1000).toFixed(1)}s`;
    }
    
    // Accuracy by difficulty
    const easyAcc = calculateAccuracy(profile.accuracyByDifficulty.Easy);
    const mediumAcc = calculateAccuracy(profile.accuracyByDifficulty.Medium);
    const hardAcc = calculateAccuracy(profile.accuracyByDifficulty.Hard);
    
    document.getElementById('easyAccuracy').textContent = profile.accuracyByDifficulty.Easy.length > 0 
        ? `${Math.round(easyAcc * 100)}%` : '--';
    document.getElementById('mediumAccuracy').textContent = profile.accuracyByDifficulty.Medium.length > 0 
        ? `${Math.round(mediumAcc * 100)}%` : '--';
    document.getElementById('hardAccuracy').textContent = profile.accuracyByDifficulty.Hard.length > 0 
        ? `${Math.round(hardAcc * 100)}%` : '--';
    
    // Update RL Analytics
    updateRLAnalytics();
}

function updateRLAnalytics() {
    const rlPanel = document.getElementById('rlAnalyticsPanel');
    if (!rlPanel) return;
    
    // Show RL panel if any RL algorithm is active
    const hasRL = window.PALHybridAlgorithm || window.PALRLAlgorithm;
    rlPanel.style.display = hasRL ? 'block' : 'none';
    
    if (!hasRL) return;
    
    // Update algorithm type
    let algorithmType = 'Statistical';
    if (window.PALHybridAlgorithm) {
        algorithmType = 'Hybrid RL';
    } else if (window.PALRLAlgorithm) {
        algorithmType = 'Pure RL';
    }
    document.getElementById('algorithmType').textContent = algorithmType;
    
    // Update RL-specific metrics
    if (window.PALHybridAlgorithm) {
        const hybridStats = window.PALHybridAlgorithm.getHybridStats();
        const explanation = window.PALHybridAlgorithm.getDecisionExplanation();
        
        document.getElementById('totalDecisions').textContent = hybridStats.decisionCount;
        document.getElementById('blendingWeights').textContent = hybridStats.currentRLWeight;
        document.getElementById('lastDecision').textContent = explanation ? explanation.finalDecision : '--';
        document.getElementById('decisionReasoning').textContent = explanation ? explanation.reasoning : '--';
        
        if (explanation && explanation.rlDetails) {
            document.getElementById('qValues').textContent = 
                `E:${explanation.rlDetails.qValues.Easy} M:${explanation.rlDetails.qValues.Medium} H:${explanation.rlDetails.qValues.Hard}`;
            document.getElementById('explorationRate').textContent = explanation.rlDetails.explorationRate;
        } else {
            document.getElementById('qValues').textContent = '--';
            document.getElementById('explorationRate').textContent = '--';
        }
    } else if (window.PALRLAlgorithm) {
        const rlStats = window.PALRLAlgorithm.getLearningStats();
        const explanation = window.PALRLAlgorithm.getDecisionExplanation();
        
        document.getElementById('totalDecisions').textContent = rlStats.totalDecisions;
        document.getElementById('explorationRate').textContent = rlStats.explorationRate;
        document.getElementById('blendingWeights').textContent = 'N/A';
        document.getElementById('lastDecision').textContent = explanation ? explanation.selectedDifficulty : '--';
        document.getElementById('decisionReasoning').textContent = explanation ? explanation.reasoning : '--';
        
        if (explanation) {
            document.getElementById('qValues').textContent = 
                `E:${explanation.qValues.Easy} M:${explanation.qValues.Medium} H:${explanation.qValues.Hard}`;
        } else {
            document.getElementById('qValues').textContent = '--';
        }
    }
}

function updateProgressDisplay() {
    const progress = (gameState.currentQuestionIndex / gameState.currentLessonData.questions.length) * 100;
    document.getElementById('progressFill').style.width = `${progress}%`;
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    updateStatsDisplay();
    updateProgressDisplay();
    // Mode control via URL (?mode=baseline|enhanced)
    const params = new URLSearchParams(window.location.search);
    const mode = (params.get('mode') || 'auto').toLowerCase();
    // Reflect in radio controls
    const autoEl = document.getElementById('modeAuto');
    const baseEl = document.getElementById('modeBaseline');
    const enhEl = document.getElementById('modeEnhanced');
    if (autoEl && baseEl && enhEl) {
        if (mode === 'baseline') baseEl.checked = true;
        else if (mode === 'enhanced') enhEl.checked = true;
        else autoEl.checked = true;
        // Wire change handlers
        [autoEl, baseEl, enhEl].forEach(el => {
            el.addEventListener('change', () => {
                const selected = document.querySelector('input[name="mode"]:checked').value;
                const url = new URL(window.location.href);
                if (selected === 'auto') url.searchParams.delete('mode');
                else url.searchParams.set('mode', selected);
                window.location.href = url.toString();
            });
        });
    }
    // If baseline requested, temporarily disable external algorithm
    if (mode === 'baseline') window.PALAlgorithm = null;
});
