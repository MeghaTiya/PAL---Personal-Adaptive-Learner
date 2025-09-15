import { Link } from "react-router-dom";
import loginStyle from "../stylesheets/login.module.css"

function Start() {
  return (
    <div className={loginStyle.formContainer}>
      <div className={loginStyle.formContainerLink}>
        <Link to="/login" className={loginStyle.formContainerLinkButton}>Login</Link>
        <Link to="/signup" className={loginStyle.formContainerLinkButton}>Sign Up</Link>
      </div>
    </div>
  )
}

export default Start;