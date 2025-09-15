import { useEffect, useState } from "react";
import { LessonList } from "../model/LessonList";

export function useLessonList() {
    const lessonList = LessonList.getInstance();
    const [lessons, setLessons] = useState(lessonList.getLessons());

    useEffect(() => {
        const handleChange = () => {
            setLessons(lessonList.getLessons());
        };
        lessonList.subscribe(handleChange);
        return () => lessonList.unsubscribe(handleChange);
    }, []);

    return {
        lessons,
        addLesson: (lesson) => lessonList.addLesson(lesson)
    }
}