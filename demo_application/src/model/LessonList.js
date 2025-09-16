import { Lesson } from "./Lesson";

/**
 * Creates a LessonList
 */
export class LessonList {
    #lessons;
    static #lessonList;
    #listeners;

    /**
     * Creates a LessonList
     */
    constructor() {
        this.#lessons = [];
        this.#listeners = [];
    }

    /**
     * Returns singleton of LessonList
     * @returns Singleton of LessonList
     */
    static getInstance() {
        if (!this.#lessonList) {
            this.#lessonList = new LessonList();
        }
        return this.#lessonList;
    }

    subscribe(listener) {
        this.#listeners.push(listener);
    }

    unsubscribe(listener) {
        this.#listeners = this.#listeners.filter(l => l !== listener);
    }

    notify() {
        this.#listeners.forEach(fn => fn());
    } 

    /**
     * Adds lesson to lessons
     * @param {Lesson} lesson Lesson to be added to lessons
     */
    addLesson(lesson) {
        this.#lessons.push(lesson);
        this.notify();
    }

    /**
     * Gets lesson from lessons with title
     * @param {string} title 
     * @returns Lesson from lessons
     */
    getLesson(title) {
        return new Lesson(title,"","files/vid/d1s1.mp4");
    }

    /**
     * Gets lesson from lessons with id
     * @param {number} id 
     * @returns Lesson from lessons
     */
    getLessonFromId(id) {
        for (const lesson of this.#lessons) {
            console.log(id);
            console.log(lesson.getId());
            if (lesson.getId().toString() === id.toString()) {
                console.log("lesson log loading: ", id);
                return lesson;
            }
        }
    }

    /**
     * Returns lessons
     * @returns Lessons
     */
    getLessons() {
        // Returns a new instance of lessons to update useEffect
        return [...this.#lessons];
    }

    /**
     * Saves LessonList
     */
    save() {
        this.notify();
    }
}