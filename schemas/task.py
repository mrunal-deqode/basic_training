from datetime import date

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    description: str
    status: str
    due_date: date


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    due_date: date | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    due_date: date

    model_config = ConfigDict(from_attributes=True)