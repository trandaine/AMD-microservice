from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

app = FastAPI()

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/" 
DATABASE_NAME = "ChalengesDB"
COLLECTION_NAME = "challenges"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


# Pydantic model for challenge data
class Challenges(BaseModel):
    # id: int
    id: str = str(ObjectId())
    name: str
    challenges: str
    description: str
    quantity: int


# Create an challenge
@app.post("/challenges/", response_model=Challenges)
async def create_item(challenge: Challenges):
    challenge_dict = jsonable_encoder(challenge)
    if collection.find_one({"id": challenge.id}):
        raise HTTPException(status_code=400, detail="Challenges with this ID already exists.")
    collection.insert_one(challenge_dict)
    return challenge


# Read all challenges
@app.get("/challenges/", response_model=List[Challenges])
async def read_items():
    challenges = []
    for challenge_dict in collection.find():
        challenges.append(Challenges(**challenge_dict))
    return challenges


# Read a single challenge by ID
@app.get("/challenges/{challenge_id}", response_model=Challenges)
async def read_item(challenge_id: str):
    challenge_dict = collection.find_one({"id": challenge_id})
    if challenge_dict is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Challenges(**challenge_dict)


# Update an challenge
@app.put("/challenges/{challenge_id}", response_model=Challenges)
async def update_item(challenge_id: str, challenge: Challenges):
    challenge_dict = jsonable_encoder(challenge)
    result = collection.update_one({"id": challenge_id}, {"$set": challenge_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


# Delete an challenge
@app.delete("/challenges/{challenge_id}", response_model=Challenges)
async def delete_item(challenge_id: str):
    challenge_dict = collection.find_one_and_delete({"id": challenge_id})
    if challenge_dict is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Challenges(**challenge_dict)