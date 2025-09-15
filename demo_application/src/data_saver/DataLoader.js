import { Lesson } from "../model/Lesson";
import { Question } from "../model/Question";
import { useEffect, useState } from "react";
import { useLearningAppFascade } from "../useSingleton/useLearningAppFascade";
import { useLessonList } from "../useSingleton/useLessonList";

function DataLoader() {
  const [isInitializedReady, setIsInitializedReady] = useState(false);
  const { resumeLesson, currentLesson } = useLearningAppFascade();
  const { addLesson, lessons } = useLessonList();

  function timestampToSeconds(timestamp) {
    if (!timestamp || typeof timestamp !== "string") {
      return 0; // fallback if missing
    }

    const parts = timestamp.split(":").map(Number);

    if (parts.length === 3) {
      const [hours, minutes, seconds] = parts;
      return hours * 3600 + minutes * 60 + seconds;
    } else if (parts.length === 2) {
      const [minutes, seconds] = parts;
      return minutes * 60 + seconds;
    }

    return 0;
  }
  // Run to Initialize data in App
  useEffect(() => {
    // Flag to prevent state update after component unmounts
    let ignore = false;

    const initializeData = async () => {
      try {
        const res = await fetch(
          "data/D2-S1_Corln.v.Causn_questions_20250829_081747.json"
        );
        const data = await res.json();

        // Only process data if the component is still mounted
        if (!ignore) {
          // Check if data is already loaded to prevent any race conditions
          if (lessons.length === 0) {
            data.forEach((item) => {
              var questions = [];
              item.questions.forEach((jsonquestion, index) => {
                if (
                  index === 0 ||
                  item.questions[index - 1].timestamp !== jsonquestion.timestamp
                ) {
                  questions.push(new Question(timestampToSeconds(jsonquestion.timestamp)))
                }
                questions[questions.length - 1].addDifficulty(
                    jsonquestion.question.text,
                    jsonquestion.question.options,
                    jsonquestion.question.answer,
                    jsonquestion.question.detailed_answer,
                    jsonquestion.question.difficulty,
                    jsonquestion.tags
                  );
              });

              /*const questions = item.questions.map(
                (jsonquestion) =>
                  new Question(
                    jsonquestion.question.text,
                    jsonquestion.question.options,
                    jsonquestion.question.answer,
                    jsonquestion.question.detailed_answer,
                    timestampToSeconds(jsonquestion.timestamp),
                    jsonquestion.difficulty,
                    jsonquestion.tags
                  )
              );*/
              const lessonInstance = new Lesson(
                item.id,
                item.title,
                questions,
                item.thumbnailFileName,
                item.video_file
              );
              addLesson(lessonInstance);
            });
          }
          setIsInitializedReady(true); // Moved inside to run after data is loaded
        }
      } catch (err) {
        console.error("Failed to load lessons:", err);
        if (!ignore) {
          setIsInitializedReady(true); // Still signal readiness on error
        }
      }
    };

    initializeData();

    // Cleanup function: runs when the component unmounts
    return () => {
      ignore = true;
    };
  }, [addLesson, lessons.length]);

  // Load saved lesson from localStorage on mount
  useEffect(() => {
    if (isInitializedReady) {
      const saved = localStorage.getItem("currentLesson");
      if (saved && saved !== "undefined") {
        resumeLesson(saved);
      }
    }
  }, [isInitializedReady, resumeLesson]);

  // Save current lesson to localStorage on unload
  useEffect(() => {
    if (isInitializedReady) {
      const handleBeforeUnload = () => {
        if (currentLesson) {
          const id = currentLesson.getId();
          localStorage.setItem("currentLesson", id);
        }
      };

      window.addEventListener("beforeunload", handleBeforeUnload);
      return () => {
        window.removeEventListener("beforeunload", handleBeforeUnload);
      };
    }
  }, [isInitializedReady, currentLesson]);

  return null;
}

export default DataLoader;
