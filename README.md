# fastapi-response-boost

Speed up your FastAPI APIs with efficient caching using Redis. Practical examples and clean architecture included.
Caching in FastAPI: Unlocking High-Performance Development
This repository contains a simple FastAPI application demonstrating how to implement Redis caching to significantly improve API response times for frequently accessed data.

## Table of Contents

- [Introduction](#Introduction)

- [Required Libraries](#required-libraries)

- [Redis Setup and Verification](#redis-setup-and-verification)

- [Setting Up the FastAPI Application](#setting-up-the-fastapi-application)

    - [Step 1: Define the Pydantic Model for User Data](#step-1-define-the-pydantic-model-for-user-data)

    - [Step 2: Create a Caching Decorator](#step-2-create-a-caching-decorator)

    - [Step 3: Implement a FastAPI Route for User Details](#step-3-implement-a-fastapi-route-for-user-details)

- [Run the Application](#run-the-application)

- [Testing the Cache](#testing-the-cache)

- [How Caching Works in This Example](#how-caching-works-in-this-example)

- [Conclusion](#conclusion)

## Introduction

In modern digital applications, efficient API performance is crucial. Caching is a powerful technique that stores frequently accessed data in memory, allowing APIs to respond instantly without repeatedly querying slower databases. This project demonstrates how to integrate Redis caching with a FastAPI application to reduce API response times and improve overall efficiency.

## Required Libraries

To run this application and connect with Redis Cache, you need to install the following Python libraries:

```
pip install -r requirements.txt
```

- `fastapi`: For building the web API.

- `uvicorn`: An ASGI server for running the FastAPI application.

- `aiocache`: An asynchronous caching library for Python, used here to interact with Redis.

- `pydantic`: For data validation and settings management, used to define the User model.

## Redis Setup and Verification

Redis needs to be running for the caching mechanism to work. If you are on Windows, it's recommended to set up Redis using the Windows Subsystem for Linux (WSL).

## Install WSL

Follow the instructions on the official Microsoft documentation to install WSL:
Install WSL | Microsoft Learn

You can typically install WSL with the command:

```
wsl --install
```

### Install and Start Redis in WSL

Once WSL is installed and your preferred Linux distribution is running, execute the following commands in your WSL terminal to install and start the Redis server:

```
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

### Verify Redis Connectivity

To test if the Redis server is running and accessible, use the Redis CLI:

```
redis-cli
```

This command will open a virtual terminal connected to Redis on port 6379. You can then type Redis commands to interact with the server.

## Setting Up the FastAPI Application

Let's create a simple FastAPI application that retrieves user information and caches it for future requests using Redis.

### Step 1: Define the Pydantic Model for User Data

Create a file named app.py (or main.py if you prefer) and define your Pydantic model for user data. This model represents the structure of the API response.

```
# app.py
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int
```

### Step 2: Create a Caching Decorator

In the same app.py file, implement a reusable caching decorator using the aiocache library. This decorator will attempt to retrieve the response from Redis before calling the actual function.

```
# app.py (continued)
import json
from functools import wraps
from aiocache import Cache
from fastapi import HTTPException

def cache_response(ttl: int = 60, namespace: str = "main"):
    """
    Caching decorator for FastAPI endpoints.

    ttl: Time to live for the cache in seconds.
    namespace: Namespace for cache keys in Redis.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Assuming the user ID is passed as a keyword argument 'user_id'
            # or as the first positional argument. Adjust as needed for your API.
            user_id = kwargs.get('user_id') or (args[0] if args else None)
            if user_id is None:
                raise ValueError("User ID could not be determined for caching.")

            cache_key = f"{namespace}:user:{user_id}"

            # Initialize Redis cache client
            # Ensure Redis is running on localhost:6379
            cache = Cache.REDIS(endpoint="localhost", port=6379, namespace=namespace)

            # Try to retrieve data from cache
            cached_value = await cache.get(cache_key)
            if cached_value:
                # print(f"Cache hit for key: {cache_key}") # Optional: for debugging
                return json.loads(cached_value)  # Return cached data

            # print(f"Cache miss for key: {cache_key}. Fetching from source.") # Optional: for debugging
            # Call the actual function if cache is not hit
            response = await func(*args, **kwargs)

            try:
                # Store the response in Redis with a TTL
                await cache.set(cache_key, json.dumps(response.dict() if isinstance(response, BaseModel) else response), ttl=ttl)
            except Exception as e:
                # It's generally better to log this error and proceed without caching
                # rather than raising an HTTPException that stops the request.
                print(f"Error caching data for key {cache_key}: {e}")
                # raise HTTPException(status_code=500, detail=f"Error caching data: {e}") # Uncomment if you want to fail on cache error

            return response
        return wrapper
    return decorator
```

Note on response.dict() if isinstance(response, BaseModel) else response: The original blog post assumes response is directly JSON serializable. If your FastAPI endpoint returns a Pydantic model instance, you'll need to convert it to a dictionary using .dict() or .model_dump() (Pydantic v2) before json.dumps(). The updated decorator includes this check.

### Step 3: Implement a FastAPI Route for User Details

Now, implement a FastAPI route that retrieves user information based on a user ID. The response will be cached using Redis for faster access in subsequent requests.

```
# app.py (continued)
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Sample data representing users in a database (simulated)
users_db = {
    1: {"id": 1, "name": "Manas", "email": "manas@example.com", "age": 25},
    2: {"id": 2, "name": "omkar", "email": "omkar@example.com", "age": 29},
    3: {"id": 3, "name": "anand", "email": "anand@example.com", "age": 27},
}

@app.get("/users/{user_id}", response_model=User)
@cache_response(ttl=120, namespace="users")
async def get_user_details(user_id: int):
    """
    Retrieves user details and caches the response.
    """
    # Simulate a database call by retrieving data from users_db
    user_data = users_db.get(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Return a Pydantic User model instance
    return User(**user_data)
```

## Run the Application

To start your FastAPI application, navigate to your project directory in the terminal and run:

```
uvicorn app:app --reload
```

This command tells Uvicorn to look for the app object within the app.py file and enables auto-reloading on code changes.

Now, you can test the API by fetching user details via your web browser or a tool like curl:

```
http://127.0.0.1:8000/users/1
```

## Testing the Cache

You can verify the cache by inspecting the keys stored in Redis.

Open the Redis CLI in your WSL terminal:

```
redis-cli
```

Once in the Redis CLI, type the following command to see all stored keys:

```
KEYS *
```

You should see keys like users:user:1 appearing after you make requests to your FastAPI application.

## How Caching Works in This Example

- First Request: When user data is requested for the first time (e.g., GET /users/1), the API fetches it from the simulated database (users_db). The cache_response decorator then stores this result in Redis with a Time-To-Live (TTL) of 120 seconds.

- Subsequent Requests: Any subsequent requests for the same user (e.g., GET /users/1 again) within the 120-second TTL period are served directly from Redis. This makes the response significantly faster and reduces the load on the "database."

- TTL (Time to Live): After 120 seconds, the cache entry for that specific user expires. The next request for that user will then fetch the data from the database again, refreshing the cache with the latest data.

## Conclusion

This project provides a practical example of how to implement Redis caching in a FastAPI application. By leveraging caching, you can significantly enhance the performance and responsiveness of your APIs, especially for data that is frequently accessed but doesn't change often.
