# Enhanced Adaptive Learning Algorithm with Personalization & Buffers

initialize learner_profile = {
    skill_score: 50,
    streak: 0,
    best_streak: 0,
    last_difficulty: "Easy",
    consecutive_correct: 0,
    consecutive_wrong: 0,
    
    # Personalization tracking
    response_times: [],
    difficulty_history: [],  # stores {difficulty, correct, response_time, score_change}
    accuracy_by_difficulty: {Easy: [], Medium: [], Hard: []},
    learning_velocity: 0,    # rate of improvement/decline
    confidence_level: 0.5,   # algorithm's confidence in assessment
    adaptation_rate: 0.5,    # how quickly to adapt (0-1)
    question_start_time: null
}

function get_question_difficulty(learner_profile):
    # Step 1: Calculate base probabilities from skill score
    base_probs = calculate_base_probabilities(learner_profile.skill_score)
    
    # Step 2: Apply personalization adjustments with buffers
    adjusted_probs = base_probs
    adjusted_probs = adjust_for_recent_performance(adjusted_probs, learner_profile)
    adjusted_probs = adjust_for_response_time_patterns(adjusted_probs, learner_profile)
    adjusted_probs = adjust_for_accuracy_patterns(adjusted_probs, learner_profile)
    adjusted_probs = adjust_for_streak_momentum(adjusted_probs, learner_profile)
    adjusted_probs = adjust_for_learning_velocity(adjusted_probs, learner_profile)
    adjusted_probs = adjust_for_confidence(adjusted_probs, learner_profile)
    
    # Step 3: Apply stability buffer to prevent dramatic swings
    final_probs = apply_smoothing_buffer(adjusted_probs, learner_profile)
    
    # Step 4: Normalize and sample
    normalize_probabilities(final_probs)
    return sample_from_distribution(final_probs)

function calculate_base_probabilities(skill_score):
    # More granular skill levels with conservative transitions
    if skill_score <= 20:
        return {Easy: 0.85, Medium: 0.12, Hard: 0.03}
    else if skill_score <= 35:
        return {Easy: 0.75, Medium: 0.20, Hard: 0.05}
    else if skill_score <= 50:
        return {Easy: 0.55, Medium: 0.35, Hard: 0.10}
    else if skill_score <= 65:
        return {Easy: 0.35, Medium: 0.45, Hard: 0.20}
    else if skill_score <= 80:
        return {Easy: 0.20, Medium: 0.45, Hard: 0.35}
    else if skill_score <= 90:
        return {Easy: 0.10, Medium: 0.35, Hard: 0.55}
    else:
        return {Easy: 0.05, Medium: 0.25, Hard: 0.70}

function adjust_for_recent_performance(probs, profile):
    recent_history = profile.difficulty_history.slice(-4)  # Last 4 questions
    if recent_history.length == 0: return probs
    
    recent_accuracy = calculate_accuracy(recent_history)
    
    # STABILITY BUFFER: More conservative thresholds
    if recent_accuracy >= 0.75 and recent_history.length >= 4:
        # Very high performance - gradual increase
        probs.Easy *= 0.85
        probs.Hard *= (1 + (recent_accuracy - 0.75) * 0.8)
        log("Strong recent performance - gradual challenge increase")
    
    else if recent_accuracy <= 0.25 and recent_history.length >= 3:
        # Very poor performance - measured support
        probs.Easy *= 1.3
        probs.Hard *= 0.7
        log("Weak recent performance - providing measured support")
    
    else if recent_accuracy >= 0.25 and recent_accuracy < 0.75:
        # LEARNING ZONE: Maintain difficulty for practice
        log("Learning zone - maintaining current difficulty")
    
    return probs

