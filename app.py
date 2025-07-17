from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from decorator import cache_response

app = FastAPI()

# Sample data representing users in a database
users_db = {
    1: {"id": 1, "name": "Manas", "email": "manas@example.com", "age": 25},
    2: {"id": 2, "name": "omkar", "email": "omkar@example.com", "age": 29},
    3: {"id": 3, "name": "anand", "email": "anand@example.com", "age": 27},
}


@app.get("/users/{user_id}")
@cache_response(ttl=120, namespace="users")
async def get_user_details(user_id: int):
    # Simulate a database call by retrieving data from users_db
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
