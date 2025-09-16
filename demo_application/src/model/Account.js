/**
 * Class to create new Account
 */
export class Account {
    #firstName;
    #lastName;
    #email;
    #username;
    #password;
    #lessonsCompleted;

    /**
     * Creates an Account object
     * @param {string} firstName User's first name
     * @param {string} lastName User's last name
     * @param {string} email User's email
     * @param {string} username User's username
     * @param {string} password User's password
     */
    constructor(firstName, lastName, email, username, password) {
        this.#firstName = firstName;
        this.#lastName = lastName;
        this.#email = email;
        this.#username = username;
        this.#password = password;
        this.#lessonsCompleted = 0;
    }

    /**
     * Returns User's first name
     * @returns {string} User's first name
     */
    getFirstName() {
        return this.#firstName;
    }

    /**
     * Returns User's last name
     * @returns {string} User's last name
     */
    getlastName() {
        return this.#lastName;
    }

    /**
     * Returns User's email
     * @returns {string} User's email
     */
    getEmail() {
        return this.#email;
    }

    /**
     * Returns User's username
     * @returns {string} User's username
     */
    getUsername() {
        return this.#username;
    }

    /**
     * Returns User's password
     * @returns {string} User's password
     */
    getPassword() {
        return this.#password;
    }

    /**
     * Returns lessons completed
     * @returns {string} lessons completed
     */
    getLessonsCompleted() {
        return this.#lessonsCompleted;
    }
}