function adjust_for_accuracy_patterns(probs, profile):
    easy_accuracy = calculate_accuracy(profile.accuracy_by_difficulty.Easy)
    medium_accuracy = calculate_accuracy(profile.accuracy_by_difficulty.Medium)
    hard_accuracy = calculate_accuracy(profile.accuracy_by_difficulty.Hard)
    
    easy_count = profile.accuracy_by_difficulty.Easy.length
    medium_count = profile.accuracy_by_difficulty.Medium.length
    hard_count = profile.accuracy_by_difficulty.Hard.length
    
    # ENHANCED BUFFER SYSTEM with higher thresholds
    
    # Easy mastery: Need 4+ attempts with 85%+ accuracy
    if easy_accuracy >= 0.85 and easy_count >= 4:
        mastery_level = min(1.5, 1 + (easy_accuracy - 0.85) * 2)
        probs.Easy *= (0.8 / mastery_level)
        probs.Medium *= 1.1
        log("Easy mastery detected")
    
    # Medium adjustment: Need 3+ attempts, with practice zone buffer
    if medium_count >= 3:
        if medium_accuracy <= 0.25:
            # Very poor - significant support
            probs.Easy *= 1.4
            probs.Medium *= 0.7
            probs.Hard *= 0.5
            log("Medium struggling - providing support")
        
        else if medium_accuracy >= 0.8 and medium_count >= 4:
            # Strong performance - gradual challenge
            probs.Medium *= 0.9
            probs.Hard *= 1.2
            log("Medium mastery - increasing challenge")
        
        else:
            # PRACTICE ZONE: 25%-80% accuracy maintains difficulty
            log("Medium practice zone - maintaining difficulty")
    
    # Hard questions: Conservative with 3+ attempts needed
    if hard_count >= 3:
        if hard_accuracy >= 0.75:
            probs.Hard *= 1.25
            log("Hard mastery detected")
        else if hard_accuracy <= 0.2 and hard_count >= 4:
            probs.Hard *= 0.6
            probs.Medium *= 1.2
            log("Hard difficulty too high - reducing")
    
    return probs

function adjust_for_streak_momentum(probs, profile):
    streak = profile.streak
    consecutive_wrong = profile.consecutive_wrong
    
    # ENHANCED BUFFER SYSTEM FOR STREAKS
    
    # Positive momentum: Gradual buildup
    if streak >= 5:
        streak_bonus = min(1.4, 1 + (streak - 4) * 0.08)
        probs.Hard *= streak_bonus
        probs.Easy *= (2 - streak_bonus)
        log("Hot streak - difficulty boost: " + streak_bonus)
    
    else if streak >= 3:
        probs.Hard *= 1.1
        probs.Easy *= 0.95
        log("Good streak - slight difficulty increase")
    
    # Negative momentum: Buffer before major changes
    if consecutive_wrong >= 3:
        probs.Easy *= 1.5
        probs.Hard *= 0.4
        log("Major struggle - strong support")
    
    else if consecutive_wrong == 2:
        probs.Easy *= 1.2
        probs.Hard *= 0.8
        log("Minor struggle - gentle support")
    
    # Context-aware difficulty stepping with pattern recognition
    if profile.last_difficulty == "Hard":
        recent_hard_attempts = filter_recent_by_difficulty(profile.difficulty_history, "Hard", 4)
        if recent_hard_attempts.length >= 2:
            hard_failure_rate = calculate_failure_rate(recent_hard_attempts)
            if hard_failure_rate >= 0.5:
                probs.Hard *= 0.4
                probs.Medium *= 1.4
                log("Hard questions too difficult - stepping down")
    
    else if profile.last_difficulty == "Medium":
        recent_medium_attempts = filter_recent_by_difficulty(profile.difficulty_history, "Medium", 3)
        if recent_medium_attempts.length >= 2:
            medium_failure_rate = calculate_failure_rate(recent_medium_attempts)
            if medium_failure_rate >= 0.67:  # 2/3 failure threshold
                probs.Easy *= 1.3
                probs.Medium *= 0.8
                log("Medium questions challenging - providing easier options")
    
    return probs

