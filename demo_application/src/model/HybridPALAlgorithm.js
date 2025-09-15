// Hybrid Configuration
const HYBRID_CONFIG = {
  initialRLWeight: 0.3, // Start with 30% RL influence
  maxRLWeight: 0.8, // Maximum 80% RL influence
  rlWeightIncrement: 0.02, // Increase RL weight by 2% per session
  minDecisionsForRL: 10, // Minimum decisions before using RL
  confidenceThreshold: 0.6, // Confidence threshold for RL dominance
};

// Hybrid Algorithm Class
export class HybridPALAlgorithm {
  static #hybridPALAlgorithm;

  constructor() {
    this.rlWeight = HYBRID_CONFIG.initialRLWeight;
    this.decisionCount = 0;
    this.lastDecision = null;
    this.blendingHistory = [];
  }

  static getInstance() {
    if (!this.#hybridPALAlgorithm) {
      this.#hybridPALAlgorithm = new HybridPALAlgorithm();
    }
    return this.#hybridPALAlgorithm;
  }

  // Get next difficulty using hybrid approach
  getNextDifficulty(ctx) {
    this.decisionCount++;

    // Determine blending weights
    const weights = this.calculateBlendingWeights(ctx.state);

    // Get predictions from both algorithms
    const statisticalPred = this.getStatisticalPrediction(ctx.state);
    const rlPred = this.getRLPrediction(ctx.state);

    // Blend predictions
    const finalPrediction = this.blendPredictions(
      statisticalPred,
      rlPred,
      weights
    );

    // Store decision for interpretability
    this.lastDecision = {
      statisticalPrediction: statisticalPred,
      rlPrediction: rlPred,
      finalPrediction,
      weights,
      decisionCount: this.decisionCount,
      timestamp: Date.now(),
      reasoning: this.generateBlendingReasoning(
        weights,
        statisticalPred,
        rlPred,
        finalPrediction
      ),
    };

    this.blendingHistory.push(this.lastDecision);
    if (this.blendingHistory.length > 100) {
      this.blendingHistory.shift();
    }

    // Log hybrid decision
    console.log("🔄 Hybrid Decision:", {
      statistical: statisticalPred,
      rl: rlPred,
      final: finalPrediction,
      weights: `Statistical: ${(weights.statistical * 100).toFixed(1)}%, RL: ${(
        weights.rl * 100
      ).toFixed(1)}%`,
      reasoning: this.lastDecision.reasoning,
    });

    return finalPrediction;
  }

  // Calculate blending weights based on system state
  calculateBlendingWeights(state) {
    let rlWeight = this.rlWeight;

    // Adjust based on decision count
    if (this.decisionCount < HYBRID_CONFIG.minDecisionsForRL) {
      rlWeight = 0; // Use only statistical for first few decisions
    } else {
      // Gradually increase RL weight
      rlWeight = Math.min(
        HYBRID_CONFIG.maxRLWeight,
        HYBRID_CONFIG.initialRLWeight +
          (this.decisionCount - HYBRID_CONFIG.minDecisionsForRL) *
            HYBRID_CONFIG.rlWeightIncrement
      );
    }

    // Adjust based on confidence
    const confidence = state.learnerProfile.confidenceLevel || 0.5;
    if (confidence > HYBRID_CONFIG.confidenceThreshold) {
      rlWeight = Math.min(HYBRID_CONFIG.maxRLWeight, rlWeight * 1.2);
    }

    // Adjust based on learning progress
    const learningVelocity = state.learnerProfile.learningVelocity || 0;
    if (Math.abs(learningVelocity) > 0.3) {
      rlWeight = Math.min(HYBRID_CONFIG.maxRLWeight, rlWeight * 1.1);
    }

    this.rlWeight = rlWeight;

    return {
      statistical: 1 - rlWeight,
      rl: rlWeight,
    };
  }

  // Get statistical prediction (using existing enhanced algorithm)
  getStatisticalPrediction(state) {
    if (window.PALAlgorithm && window.PALAlgorithm.getNextDifficulty) {
      return window.PALAlgorithm.getNextDifficulty({ state });
    }

    // Fallback to simple statistical approach
    const score = state.skillScore;
    if (score <= 30) return "easy";
    if (score <= 70) return "medium";
    return "hard";
  }

