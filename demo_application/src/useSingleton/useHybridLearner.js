import { useEffect, useState } from "react";
import { HybridLearner } from "../model/HybridLearner";

export function useHybridLearner() {
    const hybridLearner = HybridLearner.getInstance();
    const [nextDifficulty, setNextDifficulty] = useState(hybridLearner.getNextDifficulty());

    useEffect(() => {
        const handleChange = () => {
            console.log("Notification received. New difficulty is:", nextDifficulty);
            setNextDifficulty(hybridLearner.getNextDifficulty());
        };
        hybridLearner.subscribe(handleChange);
        return () => hybridLearner.unsubscribe(handleChange);
    }, []);

    return {
        handleAnswer: (correct) => hybridLearner.handleAnswer(correct),
        startQuestionTimer: () => hybridLearner.startQuestionTimer(),
        nextDifficulty
    }
}