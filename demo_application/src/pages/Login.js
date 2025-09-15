import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLearningAppFascade } from "../useSingleton/useLearningAppFascade";
import loginStyle from "../stylesheets/login.module.css";

function Login() {
  const [inputs, setInputs] = useState({});
  const navigate = useNavigate();
  const { login } = useLearningAppFascade();

  const handleChange = (event) => {
    const name = event.target.name;
    const value = event.target.value;
    setInputs(values => ({ ...values, [name]: value }))
  }

  const handleSubmit = (event) => {
    event.preventDefault();
    const { username, password } = inputs;
    login(username, password);
    navigate("/home");
  }

  return (
    <div className={loginStyle.formContainer}>
      <form onSubmit={handleSubmit}>
        <label>Username:
          <input
            type="text"
            name="username"
            value={inputs.username || ""}
            onChange={handleChange}
          />
        </label>
        <label>Password:
          <input
            type="password"
            name="password"
            value={inputs.password || ""}
            onChange={handleChange}
          />
        </label>
        <input type="submit" className={loginStyle.formContainerButton} />
      </form>
    </div>
  )
}

export default Login;