from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId
from pymongo import MongoClient
import os

Mongo_url = os.getenv("MONGO_URL")
client = MongoClient(Mongo_url)
db = client["task"]
task_collection = db["tasks"]

app = FastAPI()

#pydantic models
class Taskbase(BaseModel):
  title:str
  description: Optional[str] = None
  completed: bool = False 

class TaskCreate(Taskbase):
  id: str

#for mongo docs we are using serialization docs
def task_serializer(task) -> dict:
  return {
    "id": str(task["_id"]),
    "title": task["title"],
    "description": task.get("description"),
    "completed": task["completed"]
  }  

@app.post("/tasks/", response_model=Taskbase)
async def create_task(task: Taskbase):
  new_task = task.dict()
  result = task_collection.insert_one(new_task)
  new_task['_id']=result.inserted_id
  return task_serializer(new_task)

@app.get("/tasks/", response_model=List[Taskbase])
async def get_tasks():
  return [task_serializer(task) for task in task_collection.find()]

@app.put("/tasks/{task_id}", response_model=Taskbase)
async def update_task(task_id: str, task: Taskbase):
  result = task_collection.find_one_and_update(
    {"_id": task_id},
    {"$set": task.dict()},
    return_document=True
  )
  if not result:
    raise HTTPException(status_code=404, detail="task not found")
  return task_serializer(result)


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
  result = task_collection.delete_one(
    {"_id": ObjectId(task_id)}
  )
  if result.deleted_count == 0:
    raise HTTPException(status_code=404,detail="task not found")
  return {"message": "task deleted successfully"}