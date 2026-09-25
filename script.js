const form = document.getElementById("todoForm");
const input = document.getElementById("todoInput");
const todoList = document.getElementById("todoList");

form.addEventListener("submit", function (event) {
    event.preventDefault();

    addTodo(todoText);

});



function addTodo(todoText) {
    const existingTodos = document.querySelectorAll(".todo-text");


    const li = document.createElement("li");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";

    const span = document.createElement("span");
    span.textContent = todoText;

    const removeButton = document.createElement("button");
    removeButton.textContent = "Remove";

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