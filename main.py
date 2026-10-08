from fastapi import Depends, FastAPI, status, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.task import Task
from schemas.task import TaskCreate, TaskUpdate


app = FastAPI()


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

@app.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)

    if task:
        return task
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.put("/tasks/{task_id}")
def update_task(task_id: int,task_data: TaskUpdate,db: Session = Depends(get_db)):
    task = db.get(Task, task_id)

    if task:
        update_data = task_data.model_dump(exclude_unset=True)
        task.title = update_data.get("title", task.title)
        task.description = update_data.get("description", task.description)
        task.status = update_data.get("status", task.status)
        task.due_date = update_data.get("due_date", task.due_date)
        db.commit()
        db.refresh(task)
        return {"message": "Task updated successfully", "task": task}
    else:
        raise HTTPException(status_code=404, detail="Task not found")
    # return task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)

    if task:
        db.delete(task)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Task not found")