  // Get RL prediction
  getRLPrediction(state) {
    if (window.PALRLAlgorithm && window.PALRLAlgorithm.getNextDifficulty) {
      return window.PALRLAlgorithm.getNextDifficulty({ state });
    }

    // Fallback to random if RL not available
    const difficulties = ["easy", "medium", "hard"];
    return difficulties[Math.floor(Math.random() * difficulties.length)];
  }

  // Blend predictions using weighted approach
  blendPredictions(statisticalPred, rlPred, weights) {
    // If both predictions are the same, return that
    if (statisticalPred === rlPred) {
      return statisticalPred;
    }

    // Use weighted random selection
    const rand = Math.random();
    if (rand < weights.statistical) {
      return statisticalPred;
    } else {
      return rlPred;
    }
  }

  // Generate human-readable reasoning for blending decision
  generateBlendingReasoning(weights, statisticalPred, rlPred, finalPrediction) {
    const reasons = [];

    if (weights.rl < 0.1) {
      reasons.push("Using statistical approach (early learning phase)");
    } else if (weights.rl > 0.7) {
      reasons.push("RL-dominant decision (high confidence)");
    } else {
      reasons.push(
        `Blended decision (${(weights.statistical * 100).toFixed(
          0
        )}% statistical, ${(weights.rl * 100).toFixed(0)}% RL)`
      );
    }

    if (statisticalPred !== rlPred) {
      reasons.push(`Statistical: ${statisticalPred}, RL: ${rlPred}`);
      if (finalPrediction === rlPred) {
        reasons.push("RL prediction selected");
      } else {
        reasons.push("Statistical prediction selected");
      }
    } else {
      reasons.push(`Both algorithms agree: ${finalPrediction}`);
    }

    return reasons.join("; ");
  }

  // Update both algorithms
  updateProfileAfterAnswer(state, correct, difficulty, responseTime) {
    // Update statistical algorithm
    if (window.PALAlgorithm && window.PALAlgorithm.updateProfileAfterAnswer) {
      window.PALAlgorithm.updateProfileAfterAnswer(
        state,
        correct,
        difficulty,
        responseTime
      );
    }

    // Update RL algorithm
    if (
      window.PALRLAlgorithm &&
      window.PALRLAlgorithm.updateProfileAfterAnswer
    ) {
      window.PALRLAlgorithm.updateProfileAfterAnswer(
        state,
        correct,
        difficulty,
        responseTime
      );
    }
  }

  // Get comprehensive decision explanation
  getDecisionExplanation() {
    if (!this.lastDecision) return null;

    const explanation = {
      finalDecision: this.lastDecision.finalPrediction,
      blendingWeights: {
        statistical: `${(this.lastDecision.weights.statistical * 100).toFixed(
          1
        )}%`,
        rl: `${(this.lastDecision.weights.rl * 100).toFixed(1)}%`,
      },
      predictions: {
        statistical: this.lastDecision.statisticalPrediction,
        rl: this.lastDecision.rlPrediction,
      },
      reasoning: this.lastDecision.reasoning,
      decisionCount: this.decisionCount,
      timestamp: new Date(this.lastDecision.timestamp).toLocaleTimeString(),
    };

    // Add RL-specific explanations if available
    if (window.PALRLAlgorithm && window.PALRLAlgorithm.getDecisionExplanation) {
      explanation.rlDetails = window.PALRLAlgorithm.getDecisionExplanation();
    }

    return explanation;
  }

  // Get hybrid learning statistics
  getHybridStats() {
    const stats = {
      decisionCount: this.decisionCount,
      currentRLWeight: `${(this.rlWeight * 100).toFixed(1)}%`,
      blendingHistory: this.blendingHistory.slice(-10).map((d) => ({
        decision: d.finalPrediction,
        weights: `${(d.weights.statistical * 100).toFixed(0)}/${(
          d.weights.rl * 100
        ).toFixed(0)}`,
        reasoning: d.reasoning.split("; ")[0],
      })),
    };

    // Add RL stats if available
    if (window.PALRLAlgorithm && window.PALRLAlgorithm.getLearningStats) {
      stats.rlStats = window.PALRLAlgorithm.getLearningStats();
    }

    return stats;
  }

  // Reset hybrid algorithm
  reset() {
    this.rlWeight = HYBRID_CONFIG.initialRLWeight;
    this.decisionCount = 0;
    this.lastDecision = null;
    this.blendingHistory = [];

    // Reset RL agent if available
    if (window.PALRLAlgorithm && window.PALRLAlgorithm.resetAgent) {
      window.PALRLAlgorithm.resetAgent();
    }
  }
}
