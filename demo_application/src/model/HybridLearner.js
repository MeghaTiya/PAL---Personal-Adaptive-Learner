import { HybridPALAlgorithm } from "./HybridPALAlgorithm";

/**
 * Creates a Hybrid Learner
 */
export class HybridLearner {
  static #hybridLearner;
  #listeners = [];
  #gameState;
  #learner;

  /**
   * Creates a Hybrid Learner
   */
  constructor() {
    this.#gameState = {
      skillScore: 50,
      streak: 0,
      bestStreak: 0,
      lastDifficulty: "easy",
      currentQuestionIndex: 0,
      showingQuestion: false,
      finished: false,
      selectedOption: null,
      currentQuestion: null,
      currentDifficulty: "medium",
      selectedLessonIndex: 0,

      // Enhanced personalization data
      learnerProfile: {
        responseTime: [], // Track how long user takes to answer
        difficultyHistory: [], // Track difficulty of last N questions
        accuracyByDifficulty: { easy: [], medium: [], hard: [] }, // Track accuracy per difficulty
        consecutiveCorrect: 0,
        consecutiveWrong: 0,
        preferredDifficulty: null, // Learned preference
        adaptationRate: 0.5, // How quickly to adapt (0-1)
        confidenceLevel: 0.5, // Confidence in current skill assessment
        learningVelocity: 0, // Rate of improvement/decline
        sessionStartTime: Date.now(),
        questionStartTime: null,
      },
    };
    this.#listeners = [];
    this.#learner = HybridPALAlgorithm.getInstance();
    this.#learner.reset(); // Start with a fresh state
    const firstDifficulty = this.#learner.getNextDifficulty({ state: this.#gameState });
    console.log(firstDifficulty);
  }

  /**
   * Returns singleton of Hybrid Learner
   * @returns Singleton of Hybrid Learner
   */
  static getInstance() {
    if (!this.#hybridLearner) {
      this.#hybridLearner = new HybridLearner();
    }
    return this.#hybridLearner;
  }

  subscribe(listener) {
    this.#listeners.push(listener);
  }

  unsubscribe(listener) {
    this.#listeners = this.#listeners.filter((l) => l !== listener);
  }

  notify() {
    this.#listeners.forEach((fn) => fn());
  }

  startQuestionTimer() {
    this.#gameState.learnerProfile.questionStartTime = Date.now();
  }

  /**
   * Gets next difficulty using HybridPALAlgorithm
   * @returns Next difficulty
   */
  getNextDifficulty() {
    const nextDifficulty = this.#learner.getNextDifficulty({
      state: this.#gameState,
    });
    return nextDifficulty;
  }

  /**
   * Updates HybridPALAlgorithm based on if user's answer was correct
   * @param {boolean} correct Was user's answer correct
   */
  handleAnswer(correct) {
    const updated = this.updateScore(correct, this.#gameState.currentDifficulty);
    this.notify();
  }

  updateScore(correct, difficulty) {
    const profile = this.#gameState.learnerProfile;
    console.log("updateScore called with:", { correct, difficulty, profile });
    const responseTime = Date.now() - profile.questionStartTime;

    // Update basic score and streak
    const oldScore = this.#gameState.skillScore;
    if (correct) {
      const increment = { easy: 2, medium: 5, hard: 8 }[difficulty];
      this.#gameState.skillScore += increment;
      this.#gameState.streak += 1;
      this.#gameState.bestStreak = Math.max(this.#gameState.bestStreak, this.#gameState.streak);
      profile.consecutiveCorrect += 1;
      profile.consecutiveWrong = 0;
    } else {
      const decrement = { easy: 2, medium: 4, hard: 6 }[difficulty];
      this.#gameState.skillScore -= decrement;
      this.#gameState.streak = 0;
      profile.consecutiveWrong += 1;
      profile.consecutiveCorrect = 0;
    }

    this.#gameState.skillScore = Math.max(0, Math.min(this.#gameState.skillScore, 100));
    this.#gameState.lastDifficulty = difficulty;

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
      scoreChange: this.#gameState.skillScore - oldScore,
      questionText: this.#gameState.currentQuestion
        ? this.#gameState.currentQuestion.q
        : null,
      selectedOption: this.#gameState.selectedOption,
      correctAnswer: this.#gameState.currentQuestion
        ? this.#gameState.currentQuestion.answer
        : null,
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
      const scoreChanges = recent5.map((q) => q.scoreChange);
      profile.learningVelocity = scoreChanges.reduce((a, b) => a + b, 0) / 5;
    }

    // Update confidence level based on recent performance stability
    this.updateConfidenceLevel(profile);

    // Adapt the adaptation rate based on performance patterns
    this.updateAdaptationRate(profile);

    // Log personalization insights
    console.log("Learner Profile Update:", {
      difficulty: difficulty,
      correct: correct,
      responseTime: responseTime,
      learningVelocity: profile.learningVelocity.toFixed(3),
      confidenceLevel: profile.confidenceLevel.toFixed(3),
      easyAccuracy: this.calculateAccuracy(
        profile.accuracyByDifficulty.easy
      ).toFixed(2),
      mediumAccuracy: this.calculateAccuracy(
        profile.accuracyByDifficulty.medium
      ).toFixed(2),
      hardAccuracy: this.calculateAccuracy(
        profile.accuracyByDifficulty.hard
      ).toFixed(2),
    });

    // Notify enhanced modules for additional updates
    // Priority: Hybrid RL > Pure RL > Enhanced Statistical
    if (
      window.PALHybridAlgorithm &&
      typeof window.PALHybridAlgorithm.updateProfileAfterAnswer === "function"
    ) {
      try {
        window.PALHybridAlgorithm.updateProfileAfterAnswer(
          this.#gameState,
          correct,
          difficulty,
          responseTime
        );
      } catch (e) {
        console.warn("PALHybridAlgorithm.updateProfileAfterAnswer failed:", e);
      }
    } else if (
      window.PALRLAlgorithm &&
      typeof window.PALRLAlgorithm.updateProfileAfterAnswer === "function"
    ) {
      try {
        window.PALRLAlgorithm.updateProfileAfterAnswer(
          this.#gameState,
          correct,
          difficulty,
          responseTime
        );
      } catch (e) {
        console.warn("PALRLAlgorithm.updateProfileAfterAnswer failed:", e);
      }
    } else if (
      window.PALAlgorithm &&
      typeof window.PALAlgorithm.updateProfileAfterAnswer === "function"
    ) {
      try {
        window.PALAlgorithm.updateProfileAfterAnswer(
          this.#gameState,
          correct,
          difficulty,
          responseTime
        );
      } catch (e) {
        console.warn("PALAlgorithm.updateProfileAfterAnswer failed:", e);
      }
    }
  }

  getQuestionDifficulty(score, streak, lastDiff) {
    const profile = this.#gameState.learnerProfile;

    // Base probabilities based on skill score
    let probs = this.calculateBaseProbabilities(score);

    // Adjust based on recent performance
    probs = this.adjustForRecentPerformance(probs, profile);

    // Adjust based on response time patterns
    probs = this.adjustForResponseTime(probs, profile);

    // Adjust based on accuracy patterns
    probs = this.adjustForAccuracyPatterns(probs, profile);

    // Adjust based on streak and momentum
    probs = this.adjustForStreakMomentum(probs, streak, lastDiff);

    // Adjust for learning velocity (improvement/decline trend)
    probs = this.adjustForLearningVelocity(probs, profile);

    // Apply confidence-based fine-tuning
    probs = this.adjustForConfidence(probs, profile);

    // STABILITY SYSTEM: Prevent wild difficulty swings
    probs = this.applySmoothingBuffer(probs, profile);

    // Ensure probabilities sum to 1
    const total = probs.easy + probs.medium + probs.hard;
    probs.easy /= total;
    probs.medium /= total;
    probs.hard /= total;

    // Log the algorithm's reasoning
    console.log("🤖 Algorithm Decision Process:", {
      finalProbabilities: {
        easy: (probs.easy * 100).toFixed(1) + "%",
        medium: (probs.medium * 100).toFixed(1) + "%",
        hard: (probs.hard * 100).toFixed(1) + "%",
      },
      recentAccuracy:
        profile.difficultyHistory.length > 0
          ? `${(
            (profile.difficultyHistory
              .slice(-3)
              .reduce((sum, item) => sum + (item.correct ? 1 : 0), 0) /
              Math.min(3, profile.difficultyHistory.length)) *
            100
          ).toFixed(0)}%`
          : "N/A",
      confidence: `${(profile.confidenceLevel * 100).toFixed(0)}%`,
      learningVelocity: profile.learningVelocity.toFixed(2),
    });

    // Weighted random selection
    // Priority: Hybrid RL > Pure RL > Enhanced Statistical > Fallback Statistical
    if (
      window.PALHybridAlgorithm &&
      typeof window.PALHybridAlgorithm.getNextDifficulty === "function"
    ) {
      try {
        return window.PALHybridAlgorithm.getNextDifficulty({
          state: this.#gameState,
        });
      } catch (e) {
        console.warn(
          "PALHybridAlgorithm.getNextDifficulty failed, falling back:",
          e
        );
      }
    }
    if (
      window.PALRLAlgorithm &&
      typeof window.PALRLAlgorithm.getNextDifficulty === "function"
    ) {
      try {
        return window.PALRLAlgorithm.getNextDifficulty({ state: this.#gameState });
      } catch (e) {
        console.warn(
          "PALRLAlgorithm.getNextDifficulty failed, falling back:",
          e
        );
      }
    }
    if (
      window.PALAlgorithm &&
      typeof window.PALAlgorithm.getNextDifficulty === "function"
    ) {
      try {
        return window.PALAlgorithm.getNextDifficulty({ state: this.#gameState });
      } catch (e) {
        console.warn("PALAlgorithm.getNextDifficulty failed, falling back:", e);
      }
    }
    // Fallback: sample from computed probs
    const rand = Math.random();
    let cumulative = 0;
    for (const [difficulty, prob] of Object.entries(probs)) {
      cumulative += prob;
      if (rand <= cumulative) return difficulty;
    }
    return "easy";
  }

  updateConfidenceLevel(profile) {
    if (profile.difficultyHistory.length < 3) return;

    const recent = profile.difficultyHistory.slice(-5);
    const accuracyVariance = this.calculateVariance(
      recent.map((q) => (q.correct ? 1 : 0))
    );
    const responseTimeVariance = this.calculateVariance(
      recent.map((q) => q.responseTime)
    );

    // Lower variance = higher confidence
    const accuracyConfidence = Math.max(0, 1 - accuracyVariance * 2);
    const timingConfidence = Math.max(0, 1 - responseTimeVariance / 10000); // Normalize

    profile.confidenceLevel = (accuracyConfidence + timingConfidence) / 2;
  }

  updateAdaptationRate(profile) {
    // Faster adaptation for consistent performers, slower for inconsistent
    const consistency = profile.confidenceLevel;
    const sessionProgress = Math.min(1, profile.difficultyHistory.length / 10);

    profile.adaptationRate = 0.3 + consistency * sessionProgress * 0.4;
  }

  calculateAccuracy(results) {
    if (results.length === 0) return 0.5;
    return (
      results.reduce((sum, correct) => sum + (correct ? 1 : 0), 0) /
      results.length
    );
  }

  calculateBaseProbabilities(score) {
    if (score <= 20) {
      return { easy: 0.85, medium: 0.12, hard: 0.03 };
    } else if (score <= 35) {
      return { easy: 0.75, medium: 0.2, hard: 0.05 };
    } else if (score <= 50) {
      return { easy: 0.55, medium: 0.35, hard: 0.1 };
    } else if (score <= 65) {
      return { easy: 0.35, medium: 0.45, hard: 0.2 };
    } else if (score <= 80) {
      return { easy: 0.2, medium: 0.45, hard: 0.35 };
    } else if (score <= 90) {
      return { easy: 0.1, medium: 0.35, hard: 0.55 };
    } else {
      return { easy: 0.05, medium: 0.25, hard: 0.7 };
    }
  }

  adjustForRecentPerformance(probs, profile) {
    const recentHistory = profile.difficultyHistory.slice(-4); // Look at last 4 instead of 3
    if (recentHistory.length === 0) return probs;

    const recentAccuracy =
      recentHistory.reduce((sum, item) => sum + (item.correct ? 1 : 0), 0) /
      recentHistory.length;

    // STABILITY BUFFER: More conservative thresholds
    if (recentAccuracy >= 0.75 && recentHistory.length >= 4) {
      // Very high recent performance - gradual difficulty increase
      const performanceBonus = 1 + (recentAccuracy - 0.75) * 0.8; // Less aggressive
      probs.easy *= 0.85;
      probs.medium *= 0.95;
      probs.hard *= performanceBonus;
      console.log(
        `🎯 Strong recent performance (${(recentAccuracy * 100).toFixed(
          0
        )}%) - gradual challenge increase`
      );
    } else if (recentAccuracy <= 0.25 && recentHistory.length >= 3) {
      // Very poor recent performance - provide support but not immediately drastic
      probs.easy *= 1.3;
      probs.medium *= 0.9;
      probs.hard *= 0.7;
      console.log(
        `📉 Weak recent performance (${(recentAccuracy * 100).toFixed(
          0
        )}%) - providing measured support`
      );
    } else if (recentAccuracy >= 0.25 && recentAccuracy < 0.75) {
      // LEARNING ZONE: 25-75% accuracy - maintain current difficulty for practice
      console.log(
        `⚖️ Learning zone (${(recentAccuracy * 100).toFixed(
          0
        )}%) - maintaining current difficulty`
      );
      // Slight bias toward their current performance level
      if (recentAccuracy > 0.5) {
        probs.medium *= 1.05; // Slight preference for medium
      }
    }

    return probs;
  }

  adjustForResponseTime(probs, profile) {
    if (profile.responseTime.length < 2) return probs;

    const avgResponseTime =
      profile.responseTime.reduce((a, b) => a + b, 0) /
      profile.responseTime.length;
    const recentResponseTime =
      profile.responseTime.slice(-2).reduce((a, b) => a + b, 0) / 2;

    // If answering much faster than average, might be too easy
    if (recentResponseTime < avgResponseTime * 0.6) {
      probs.easy *= 0.8;
      probs.hard *= 1.2;
    }
    // If answering much slower, might be too hard
    else if (recentResponseTime > avgResponseTime * 1.5) {
      probs.easy *= 1.2;
      probs.hard *= 0.8;
    }

    return probs;
  }

  adjustForAccuracyPatterns(probs, profile) {
    const easyAccuracy = this.calculateAccuracy(profile.accuracyByDifficulty.easy);
    const mediumAccuracy = this.calculateAccuracy(
      profile.accuracyByDifficulty.medium
    );
    const hardAccuracy = this.calculateAccuracy(profile.accuracyByDifficulty.hard);

    const easyCount = profile.accuracyByDifficulty.easy.length;
    const mediumCount = profile.accuracyByDifficulty.medium.length;
    const hardCount = profile.accuracyByDifficulty.hard.length;

    // BUFFER SYSTEM: Need more attempts before making major adjustments

    // Easy questions: Only reduce after mastery is clearly demonstrated
    if (easyAccuracy >= 0.85 && easyCount >= 4) {
      const masteryLevel = Math.min(1.5, 1 + (easyAccuracy - 0.85) * 2);
      probs.easy *= 0.8 / masteryLevel;
      probs.medium *= 1.1;
      console.log(
        `🎯 Easy mastery detected (${(easyAccuracy * 100).toFixed(
          0
        )}% over ${easyCount} questions)`
      );
    }

    // Medium questions: More nuanced adjustment with buffer
    if (mediumCount >= 3) {
      if (mediumAccuracy <= 0.25) {
        // Very poor performance - provide significant support but not immediately
        probs.easy *= 1.4;
        probs.medium *= 0.7;
        probs.hard *= 0.5;
        console.log(
          `📉 Medium struggling detected (${(mediumAccuracy * 100).toFixed(
            0
          )}% over ${mediumCount} questions) - providing support`
        );
      } else if (mediumAccuracy >= 0.8 && mediumCount >= 4) {
        // Strong performance - gradually increase challenge
        probs.medium *= 0.9;
        probs.hard *= 1.2;
        console.log(
          `📈 Medium mastery detected (${(mediumAccuracy * 100).toFixed(
            0
          )}% over ${mediumCount} questions) - increasing challenge`
        );
      }
      // BUFFER ZONE: 25%-80% accuracy = no major changes, let them practice
      else if (mediumAccuracy > 0.25 && mediumAccuracy < 0.8) {
        console.log(
          `⚖️ Medium practice zone (${(mediumAccuracy * 100).toFixed(
            0
          )}% over ${mediumCount} questions) - maintaining difficulty`
        );
      }
    }

    // Hard questions: Conservative approach with larger buffer
    if (hardCount >= 3) {
      if (hardAccuracy >= 0.75) {
        // Excellent performance on hard - they're ready for more
        probs.hard *= 1.25;
        probs.easy *= 0.85;
        console.log(
          `🔥 Hard mastery detected (${(hardAccuracy * 100).toFixed(
            0
          )}% over ${hardCount} questions)`
        );
      } else if (hardAccuracy <= 0.2 && hardCount >= 4) {
        // Really struggling with hard questions - step back gradually
        probs.hard *= 0.6;
        probs.medium *= 1.2;
        console.log(
          `🛡️ Hard difficulty too high (${(hardAccuracy * 100).toFixed(
            0
          )}% over ${hardCount} questions) - reducing`
        );
      }
    }

    return probs;
  }

  adjustForStreakMomentum(probs, streak, lastDiff) {
    // ENHANCED BUFFER SYSTEM FOR STREAKS

    // Positive momentum: Build up gradually
    if (streak >= 5) {
      const streakBonus = Math.min(1.4, 1 + (streak - 4) * 0.08); // More gradual increase
      probs.hard *= streakBonus;
      probs.easy *= 2 - streakBonus;
      console.log(
        `🔥 Hot streak (${streak}) - difficulty boost: ${streakBonus.toFixed(
          2
        )}x`
      );
    } else if (streak >= 3) {
      // Moderate streak - small boost
      probs.hard *= 1.1;
      probs.easy *= 0.95;
      console.log(`📈 Good streak (${streak}) - slight difficulty increase`);
    }

    // Negative momentum: Provide buffer before major changes
    const consecutiveWrong = this.#gameState.learnerProfile.consecutiveWrong;
    if (consecutiveWrong >= 3) {
      // Significant struggle - provide substantial support
      probs.easy *= 1.5;
      probs.hard *= 0.4;
      console.log(
        `🆘 Major struggle (${consecutiveWrong} wrong) - providing strong support`
      );
    } else if (consecutiveWrong === 2) {
      // Minor struggle - gentle support
      probs.easy *= 1.2;
      probs.hard *= 0.8;
      console.log(
        `⚠️ Minor struggle (${consecutiveWrong} wrong) - gentle support`
      );
    }

    // Context-aware difficulty stepping
    if (lastDiff === "hard") {
      const lastResult =
        this.#gameState.learnerProfile.difficultyHistory.slice(-1)[0];
      if (!lastResult.correct) {
        // Failed hard question - but check if it's part of a pattern
        const recentHardAttempts = this.#gameState.learnerProfile.difficultyHistory
          .slice(-4)
          .filter((q) => q.difficulty === "hard");

        if (recentHardAttempts.length >= 2) {
          const hardFailureRate =
            recentHardAttempts.filter((q) => !q.correct).length /
            recentHardAttempts.length;
          if (hardFailureRate >= 0.5) {
            probs.hard *= 0.4;
            probs.medium *= 1.4;
            console.log(
              `📉 Hard questions too difficult (${(
                hardFailureRate * 100
              ).toFixed(0)}% failure) - stepping down`
            );
          }
        }
      }
    } else if (lastDiff === "medium") {
      const lastResult =
        this.#gameState.learnerProfile.difficultyHistory.slice(-1)[0];
      if (!lastResult.correct) {
        // Failed medium - check for pattern before stepping down
        const recentMediumAttempts = this.#gameState.learnerProfile.difficultyHistory
          .slice(-3)
          .filter((q) => q.difficulty === "medium");

        if (recentMediumAttempts.length >= 2) {
          const mediumFailureRate =
            recentMediumAttempts.filter((q) => !q.correct).length /
            recentMediumAttempts.length;
          if (mediumFailureRate >= 0.67) {
            // 2/3 failure rate
            probs.easy *= 1.3;
            probs.medium *= 0.8;
            console.log(
              `📉 Medium questions challenging (${(
                mediumFailureRate * 100
              ).toFixed(0)}% failure) - providing easier options`
            );
          }
        }
      }
    }

    return probs;
  }

  adjustForLearningVelocity(probs, profile) {
    // If improving rapidly, challenge more
    if (profile.learningVelocity > 0.3) {
      probs.hard *= 1.2;
      probs.easy *= 0.8;
    }
    // If declining, support more
    else if (profile.learningVelocity < -0.3) {
      probs.easy *= 1.2;
      probs.hard *= 0.8;
    }

    return probs;
  }

  adjustForConfidence(probs, profile) {
    // Low confidence - be more conservative
    if (profile.confidenceLevel < 0.3) {
      probs.easy *= 1.1;
      probs.hard *= 0.9;
    }
    // High confidence - can take more risks
    else if (profile.confidenceLevel > 0.8) {
      probs.hard *= 1.1;
      probs.easy *= 0.9;
    }

    return probs;
  }

  applySmoothingBuffer(probs, profile) {
    // Prevent dramatic difficulty jumps by comparing to recent difficulty distribution
    if (profile.difficultyHistory.length < 3) return probs;

    const recentDifficulties = profile.difficultyHistory.slice(-5);
    const recentDistribution = {
      easy:
        recentDifficulties.filter((q) => q.difficulty === "easy").length /
        recentDifficulties.length,
      medium:
        recentDifficulties.filter((q) => q.difficulty === "medium").length /
        recentDifficulties.length,
      hard:
        recentDifficulties.filter((q) => q.difficulty === "hard").length /
        recentDifficulties.length,
    };

    // Limit how much probabilities can change from recent pattern
    const maxChange = 0.4; // Maximum 40% change in probability
    const smoothingFactor = 0.7; // How much to blend with recent pattern

    probs.easy =
      probs.easy * (1 - smoothingFactor) +
      recentDistribution.easy * smoothingFactor;
    probs.medium =
      probs.medium * (1 - smoothingFactor) +
      recentDistribution.medium * smoothingFactor;
    probs.hard =
      probs.hard * (1 - smoothingFactor) +
      recentDistribution.hard * smoothingFactor;

    // Ensure no probability goes negative or exceeds reasonable bounds
    probs.easy = Math.max(0.05, Math.min(0.8, probs.easy));
    probs.medium = Math.max(0.1, Math.min(0.6, probs.medium));
    probs.hard = Math.max(0.05, Math.min(0.7, probs.hard));

    console.log(
      "🔧 Smoothing buffer applied - preventing dramatic difficulty swings"
    );

    return probs;
  }

  calculateVariance(values) {
    if (values.length < 2) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    return (
      values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) /
      values.length
    );
  }
}
