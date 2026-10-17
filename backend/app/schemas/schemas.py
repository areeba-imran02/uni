from pydantic import BaseModel, EmailStr, Field
from typing import Any

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ProjectIn(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    discipline: str
    degree: str = ""
    semester: str = ""
    task_type: str
    description: str = Field(min_length=8, max_length=12000)
    success_criteria: str = ""

class ProjectOut(BaseModel):
    id: int
    title: str
    discipline: str
    degree: str
    semester: str
    task_type: str
    description: str
    success_criteria: str
    status: str
    created_at: Any
    model_config = {"from_attributes": True}
