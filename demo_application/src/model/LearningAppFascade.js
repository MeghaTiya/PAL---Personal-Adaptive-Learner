import { Account } from "./Account";
import { Lesson } from "./Lesson";
import { LessonList } from "./LessonList";

/**
 * Creates a LearningAppFascade
 */
export class LearningAppFascade {
  static #learningAppFascade;
  #currentAccount;
  #currentLesson;
  #listeners = [];

  /**
   * Creates a LearningAppFascade
   */
  constructor() {
    this.#currentAccount = new Account("", "", "", "", "");
    this.#currentLesson = new Lesson("", "", "");
    this.#listeners = [];
  }

  /**
   * Returns singleton of LearningAppFascade
   * @returns Singleton of LearningAppFascade
   */
  static getInstance() {
    if (!this.#learningAppFascade) {
      this.#learningAppFascade = new LearningAppFascade();
    }
    return this.#learningAppFascade;
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

  /**
   * Handles user login
   * @param {string} username 
   * @param {string} password 
   * @returns Username
   */
  login(username, password) {
    this.#currentAccount = new Account(
      "firstName",
      "lastName",
      "email",
      username,
      password
    );
    this.notify();
    return username;
  }

  /**
   * Handles user logout
   */
  logout() {
    this.notify();
  }

  /**
   * Handles user sign up
   * @param {string} firstName 
   * @param {string} lastName 
   * @param {string} email 
   * @param {string} username 
   * @param {string} password 
   */
  signUp(firstName, lastName, email, username, password) {
    this.#currentAccount = new Account(
      firstName,
      lastName,
      email,
      username,
      password
    );
    this.notify();
  }

  /**
   * Returns account details
   * @returns First name
   */
  viewAccountDetails() {
    return this.#currentAccount.getFirstName();
  }

  /**
   * Handles user starting new lesson
   * @param {string} lesson Name of lesson
   */
  startNewLesson(lesson) {
    this.#currentLesson = lesson;
    this.notify();
  }

  /**
   * Handles user ending lesson
   */
  endLesson() {
    this.notify();
  }

  /**
   * Handles user resuming lesson
   * @param {number} lessonId 
   */
  resumeLesson(lessonId) {
    const lessonList = LessonList.getInstance();
    this.#currentLesson = lessonList.getLessonFromId(lessonId);
    this.notify();
  }

  /**
   * Handles user pausing lesson
   */
  pauseLesson() {
    this.notify();
  }

  /**
   * Handles user answering question
   * @param {string} answer 
   */
  answerQuestion(answer) {
    this.notify();
  }

  /**
   * Returns current lesson
   * @returns Current lesson
   */
  getCurrentLesson() {
    return this.#currentLesson;
  }

  /**
   * Returns user's summary
   * @returns User's summary
   */
  getSummary() {
    return this.#currentLesson.getSummary();
  }
}
