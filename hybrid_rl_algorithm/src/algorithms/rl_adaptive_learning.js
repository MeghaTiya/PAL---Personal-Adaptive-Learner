// PAL RL-Enhanced Algorithm: Multi-Armed Bandit with Interpretable Decisions
// Exposes window.PALRLAlgorithm with:
// - getNextDifficulty({ state })
// - updateProfileAfterAnswer(state, correct, difficulty, responseTime)
// - getDecisionExplanation() - for interpretability

(function () {
    'use strict';

    // RL Configuration
    const RL_CONFIG = {
        learningRate: 0.1,
        explorationRate: 0.15,
        explorationDecay: 0.995,
        minExplorationRate: 0.05,
        rewardDiscount: 0.9,
        memorySize: 1000,
        updateFrequency: 5
    };

    // Difficulty levels and their indices
    const DIFFICULTIES = ['Easy', 'Medium', 'Hard'];
    const DIFFICULTY_INDICES = { 'Easy': 0, 'Medium': 1, 'Hard': 2 };

    // RL Agent Class
    class PALRLAgent {
        constructor() {
            this.qValues = [0, 0, 0]; // Q-values for Easy, Medium, Hard
            this.actionCounts = [0, 0, 0]; // Number of times each action was taken
            this.explorationRate = RL_CONFIG.explorationRate;
            this.memory = [];
            this.updateCounter = 0;
            this.lastDecision = null;
            this.decisionHistory = [];
        }

        // State encoding: convert learner profile to numerical state
        encodeState(state) {
            const profile = state.learnerProfile;
            const history = profile.difficultyHistory || [];
            
            // Recent accuracy (last 5 questions)
            const recentAccuracy = history.length > 0 ? 
                history.slice(-5).reduce((sum, h) => sum + (h.correct ? 1 : 0), 0) / Math.min(5, history.length) : 0.5;
            
            // Response time pattern (normalized)
            const avgResponseTime = profile.responseTime.length > 0 ?
                profile.responseTime.reduce((a, b) => a + b, 0) / profile.responseTime.length : 5000;
            const normalizedTime = Math.min(1, avgResponseTime / 10000);
            
            // Streak momentum
            const streakMomentum = Math.min(1, state.streak / 10);
            
            // Learning velocity (rate of score change)
            const learningVelocity = Math.max(-1, Math.min(1, profile.learningVelocity || 0));
            
            return {
                skillScore: state.skillScore / 100, // Normalize to [0,1]
                recentAccuracy,
                normalizedTime,
                streakMomentum,
                learningVelocity,
                confidenceLevel: profile.confidenceLevel || 0.5
            };
        }

        // Calculate reward based on outcome
        calculateReward(state, action, outcome) {
            let reward = 0;
            
            // 1. Accuracy reward (primary)
            reward += outcome.correct ? 1.0 : -0.5;
            
            // 2. Engagement reward (response time appropriateness)
            const expectedTime = { 'Easy': 3000, 'Medium': 5000, 'Hard': 8000 }[action];
            const timeRatio = outcome.responseTime / expectedTime;
            const timeReward = Math.max(0, 1 - Math.abs(timeRatio - 1) * 0.5);
            reward += timeReward * 0.3;
            
            // 3. Difficulty progression reward
            const difficultyReward = this.calculateDifficultyProgressionReward(state, action, outcome);
            reward += difficultyReward * 0.2;
            
            // 4. Learning momentum reward
            if (outcome.correct && state.streak > 2) {
                reward += 0.1 * Math.min(state.streak / 5, 1);
            }
            
            return Math.max(-1, Math.min(1, reward)); // Clamp to [-1, 1]
        }

        // Calculate reward for appropriate difficulty progression
        calculateDifficultyProgressionReward(state, action, outcome) {
            const profile = state.learnerProfile;
            const history = profile.difficultyHistory || [];
            
            if (history.length < 3) return 0;
            
            const recentHistory = history.slice(-3);
            const recentAccuracy = recentHistory.reduce((sum, h) => sum + (h.correct ? 1 : 0), 0) / recentHistory.length;
            
            // Reward appropriate difficulty selection
            if (recentAccuracy > 0.8 && action === 'Hard') return 0.5; // Good challenge
            if (recentAccuracy < 0.3 && action === 'Easy') return 0.5; // Good support
            if (recentAccuracy >= 0.4 && recentAccuracy <= 0.7 && action === 'Medium') return 0.3; // Good practice
            
            return 0;
        }

        // Epsilon-greedy action selection
        selectAction(state) {
            const stateVector = this.encodeState(state);
            const actionIndex = this.selectActionIndex(stateVector);
            const action = DIFFICULTIES[actionIndex];
            
            // Store decision for interpretability
            this.lastDecision = {
                action,
                actionIndex,
                qValues: [...this.qValues],
                explorationRate: this.explorationRate,
                stateVector,
                timestamp: Date.now(),
                reasoning: this.generateReasoning(stateVector, actionIndex)
            };
            
            this.decisionHistory.push(this.lastDecision);
            if (this.decisionHistory.length > 50) {
                this.decisionHistory.shift(); // Keep only last 50 decisions
            }
            
            return action;
        }

        // Select action index using epsilon-greedy
        selectActionIndex(stateVector) {
            if (Math.random() < this.explorationRate) {
                // Exploration: random action
                return Math.floor(Math.random() * 3);
            } else {
                // Exploitation: best action
                return this.qValues.indexOf(Math.max(...this.qValues));
            }
        }

        // Generate human-readable reasoning for decision
        generateReasoning(stateVector, actionIndex) {
            const action = DIFFICULTIES[actionIndex];
            const reasons = [];
            
            if (this.explorationRate > RL_CONFIG.minExplorationRate) {
                reasons.push(`Exploring (ε=${this.explorationRate.toFixed(3)})`);
            }
            
            if (stateVector.recentAccuracy > 0.8) {
                reasons.push(`High recent accuracy (${(stateVector.recentAccuracy * 100).toFixed(0)}%)`);
            } else if (stateVector.recentAccuracy < 0.3) {
                reasons.push(`Low recent accuracy (${(stateVector.recentAccuracy * 100).toFixed(0)}%)`);
            }
            
            if (stateVector.streakMomentum > 0.5) {
                reasons.push(`Strong streak momentum (${stateVector.streakMomentum.toFixed(2)})`);
            }
            
            if (stateVector.learningVelocity > 0.3) {
                reasons.push(`Positive learning velocity (${stateVector.learningVelocity.toFixed(2)})`);
            } else if (stateVector.learningVelocity < -0.3) {
                reasons.push(`Negative learning velocity (${stateVector.learningVelocity.toFixed(2)})`);
            }
            
            const qValue = this.qValues[actionIndex];
            const maxQValue = Math.max(...this.qValues);
            if (qValue === maxQValue) {
                reasons.push(`Highest Q-value (${qValue.toFixed(3)})`);
            } else {
                reasons.push(`Q-value: ${qValue.toFixed(3)} (max: ${maxQValue.toFixed(3)})`);
            }
            
            return reasons.join(', ');
        }

        // Update Q-values using Q-learning
        updateQValues(state, action, reward, nextState) {
            const actionIndex = DIFFICULTY_INDICES[action];
            const currentQ = this.qValues[actionIndex];
            
            // Q-learning update: Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
            const nextStateVector = this.encodeState(nextState);
            const maxNextQ = Math.max(...this.qValues);
            const targetQ = reward + RL_CONFIG.rewardDiscount * maxNextQ;
            
            this.qValues[actionIndex] = currentQ + RL_CONFIG.learningRate * (targetQ - currentQ);
            this.actionCounts[actionIndex]++;
            
            // Decay exploration rate
            this.explorationRate = Math.max(
                RL_CONFIG.minExplorationRate,
                this.explorationRate * RL_CONFIG.explorationDecay
            );
            
            // Store experience in memory
            this.memory.push({
                state: this.encodeState(state),
                action: actionIndex,
                reward,
                nextState: nextStateVector,
                timestamp: Date.now()
            });
            
            if (this.memory.length > RL_CONFIG.memorySize) {
                this.memory.shift();
            }
            
            this.updateCounter++;
        }

        // Get interpretable decision explanation
        getDecisionExplanation() {
            if (!this.lastDecision) return null;
            
            return {
                selectedDifficulty: this.lastDecision.action,
                qValues: {
                    Easy: this.lastDecision.qValues[0].toFixed(3),
                    Medium: this.lastDecision.qValues[1].toFixed(3),
                    Hard: this.lastDecision.qValues[2].toFixed(3)
                },
                explorationRate: this.lastDecision.explorationRate.toFixed(3),
                reasoning: this.lastDecision.reasoning,
                actionCounts: {
                    Easy: this.actionCounts[0],
                    Medium: this.actionCounts[1],
                    Hard: this.actionCounts[2]
                },
                timestamp: new Date(this.lastDecision.timestamp).toLocaleTimeString()
            };
        }

        // Get learning progress statistics
        getLearningStats() {
            const totalActions = this.actionCounts.reduce((sum, count) => sum + count, 0);
            const avgQValue = this.qValues.reduce((sum, q) => sum + q, 0) / this.qValues.length;
            
            return {
                totalDecisions: totalActions,
                averageQValue: avgQValue.toFixed(3),
                explorationRate: this.explorationRate.toFixed(3),
                memorySize: this.memory.length,
                recentDecisions: this.decisionHistory.slice(-5).map(d => ({
                    action: d.action,
                    qValue: d.qValues[d.actionIndex].toFixed(3),
                    reasoning: d.reasoning.split(', ')[0] // First reason only
                }))
            };
        }
    }

    // Global RL Agent instance
    let rlAgent = new PALRLAgent();

    // Main RL Algorithm Interface
    function getNextDifficulty(ctx) {
        const state = ctx.state;
        
        // Use RL agent to select difficulty
        const selectedDifficulty = rlAgent.selectAction(state);
        
        // Log RL decision
        console.log('🤖 RL Decision:', {
            selectedDifficulty,
            qValues: rlAgent.qValues.map((q, i) => `${DIFFICULTIES[i]}: ${q.toFixed(3)}`).join(', '),
            explorationRate: rlAgent.explorationRate.toFixed(3),
            reasoning: rlAgent.lastDecision.reasoning
        });
        
        return selectedDifficulty;
    }

    function updateProfileAfterAnswer(state, correct, difficulty, responseTime) {
        // Calculate reward
        const outcome = {
            correct,
            responseTime,
            timestamp: Date.now()
        };
        
        const reward = rlAgent.calculateReward(state, difficulty, outcome);
        
        // Update Q-values
        rlAgent.updateQValues(state, difficulty, reward, state);
        
        // Log RL update
        console.log('🔄 RL Update:', {
            difficulty,
            correct,
            reward: reward.toFixed(3),
            newQValues: rlAgent.qValues.map((q, i) => `${DIFFICULTIES[i]}: ${q.toFixed(3)}`).join(', '),
            explorationRate: rlAgent.explorationRate.toFixed(3)
        });
    }

    // Expose RL Algorithm Interface
    window.PALRLAlgorithm = {
        getNextDifficulty,
        updateProfileAfterAnswer,
        getDecisionExplanation: () => rlAgent.getDecisionExplanation(),
        getLearningStats: () => rlAgent.getLearningStats(),
        resetAgent: () => { rlAgent = new PALRLAgent(); },
        getConfig: () => ({ ...RL_CONFIG })
    };

})();


