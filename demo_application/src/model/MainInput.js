function MoveToMainScreen() {
    window.location.href = 'loginScreen.html';
}

function MoveToVideo(lessonName) {   
    const learningAppFascade = LearningAppFascade.getInstance();
    learningAppFascade.startNewLesson(lessonName);
    window.location.href = 'videoScreen.html';
}

function SetVideo() {
    const learningAppFascade = LearningAppFascade.getInstance();
    const video = document.getElementById('mainVideo');
    const source = document.getElementById('videoSource');
    source.src = learningAppFascade.getCurrentLesson();
    video.load();
}

function ActivateChatbot() {

}

function login() {
    window.location.href = 'mainScreen.html';
    const learningAppFascade = LearningAppFascade.getInstance();
    console.log("hello");
    console.log(learningAppFascade);
    const usernameText = document.getElementById('username').value;
    const passwordText = document.getElementById('password').value;
    console.log(learningAppFascade.login(usernameText, passwordText));
    return false;
}