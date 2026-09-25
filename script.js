const form = document.getElementById("todoForm");
const input = document.getElementById("todoInput");
const todoList = document.getElementById("todoList");

form.addEventListener("submit", function (event) {
    event.preventDefault();

    const todoText = input.value.trim();

    if (todoText === "") {
        return;
    }

    if (todoText.length < 3) {
        alert("Todo must contain at least 3 characters.");
        return;
    }
    addTodo(todoText);

    input.value = "";
});



function addTodo(todoText) {
    const existingTodos = document.querySelectorAll(".todo-text");

    for (const todo of existingTodos) {
        if (todo.textContent.toLowerCase() === todoText.toLowerCase()) {
            alert("This todo already exists.");
            return;
        }
    }

    const li = document.createElement("li");
    li.classList.add("todo-item");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";

    const span = document.createElement("span");
    span.textContent = todoText;
    span.classList.add("todo-text");

    const removeButton = document.createElement("button");
    removeButton.textContent = "Remove";
    removeButton.classList.add("remove-btn");

    checkbox.addEventListener("change", function () {
        span.classList.toggle("completed", checkbox.checked);
    });

    removeButton.addEventListener("click", function () {
        li.remove();
    });

    li.appendChild(checkbox);
    li.appendChild(span);
    li.appendChild(removeButton);

    todoList.appendChild(li);
}