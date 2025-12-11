from __future__ import annotations
import mysql.connector
import os
import socket
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
import hashlib

from fastapi import FastAPI, HTTPException, Query, Path, Response
from fastapi.responses import JSONResponse

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from models.user import UserCreate, UserRead, UserUpdate
from models.userprofile import UserProfile
from models.health import Health

# -----------------------------------------------------------------------------
# Config & In-Memory Store
# -----------------------------------------------------------------------------
port = int(os.environ.get("PORT", 8080))

# Local in-memory "database"
users: Dict[UUID, UserRead] = {}

app = FastAPI(
    title="TripSpark User Microservice",
    description="Manages user accounts and embedded travel preferences for TripSpark.",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# Health Endpoints
# -----------------------------------------------------------------------------
def make_health(echo: Optional[str], path_echo: Optional[str] = None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo,
    )


@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None)):
    return make_health(echo=echo, path_echo=None)


@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(...),
    echo: str | None = Query(None),
):
    return make_health(echo=echo, path_echo=path_echo)

# -----------------------------------------------------------------------------
# Optional DB Test
# -----------------------------------------------------------------------------
@app.get("/dbtest")
def test_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            database=os.environ.get("DB_NAME")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"status": "success", "result": result[0]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# User Creation
# -----------------------------------------------------------------------------
@app.post("/users", response_model=UserRead, status_code=201)
def create_user(user: UserCreate, response: Response):
    # enforce unique email
    if any(u.email == user.email for u in users.values()):
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Create user
    user_read = UserRead(**user.model_dump())

    # Create associated profile
    profile = UserProfile(user_id=user_read.id)
    user_read.profile = profile

    # Store in memory
    users[user_read.id] = user_read

    response.headers["Location"] = f"/users/{user_read.id}"
    return user_read


# -----------------------------------------------------------------------------
# List Users
# -----------------------------------------------------------------------------
@app.get("/users", response_model=List[UserRead])
def list_users(
    name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    results = list(users.values())

    if name is not None:
        results = [u for u in results if u.full_name == name]

    if email is not None:
        results = [u for u in results if u.email == email]

    return results[offset: offset + limit]


# -----------------------------------------------------------------------------
# Get User
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Get User
# -----------------------------------------------------------------------------
@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    user = users[user_id]
    user_content = user.model_dump(mode='json') 
    
    user_json_str = user.model_dump_json()
    etag = hashlib.md5(user_json_str.encode("utf-8")).hexdigest()

    return JSONResponse(
        content=user_content,
        headers={"ETag": etag}
    )

# -----------------------------------------------------------------------------
# Replace User
# -----------------------------------------------------------------------------
@app.put("/users/{user_id}", response_model=UserRead)
def replace_user(user_id: UUID, user: UserCreate):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    existing_profile = users[user_id].profile

    updated = UserRead(
        **user.model_dump(),
        id=user_id,
        profile=existing_profile,
        updated_at=datetime.utcnow(),
    )

    users[user_id] = updated
    return updated


# -----------------------------------------------------------------------------
# PATCH: Update User & Profile (safe)
# -----------------------------------------------------------------------------
@app.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, update: UserUpdate):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    stored: UserRead = users[user_id]
    update_data = update.model_dump(exclude_unset=True)

    # --- update non-profile fields ---
    for field, value in update_data.items():
        if field != "profile":
            setattr(stored, field, value)

    # --- update profile safely ---
    if "profile" in update_data and update_data["profile"] is not None:
        prof_update = update_data["profile"]

        if isinstance(stored.profile, dict):
            stored.profile = UserProfile(**stored.profile)

        if isinstance(prof_update, dict):
            for key, value in prof_update.items():
                setattr(stored.profile, key, value)
        elif isinstance(prof_update, UserProfile):
            stored.profile = prof_update

    stored.updated_at = datetime.utcnow()
    return stored


# -----------------------------------------------------------------------------
# Delete User
# -----------------------------------------------------------------------------
@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: UUID):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    del users[user_id]
    return


# -----------------------------------------------------------------------------
# Profile Endpoints
# -----------------------------------------------------------------------------
@app.get("/users/{user_id}/profile", response_model=UserProfile)
def get_user_profile(user_id: UUID):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    profile = users[user_id].profile
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@app.put("/users/{user_id}/profile", response_model=UserProfile)
def update_user_profile(user_id: UUID, profile: UserProfile):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    users[user_id].profile = profile
    users[user_id].updated_at = datetime.utcnow()

    return profile


# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the TripSpark User Microservice. See /docs for OpenAPI UI."}


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
