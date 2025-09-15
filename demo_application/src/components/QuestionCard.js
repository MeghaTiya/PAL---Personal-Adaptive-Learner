import questionStyles from "../stylesheets/question.module.css";
import videoContainerStyles from "../stylesheets/videoContainer.module.css";
import { useState } from "react";

function QuestionCard(props) {
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [submitClicked, setSubmitClicked] = useState(false);
  const [correctClicked, setCorrectClicked] = useState(false);

  const answerQuestion = () => {
    setSubmitClicked(true);
    props.question.setUserAnswered(true);
    if (selectedAnswer == null) {
      return;
    }
    if (selectedAnswer !== props.question.getDifficulty(props.difficulty).getQuestionOptions()[0]) {
      props.handleAnswer(false);
      return;
    }
    props.handleAnswer(true);
    setCorrectClicked(true);
    props.question.setUserGotAnswerCorrect(true);
  };

  return (
    <div className={videoContainerStyles.videoContainer}>
      {!submitClicked ? (
        <div className={questionStyles.questionContainer}>
          <p className={questionStyles.questionContainerTitle}>
            {props.question.getDifficulty(props.difficulty).getQuestion()}
          </p>
          <div className={questionStyles.questionOptions}>
            {props.scrambledQuestionOptions.map((questionAnswer) =>
              questionAnswer !== selectedAnswer ? (
                <p
                  className={questionStyles.questionOption}
                  onClick={() => setSelectedAnswer(questionAnswer)}
                >
                  {questionAnswer}
                </p>
              ) : (
                <p
                  className={questionStyles.questionOptionHighlighted}
                  onClick={() => setSelectedAnswer(questionAnswer)}
                >
                  {questionAnswer}
                </p>
              )
            )}
          </div>
          <div className={questionStyles.submitButton}>
            <button onClick={answerQuestion}>{"\u21B5"}</button>
          </div>
        </div>
      ) : correctClicked ? (
        <div className={questionStyles.questionContainer}>
          <p className={questionStyles.questionContainerTitle}>Correct!</p>
          <p>
            {props.question
              .getDifficulty(props.difficulty)
              .getDetailedCorrectAnswer()}
          </p>
          <button onClick={props.togglePlay}>{"\u25B6"}</button>
        </div>
      ) : (
        <div className={questionStyles.questionContainer}>
          <p className={questionStyles.questionContainerTitle}>Incorrect!</p>
          <p>{"Correct Answer: " + props.question.getDifficulty(props.difficulty).getQuestionOptions()[0]}</p>
          <div className={questionStyles.playButton}>
            <button onClick={props.togglePlay}>{"\u25B6"}</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default QuestionCard;
