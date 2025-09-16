import { DifficultyQuestion } from "./DifficultyQuestion";

export class Question {
  #timeStamp;
  #userGotAnswerCorrect;
  #userAnswered;
  #allDifficultyQuestions;

  constructor(timeStamp) {
    this.#timeStamp = timeStamp;
    this.#userGotAnswerCorrect = false;
    this.#userAnswered = false;
    this.#allDifficultyQuestions = [];
  }

  addDifficulty(
    question,
    questionOptions,
    questionCorrectAnswer,
    questionDetailedCorrectAnswer,
    difficulty
  ) {
    this.#allDifficultyQuestions.forEach((difficultyQuestion) => {
      if (difficultyQuestion.getDifficulty === difficulty) {
        return;
      }
    });
    this.#allDifficultyQuestions.push(
      new DifficultyQuestion(
        question,
        questionOptions,
        questionCorrectAnswer,
        questionDetailedCorrectAnswer,
        difficulty
      )
    );
  }

  getDifficulty(difficulty) {
    const question = this.#allDifficultyQuestions.find(
      (q) => q.getDifficulty() === difficulty
    );

    if (question) {
      return question;
    } else {
      return this.#allDifficultyQuestions[0];
    }
  }

  getTimeStamp() {
    return this.#timeStamp;
  }

  getCorrectAnswer() { }

  isAnswerCorrect(answer) { }

  setUserGotAnswerCorrect(userGotAnswerCorrect) {
    this.#userGotAnswerCorrect = userGotAnswerCorrect;
  }

  getUserGotAnswerCorrect() {
    return this.#userGotAnswerCorrect;
  }

  setUserAnswered(userAnswered) {
    this.#userAnswered = userAnswered;
  }

  getUserAnswered() {
    return this.#userAnswered;
  }
}
