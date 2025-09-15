export class Account {
    #firstName;
    #lastName;
    #email;
    #username;
    #password;
    #lessonsCompleted;

    constructor(firstName, lastName, email, username, password) {
        this.#firstName = firstName;
        this.#lastName = lastName;
        this.#email = email;
        this.#username = username;
        this.#password = password;
    }

    isMatch(username, password) {

    }

    getFirstName() {
        return this.#firstName;
    }

    getlastName() {
        return this.#lastName;
    }

    getEmail() {
        return this.#email;
    }

    getUsername() {
        return this.#username;
    }

    getPassword() {
        return this.#password;
    }

    getLessonsCompleted() {

    }

    getCurrentLesson() {
        
    }
}