function apply_smoothing_buffer(probs, profile):
    # Prevent dramatic difficulty jumps
    if profile.difficulty_history.length < 3: return probs
    
    recent_difficulties = profile.difficulty_history.slice(-5)
    recent_distribution = calculate_difficulty_distribution(recent_difficulties)
    
    # Blend with recent pattern to prevent wild swings
    smoothing_factor = 0.7
    max_change = 0.4  # Maximum 40% change in probability
    
    probs.Easy = blend_probabilities(probs.Easy, recent_distribution.Easy, smoothing_factor)
    probs.Medium = blend_probabilities(probs.Medium, recent_distribution.Medium, smoothing_factor)
    probs.Hard = blend_probabilities(probs.Hard, recent_distribution.Hard, smoothing_factor)
    
    # Ensure reasonable bounds
    probs.Easy = clamp(probs.Easy, 0.05, 0.8)
    probs.Medium = clamp(probs.Medium, 0.1, 0.6)
    probs.Hard = clamp(probs.Hard, 0.05, 0.7)
    
    log("Smoothing buffer applied - preventing dramatic difficulty swings")
    return probs

function update_learner_profile(correct, difficulty, learner_profile):
    response_time = current_time() - learner_profile.question_start_time
    old_score = learner_profile.skill_score
    
    # Update basic metrics
    if correct:
        score_increment = get_score_increment(difficulty)  # Easy: 2, Medium: 5, Hard: 8
        learner_profile.skill_score += score_increment
        learner_profile.streak += 1
        learner_profile.consecutive_correct += 1
        learner_profile.consecutive_wrong = 0
        learner_profile.best_streak = max(learner_profile.best_streak, learner_profile.streak)
    else:
        score_decrement = get_score_decrement(difficulty)  # Easy: 2, Medium: 4, Hard: 6
        learner_profile.skill_score -= score_decrement
        learner_profile.streak = 0
        learner_profile.consecutive_wrong += 1
        learner_profile.consecutive_correct = 0
    
    learner_profile.skill_score = clamp(learner_profile.skill_score, 0, 100)
    learner_profile.last_difficulty = difficulty
    
    # Update personalization tracking
    update_response_times(learner_profile, response_time)
    update_difficulty_history(learner_profile, difficulty, correct, response_time, 
                            learner_profile.skill_score - old_score)
    update_accuracy_tracking(learner_profile, difficulty, correct)
    update_learning_velocity(learner_profile)
    update_confidence_level(learner_profile)
    update_adaptation_rate(learner_profile)
    
    log_personalization_insights(learner_profile, difficulty, correct, response_time)

function update_learning_velocity(profile):
    # Calculate rate of score change over recent questions
    if profile.difficulty_history.length >= 5:
        recent_5 = profile.difficulty_history.slice(-5)
        score_changes = extract_score_changes(recent_5)
        profile.learning_velocity = average(score_changes)

function update_confidence_level(profile):
    # Based on performance stability (low variance = high confidence)
    if profile.difficulty_history.length < 3: return
    
    recent = profile.difficulty_history.slice(-5)
    accuracy_variance = calculate_variance(extract_accuracies(recent))
    response_time_variance = calculate_variance(extract_response_times(recent))
    
    accuracy_confidence = max(0, 1 - accuracy_variance * 2)
    timing_confidence = max(0, 1 - response_time_variance / 10000)
    
    profile.confidence_level = (accuracy_confidence + timing_confidence) / 2

function next_lesson_setup(learner_profile):
    # Persist comprehensive learner state
    store_learner_profile(learner_profile)
    
    # Adjust starting parameters for next session
    if learner_profile.learning_velocity > 0:
        # Improving learner - start slightly higher
        adjust_initial_skill_score(learner_profile.skill_score + 5)
    else if learner_profile.learning_velocity < -0.2:
        # Declining learner - start with more support
        adjust_initial_skill_score(learner_profile.skill_score - 3)
    
    # Carry forward adaptation insights
    transfer_learning_patterns(learner_profile)
    
    log("Learner profile saved for next session with adaptive starting point")

# Utility functions
function calculate_accuracy(attempts):
    if attempts.length == 0: return 0.5
    return sum(correct_answers) / attempts.length

function calculate_variance(values):
    if values.length < 2: return 0
    mean = average(values)
    return average(square_differences_from_mean(values, mean))

function clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

function sample_from_distribution(probs):
    rand = random(0, 1)
    cumulative = 0
    for difficulty, prob in probs:
        cumulative += prob
        if rand <= cumulative:
            return difficulty
    return "Easy"  # fallback
