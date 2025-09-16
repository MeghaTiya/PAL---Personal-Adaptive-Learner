import questionStyles from "../stylesheets/question.module.css";
import videoContainerStyles from "../stylesheets/videoContainer.module.css";

function SummaryScreen(props) {

    return (
        <div className={videoContainerStyles.videoContainer}>
            <div className={questionStyles.questionContainer}>
                <p className={questionStyles.questionContainerTitle}>Summary:</p>
                <p className={questionStyles.questionContainerTitle}>{"Questions Correct: "+props.totalCorrect+"/"+props.totalAnswered}</p>
            </div>
        </div>
    )
}

export default SummaryScreen;