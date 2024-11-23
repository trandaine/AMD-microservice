from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder

app = FastAPI()

# MONGO_URI = "mongodb://sa:Dai2018@localhost:27017/"
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

# Connect to MongoDB
# client = MongoClient(MONGO_URI)
# db = client[DATABASE_NAME]
items_collection = db[COLLECTION_NAME]
users_collection = db["users_auths"]  # Collection for storing users

# --- Authentication ---

# Secret key for JWT (replace with a strong, random key)
SECRET_KEY = "f9d38701d307bc9f6c64dc05225377c424b2da06af13eeb5fcc3d2c814749ddf"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic model for user data
class User(BaseModel):
    username: str
    hashed_password: str  # Store hashed passwords

# Create a user (for testing purposes, hash the password securely in a real app)
@app.post("/users/", response_model=User)
async def create_user(user: User):
    user_dict = jsonable_encoder(user)
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    users_collection.insert_one(user_dict)
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"username": form_data.username})
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # In a real app, verify the password hash here
    if form_data.password != User(**user).hashed_password:  # Replace with actual password hashing
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Item endpoints ---

# Pydantic model for item data
class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    count: int

# Create an item (requires authentication)
@app.post("/items/", response_model=Item)
async def create_item(item: Item, current_user: User = Depends(get_current_user)):
    item_dict = jsonable_encoder(item)
    if items_collection.find_one({"id": item.id}):
        raise HTTPException(status_code=400, detail="Item with this ID already exists.")
    items_collection.insert_one(item_dict)
    return item

# Read all items (requires authentication)
@app.get("/items/", response_model=List[Item])
async def read_items(current_user: User = Depends(get_current_user)):
    items = []
    for item_dict in items_collection.find():
        items.append(Item(**item_dict))
    return items

# Read a single item by ID (requires authentication)
@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int, current_user: User = Depends(get_current_user)):
    item_dict = items_collection.find_one({"id": item_id})
    if item_dict is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(**item_dict)

# Update an item (requires authentication)
@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item, current_user: User = Depends(get_current_user)):
    item_dict = jsonable_encoder(item)
    result = items_collection.update_one({"id": item_id}, {"$set": item_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# Delete an item (requires authentication)
@app.delete("/items/{item_id}", response_model=Item)
async def delete_item(item_id: int, current_user: User = Depends(get_current_user)):
    item_dict = items_collection.find_one_and_delete({"id": item_id})
    if item_dict is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(**item_dict)