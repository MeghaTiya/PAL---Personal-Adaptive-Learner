import { useNavigate } from "react-router-dom";
import { useRef, useState, useEffect } from "react";
import { useLearningAppFascade } from "../useSingleton/useLearningAppFascade";
import { useHybridLearner } from "../useSingleton/useHybridLearner";
import sidebarStyles from "../stylesheets/sidebar.module.css";
import videoContainerStyles from "../stylesheets/videoContainer.module.css";
import QuestionCard from "../components/QuestionCard";
import SummaryScreen from "../components/SummaryScreen";

function Video() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const [videoPlaying, setVideoPlaying] = useState(false);
  const [videoIsEnded, setVideoIsEnded] = useState(false);
  const [videoWidth, setVideoWidth] = useState(640);
  const [videoHeight, setVideoHeight] = useState(360);
  const [inFullscreen, SetInFullscreen] = useState(false);
  const [triggered, setTriggered] = useState(new Set());
  const [playQuestion, setPlayQuestion] = useState(null);
  const [questionDifficulty, setQuestionDifficulty] = useState("easy");
  const { videoFileName, questions, currentLesson, summary } =
    useLearningAppFascade();
  const { handleAnswer, nextDifficulty, startQuestionTimer } = useHybridLearner();
  const questionsChecked = questions || [];
  const timestamps = questionsChecked.map((question) =>
    question.getTimeStamp()
  );

  const MoveToMainScreen = () => {
    navigate("/home");
  };

  const ActivateChatbot = () => { };

  const togglePlay = () => {
    const video = videoRef.current;
    setPlayQuestion(null);
    if (!video) return;
    setVideoPlaying(!videoPlaying);
    if (video.paused) {
      video.play();
    } else {
      video.pause();
    }
  };

  const videoEnded = () => {
    setVideoIsEnded(true);
  };

  const fullScreen = () => {
    if (inFullscreen) {
      setVideoWidth(640);
      setVideoHeight(360);
    } else {
      setVideoWidth(1280);
      setVideoHeight(720);
    }
    SetInFullscreen(!inFullscreen);
  };

  useEffect(() => {
    if (nextDifficulty !== undefined) {
      console.log("Difficulty changed to "+nextDifficulty);
      setQuestionDifficulty(nextDifficulty);
    }
  }, [nextDifficulty]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    const handleTimeUpdate = () => {
      const currentTime = video.currentTime;
      timestamps.forEach((time, index) => {
        if (currentTime >= time && !triggered.has(time)) {
          video.pause();
          setVideoPlaying(false);
          startQuestionTimer(); 
          setPlayQuestion(currentLesson.getQuestions()[index]);
          setTriggered((prev) => new Set(prev).add(time));
        }
      });
    };

    video.addEventListener("timeupdate", handleTimeUpdate);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [triggered, timestamps, videoFileName, currentLesson, startQuestionTimer]);

  if (videoIsEnded) {
    return (
      <div className={sidebarStyles.body}>
        <div className={sidebarStyles.sidebar}>
          <button name="home_button" type="button" onClick={MoveToMainScreen}>
            Home
          </button>
        </div>
        <SummaryScreen totalCorrect={summary[0]} totalAnswered={summary[1]} />
      </div>
    );
  }

  return (
    <div className={sidebarStyles.body}>
      <div className={sidebarStyles.sidebar}>
        <button name="home_button" type="button" onClick={MoveToMainScreen}>
          Home
        </button>
      </div>
      {playQuestion ? (
        <QuestionCard
          question={playQuestion}
          difficulty={questionDifficulty}
          scrambledQuestionOptions={[
            ...playQuestion
              .getDifficulty(questionDifficulty)
              .getQuestionOptions(),
          ].sort(() => Math.random() - 0.5)}
          togglePlay={togglePlay}
          style={{ display: playQuestion ? "block" : "none" }}
          handleAnswer={handleAnswer}
        />
      ) : (
        <></>
      )}
      <div
        className={videoContainerStyles.videoContainer}
        style={{ display: playQuestion ? "none" : "flex" }}
      >
        <video
          ref={videoRef}
          width={videoWidth}
          height={videoHeight}
          key={videoFileName}
          onEnded={videoEnded}
        >
          <source src={videoFileName} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
        <div className={videoContainerStyles.videoControlButtons}>
        <button onClick={togglePlay}>
          {videoPlaying ? "\u23F8" : "\u25B6"}
        </button>
        <button onClick={fullScreen}>{"\u26F6"}</button>
        </div>
      </div>
    </div>
  );
}

export default Video;
