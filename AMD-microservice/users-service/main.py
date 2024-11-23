from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

app = FastAPI(title="Users-Service")


# Pydantic model for user data
class Users(BaseModel):
    id: int
    # id: str = str(ObjectId())
    name: str
    users: str
    description: str

# MongoDB connection details
# Connect to MongoDB
MONGO_URI = "mongodb://mongodb:27017/"
COLLECTION_NAME = "users"
DATABASE_NAME = "users_db"
@app.on_event("startup")
async def startup_db_client():
    try:
        client = MongoClient(MONGO_URI)
        client.server_info() 
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Create an user
@app.post("/users/", response_model=Users)
async def create_item(user: Users):
    user_dict = jsonable_encoder(user)
    if collection.find_one({"id": user.id}):
        raise HTTPException(status_code=400, detail="Users with this ID already exists.")
    collection.insert_one(user_dict)
    return user


# Read all users
@app.get("/users/", response_model=List[Users])
async def read_items():
    users = []
    for user_dict in collection.find():
        users.append(Users(**user_dict))
    return users


# Read a single user by ID
@app.get("/users/{user_id}", response_model=Users)
async def read_item(user_id: int):
    user_dict = collection.find_one({"id": user_id})
    if user_dict is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Users(**user_dict)


# Update an user
@app.put("/users/{user_id}", response_model=Users)
async def update_item(user_id: int, user: Users):
    user_dict = jsonable_encoder(user)
    result = collection.update_one({"id": user_id}, {"$set": user_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return user


# Delete an user
@app.delete("/users/{user_id}", response_model=Users)
async def delete_item(user_id: int):
    user_dict = collection.find_one_and_delete({"id": user_id})
    if user_dict is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Users(**user_dict)