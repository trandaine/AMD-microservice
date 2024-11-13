import os
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder

app = FastAPI(title="Items-Service")


# Pydantic model for item data
class Item(BaseModel):
    id: int
    # id: str = str(ObjectId())
    name: str
    description: str
    price: float
    count: int

# MongoDB connection details
# Connect to MongoDB
MONGO_URI = "mongodb://mongodb:27017/"
COLLECTION_NAME = "items"
DATABASE_NAME = "items_db"
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


# Create an item
@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    item_dict = jsonable_encoder(item)
    if collection.find_one({"id": item.id}):
        raise HTTPException(status_code=400, detail="Item with this ID already exists.")
    collection.insert_one(item_dict)
    return item


# Read all items
@app.get("/items/", response_model=List[Item])
async def read_items():
    items = []
    for item_dict in collection.find():
        items.append(Item(**item_dict))
    return items


# Read a single item by ID
@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    item_dict = collection.find_one({"id": item_id})
    if item_dict is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(**item_dict)


# Update an item
@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    item_dict = jsonable_encoder(item)
    result = collection.update_one({"id": item_id}, {"$set": item_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


# Delete an item
@app.delete("/items/{item_id}", response_model=Item)
async def delete_item(item_id: int):
    item_dict = collection.find_one_and_delete({"id": item_id})
    if item_dict is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(**item_dict)