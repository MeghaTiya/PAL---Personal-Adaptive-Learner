/**
 * Creates a Lesson
 */
export class Lesson {
    #title;
    #questions;
    #currentQuestionNumber;
    #userScore;
    #thumbnailFileName;
    #vidFileName;
    #id;

    /**
     * Creates a Lesson
     * @param {number} id ID of lesson
     * @param {string} title Title of lesson
     * @param {Array<Question>} questions Questions for lesson
     * @param {string} thumbnailFileName File name of thumbnail
     * @param {string} vidFidName File name of Video
     */
    constructor(id, title, questions, thumbnailFileName, vidFidName) {
        this.#id = id;
        this.#title = title;
        if (!Array.isArray(questions)) {
            this.#questions = [];
        } else {
            this.#questions = questions;
        }
        this.#currentQuestionNumber = 0;
        this.#userScore = 0;
        this.#thumbnailFileName = thumbnailFileName;
        this.#vidFileName = vidFidName;
        console.log("Lesson constructor questions:", this.#questions, Array.isArray(questions));
    }

    /**
     * Returns ID of lesson
     * @returns ID of lesson
     */
    getId() {
        return this.#id;
    }

    /**
     * Returns title of lesson
     * @returns Title of lesson
     */
    getTitle() {
        return this.#title;
    }

    /**
     * Returns questions for lesson
     * @returns Questions for lesson
     */
    getQuestions() {
        return this.#questions;
    }

    /**
     * Return user's score
     * @returns User's score
     */
    getUserScore() {
        return this.#userScore;
    }

    /**
     * Returns file name of thumbnail
     * @returns File name of thumbnail
     */
    getThumbnailFileName() {
        return this.#thumbnailFileName;
    }

    /**
     * Returns file name of Video
     * @returns File name of Video
     */
    getVidFileName() {
        return this.#vidFileName;
    }

    /**
     * Adds a question to questions
     * @param {Question} question Question to be added
     */
    addQuestion(question) {
        this.#questions.push(question);
    }

    /**
     * Returns summary of lesson
     * @returns Summary of lesson
     */
    getSummary() {
        var totalAnswered = 0;
        var totalCorrect = 0;
        this.#questions.forEach(question => {
            if (question.getUserAnswered()) {
                totalAnswered++;
                if (question.getUserGotAnswerCorrect()) {
                    totalCorrect++;
                }
            }
        });
        var summary = [totalCorrect, totalAnswered];
        return summary;
    }
}