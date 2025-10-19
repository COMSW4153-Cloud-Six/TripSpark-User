from __future__ import annotations

import os
import socket
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Path

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from models.user import UserCreate, UserRead, UserUpdate
from models.userprofile import UserProfile
from models.health import Health

# -----------------------------------------------------------------------------
# Config and in-memory "databases"
# -----------------------------------------------------------------------------
port = int(os.environ.get("FASTAPIPORT", 8000))

users: Dict[UUID, UserRead] = {}

app = FastAPI(
    title="TripSpark User Microservice",
    description="Manages user accounts and their embedded travel preferences for TripSpark.",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# Health endpoints
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
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    return make_health(echo=echo, path_echo=None)


@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Echo string in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)


# -----------------------------------------------------------------------------
# User endpoints (with embedded UserProfile)
# -----------------------------------------------------------------------------
@app.post("/users", response_model=UserRead, status_code=201)
def create_user(user: UserCreate):
    if any(u.email == user.email for u in users.values()):
        raise HTTPException(status_code=400, detail="User with this email already exists")
    user_read = UserRead(**user.model_dump())
    profile = UserProfile(user_id=user_read.id)
    user_read.profile = profile
    users[user_read.id] = user_read
    return user_read


@app.get("/users", response_model=List[UserRead])
def list_users(
    name: Optional[str] = Query(None, description="Filter by full name"),
    email: Optional[str] = Query(None, description="Filter by email"),
):
    results = list(users.values())
    if name is not None:
        results = [u for u in results if u.full_name == name]
    if email is not None:
        results = [u for u in results if u.email == email]
    return results


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID):
    """Retrieve a single user and their profile."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]


@app.put("/users/{user_id}", response_model=UserRead)
def replace_user(user_id: UUID, user: UserCreate):
    """Replace an entire user record, including preferences."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    data = user.model_dump()
    data["id"] = user_id
    user_read = UserRead(**data)
    users[user_id] = user_read
    return user_read


@app.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, update: UserUpdate):
    """Update core info or the embedded profile."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    stored = users[user_id].model_dump()
    update_data = update.model_dump(exclude_unset=True)

    if "profile" in update_data:
        if update_data["profile"] is not None:
            stored["profile"] = update_data["profile"]

    stored.update(update_data)
    users[user_id] = UserRead(**stored)
    return users[user_id]


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: UUID):
    """Delete a user and their profile."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    del users[user_id]
    return


# -----------------------------------------------------------------------------
# Profile endpoints (for Recommendation Service integration)
# -----------------------------------------------------------------------------
@app.get("/users/{user_id}/profile", response_model=UserProfile)
def get_user_profile(user_id: UUID):
    """Retrieve just the user's profile."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    profile = users[user_id].profile
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found for this user")
    return profile


@app.put("/users/{user_id}/profile", response_model=UserProfile)
def update_user_profile(user_id: UUID, profile: UserProfile):
    """Replace or update a user's profile."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    current = users[user_id].model_dump()
    current["profile"] = profile
    users[user_id] = UserRead(**current)
    return users[user_id].profile


# -----------------------------------------------------------------------------
# Root endpoint
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
