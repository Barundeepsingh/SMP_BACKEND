from fastapi import FastAPI, Path, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from pydantic import BaseModel
from bson import ObjectId
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


class Address(BaseModel):
    country: str
    city: str

class Student(BaseModel):
    name: str
    age: int
    address: Address

def student_schema(student) -> dict:
    return{
        "id": str(student["_id"]),
        "name": student["name"],
        "age": student["age"],
        "address":student["address"]
    }

# Creating a Student
@app.post('/students', status_code=201)
async def create_student(student: Student):
    student_data = student.dict()
    result = await collection.insert_one(student_data)
    return {"id": str(result.inserted_id)}

#Filter students using country and age
@app.get('/students')
async def filter_students(country: Optional[str] = Query(None), age: Optional[int] = Query(None)):
    query = {}
    if country:
        query["address.country"] = country
    if age:
        query["age"] = {"$gte": age}
    students = await collection.find(query, {"name": 1, "age": 1}).to_list(length=100)
    if not students:
        return {"error": "No students found for the applied filter", "status_code": 404}
    return {"data": [{"name": student["name"], "age": student["age"]} for student in students]}


#Fetching a Student using id
@app.get('/students/{id}')
async def fetch_student(id: str = Path(...)):
    if not ObjectId.is_valid(id):
        return {"error": "Invalid ID", "status_code": 400}
    student = await collection.find_one({"_id": ObjectId(id)})
    if not student:
        return {"error": "Student not found", "status_code": 404}
    return student_schema(student)


#Updating a Student Details using Id
@app.patch('/students/{id}', status_code=204)
async def update_student(id: str = Path(...), updated_data: dict = {}):
    if not ObjectId.is_valid(id):
        return {"error": "Invalid ID", "status_code": 400}
    if not updated_data:
        return {"error": "No data passed", "status_code": 400}
    result = await collection.update_one({"_id": ObjectId(id)}, {"$set": updated_data})
    if result.matched_count == 0:
        return {"error": "Student not found", "status_code": 404}
    return None

#Deleting a Student using Id
@app.delete('/students/{id}', status_code=200)
async def delete_student(id: str = Path(...)):
    if not ObjectId.is_valid(id):
        return {"error": "Invalid ID", "status_code": 400}
    result = await collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        return {"error": "Student not found", "status_code": 404}
    return None