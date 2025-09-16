/**
 * Creates a question with only one difficulty
 */
export class DifficultyQuestion {
  #question;
  #questionOptions;
  #questionDetailedCorrectAnswer;
  #difficulty;

  /**
   * Creates a question with only one difficulty
   * @param {string} question Question
   * @param {Array<string>} questionOptions Question options
   * @param {string} questionCorrectAnswer Correct answer to question
   * @param {string} questionDetailedCorrectAnswer Summary of why answer is correct
   * @param {string} difficulty Difficulty of question
   */
  constructor(
    question,
    questionOptions,
    questionCorrectAnswer,
    questionDetailedCorrectAnswer,
    difficulty
  ) {
    this.#question = question;
    this.#questionOptions = [];
    // Set correct answer to first in array to simplify and add rest behind
    if (questionCorrectAnswer === "A") {
      this.#questionOptions.push(questionOptions[0]);
      questionOptions.forEach((question, index) => {
        if (index !== 0) {
          this.#questionOptions.push(question);
        }
      });
    } else if (questionCorrectAnswer === "B") {
      this.#questionOptions.push(questionOptions[1]);
      questionOptions.forEach((question, index) => {
        if (index !== 1) {
          this.#questionOptions.push(question);
        }
      });
    } else if (questionCorrectAnswer === "C") {
      this.#questionOptions.push(questionOptions[2]);
      questionOptions.forEach((question, index) => {
        if (index !== 2) {
          this.#questionOptions.push(question);
        }
      });
    } else {
      this.#questionOptions.push(questionOptions[3]);
      questionOptions.forEach((question, index) => {
        if (index !== 3) {
          this.#questionOptions.push(question);
        }
      });
    }
    this.#questionDetailedCorrectAnswer = questionDetailedCorrectAnswer;
    this.#difficulty = difficulty;
  }

  /**
   * Returns question
   * @returns Question
   */
  getQuestion() {
    return this.#question;
  }

  /**
   * Returns question options
   * @returns Question options
   */
  getQuestionOptions() {
    return this.#questionOptions;
  }

  /**
   * Returns difficulty of question
   * @returns Difficulty of question
   */
  getDifficulty() {
    return this.#difficulty;
  }

  /**
   * Returns summary of why answer is correct
   * @returns Summary of why answer is correct
   */
  getDetailedCorrectAnswer() {
    return this.#questionDetailedCorrectAnswer;
  }
}
