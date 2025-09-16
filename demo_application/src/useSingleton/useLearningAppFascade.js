import { useEffect, useState } from "react";
import { LearningAppFascade } from "../model/LearningAppFascade";

/**
 * Allows LearningAppFascade to be used as a useEffect
 * @returns currentLesson, videoFileName, questions, summary, startNewLesson, resumeLesson, login, signUp, logout
 */
export function useLearningAppFascade() {
    const learningAppFascade = LearningAppFascade.getInstance();
    const [currentLesson, setCurrentLesson] = useState(learningAppFascade.getCurrentLesson());

    useEffect(() => {
        const handleChange = () => {
            setCurrentLesson(learningAppFascade.getCurrentLesson());
        };

        learningAppFascade.subscribe(handleChange);
        return () => learningAppFascade.unsubscribe(handleChange);
    }, []);

    return {
        currentLesson,
        videoFileName: currentLesson.getVidFileName(),
        questions: currentLesson.getQuestions(),
        summary: learningAppFascade.getSummary(),
        startNewLesson: (lesson) => learningAppFascade.startNewLesson(lesson),
        resumeLesson: (lessonId) => learningAppFascade.resumeLesson(lessonId),
        login: (username, password) => learningAppFascade.login(username, password),
        signUp: (firstName, lastName, email, username, password) => learningAppFascade.signUp(firstName, lastName, email, username, password),
        logout: () => learningAppFascade.logout()
    }
}