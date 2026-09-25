const registerForm = document.getElementById("registerForm");
const loginForm = document.getElementById("loginForm");

let currentUser = null;

const users = [];

registerForm.addEventListener("submit", function (event) {
    event.preventDefault();
    if (currentUser !== null) {
        alert("Please logout before registering a new user.");
        return;
    }

    const email = document.getElementById("email").value.trim();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const firstName = document.getElementById("firstName").value.trim();
    const lastName = document.getElementById("lastName").value.trim();
    const gender = document.getElementById("gender").value;
    const role = document.getElementById("role").value;

    if (
        email === "" ||
        username === "" ||
        password === "" ||
        firstName === "" ||
        lastName === "" ||
        gender === "" ||
        role === ""
    ) {
        alert("All fields are required.");
        return;
    }

    if (!email.includes("@")) {
        alert("Please enter a valid email.");
        return;
    }

    if (password.length < 6) {
        alert("Password must contain at least 6 characters.");
        return;
    }

    const usernameExists = users.some(function (user) {
        return user.username.toLowerCase() === username.toLowerCase();
    });

    if (usernameExists) {
        alert("Username already exists.");
        return;
    }

    const emailExists = users.some(function (user) {
        return user.email.toLowerCase() === email.toLowerCase();
    });

    if (emailExists) {
        alert("Email already exists.");
        return;
    }

    const user = {
        email,
        username,
        password,
        firstName,
        lastName,
        gender,
        role
    };

    users.push(user);

    alert("Registration successful.");

    registerForm.reset();

    console.log(users);
});

loginForm.addEventListener("submit", function (event) {
    event.preventDefault();

    if (currentUser !== null) {
        alert("Please logout first.");
        return;
    }

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;

    const loggedInUser = users.find(function (user) {
        return (
            user.username.toLowerCase() === username.toLowerCase() &&
            user.password === password
        );
    });

    if (!loggedInUser) {
        alert("Invalid username or password.");
        return;
    }

    alert("Login successful.");

    currentUser = loggedInUser;

    console.log("Logged in user:", loggedInUser);

    displayUsers(loggedInUser);

    loginForm.reset();
});

function displayUsers(loggedInUser) {
    const userList = document.getElementById("userList");

    userList.innerHTML = "";
    userList.style.display = "block";

    let visibleUsers;

    if (loggedInUser.role === "admin") {
        visibleUsers = users;
    } else {
        visibleUsers = users.filter(function (user) {
            return user.role === "user" && user.username !== loggedInUser.username;
        });
    }

    visibleUsers.forEach(function (user) {
        const li = document.createElement("li");

        li.textContent =
            user.firstName + " " +
            user.lastName +
            " | Username: " + user.username +
            " | Role: " + user.role;

        userList.appendChild(li);
    });
}

logoutButton.addEventListener("click", function () {
    currentUser = null;

    const userList = document.getElementById("userList");

    userList.innerHTML = "";
    userList.style.display = "none";

    alert("Logged out successfully.");
});