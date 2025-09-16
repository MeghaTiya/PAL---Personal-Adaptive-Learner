import { useNavigate } from "react-router-dom";
import { useLessonList } from "../useSingleton/useLessonList";
import { useLearningAppFascade } from "../useSingleton/useLearningAppFascade";
import sidebarStyles from "../stylesheets/sidebar.module.css";
import videoGridStyles from "../stylesheets/videoGrid.module.css";

function Home() {
  const { lessons } = useLessonList();
  const { logout, startNewLesson } = useLearningAppFascade();
  const navigate = useNavigate();

  // Logout button is pressed
  const LogOut = () => {
    logout();
    navigate("/");
  };

  // Video is pressed
  const MoveToVideo = (lesson) => {
    startNewLesson(lesson);
    navigate("/video");
  };

  // Account button is pressed
  const AccessAccount = () => { };

  return (
    <div className={videoGridStyles.body}>
      <div className={sidebarStyles.sidebar}>
        <button name="signout_button" type="button" onClick={LogOut}>
          Sign Out
        </button>
        <button name="account_button" type="button" onClick={AccessAccount}>
          Account
        </button>
      </div>
      <div className={videoGridStyles.videoGrid}>
        {lessons.map((lesson) => (
          <img
            src={lesson.getThumbnailFileName()}
            alt="D1S1thumbnail"
            onClick={() => MoveToVideo(lesson)}
            style={{ cursor: "pointer" }}
            draggable="false"
            key={lesson.getThumbnailFileName()}
          />
        ))}
      </div>
    </div>
  );
}

export default Home;
