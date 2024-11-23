from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

app = FastAPI(title="Categories-Service")


# Pydantic model for category data
class Categories(BaseModel):
    id: int
    # id: str = str(ObjectId())
    name: str
    categories: str
    description: str

# MongoDB connection details
# Connect to MongoDB
MONGO_URI = "mongodb://mongodb:27017/"
COLLECTION_NAME = "categories"
DATABASE_NAME = "categories_db"
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

# Create an category
@app.post("/categories/", response_model=Categories)
async def create_item(category: Categories):
    category_dict = jsonable_encoder(category)
    if collection.find_one({"id": category.id}):
        raise HTTPException(status_code=400, detail="Categories with this ID already exists.")
    collection.insert_one(category_dict)
    return category


# Read all categories
@app.get("/categories/", response_model=List[Categories])
async def read_items():
    categories = []
    for category_dict in collection.find():
        categories.append(Categories(**category_dict))
    return categories


# Read a single category by ID
@app.get("/categories/{category_id}", response_model=Categories)
async def read_item(category_id: int):
    category_dict = collection.find_one({"id": category_id})
    if category_dict is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Categories(**category_dict)


# Update an category
@app.put("/categories/{category_id}", response_model=Categories)
async def update_item(category_id: int, category: Categories):
    category_dict = jsonable_encoder(category)
    result = collection.update_one({"id": category_id}, {"$set": category_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return category


# Delete an category
@app.delete("/categories/{category_id}", response_model=Categories)
async def delete_item(category_id: int):
    category_dict = collection.find_one_and_delete({"id": category_id})
    if category_dict is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Categories(**category_dict)