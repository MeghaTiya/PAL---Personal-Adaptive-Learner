export class Lesson {
    #title;
    #questions;
    #currentQuestionNumber;
    #userScore;
    #thumbnailFileName;
    #vidFileName;
    #id;
    #concepts;

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
        this.#concepts = [];
    }

    addConcept(concept) {
        this.#concepts.addConcept(concept);
    }

    getConcepts() {
        return this.#concepts;
    }

    getId() {
        return this.#id;
    }

    getTitle() {
        return this.#title;
    }

    getQuestions() {
        return this.#questions;
    }

    getCurrentQuestion() {

    }

    getUserScore() {
        return this.#userScore;
    }

    getThumbnailFileName() {
        return this.#thumbnailFileName;
    }

    getVidFileName() {
        return this.#vidFileName;
    }

    getLessonComplete() {

    }

    addQuestion(question) {
        this.#questions.push(question);
    }

    removeQuestion(question) {

    }

    moveToNextQuestion() {

    }

    moveToPrevQuestion() {

    }

    updateScore() {

    }

    startLesson() {

    }

    pauseLesson() {

    }

    unPauseLesson(timeStamp) {

    }

    endLesson() {
        
    }

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